odoo.define('point_of_sale.DB', function (require) {
    "use strict";

    var core = require('web.core');
    var utils = require('web.utils');

    var PosDB = core.Class.extend({
        name: 'openerp_pos_db',
        limit: 100,

        init: function (options) {
            options = options || {};
            this.name = options.name || this.name;
            this.limit = options.limit || this.limit;
            if (options.uuid) this.name += '_' + options.uuid;

            // Cache
            this.cache = {};

            // Produits
            this.product_by_id = {};
            this.product_by_barcode = {};
            this.product_by_category_id = {};

            // Partenaires
            this.partner_sorted = [];
            this.partner_by_id = {};
            this.partner_by_barcode = {};
            this.partner_search_string = "";
            this.partner_write_date = null;

            // Catégories
            this.category_by_id = {};
            this.root_category_id = 0;
            this.category_ancestors = {};
            this.category_childs = {};
            this.category_parent = {};
            this.category_search_string = {};
        },

        set_uuid: function (uuid) {
            this.name += '_' + uuid;
        },

        // --- Catégories ---
        get_category_by_id: function (categ_id) {
            if (Array.isArray(categ_id)) {
                return categ_id.map(id => this.category_by_id[id]).filter(c => c);
            } else {
                return this.category_by_id[categ_id];
            }
        },

        get_category_childs_ids: function (categ_id) {
            return this.category_childs[categ_id] || [];
        },

        get_category_ancestors_ids: function (categ_id) {
            return this.category_ancestors[categ_id] || [];
        },

        get_category_parent_id: function (categ_id) {
            return this.category_parent[categ_id] || this.root_category_id;
        },

        add_categories: function (categories) {
            const self = this;

            // 🔥 Reset des structures POS
            self.category_by_id = {};
            self.category_childs = {};
            self.category_parent = {};
            self.category_ancestors = {};

            // 🔥 Création de la racine
            const ROOT = this.root_category_id || 0;
            self.category_by_id[ROOT] = { id: ROOT, name: "All" };
            self.category_childs[ROOT] = [];

            // 1️⃣ Enregistrer toutes les catégories
            categories.forEach(cat => {
                self.category_by_id[cat.id] = cat;
                self.category_childs[cat.id] = []; // prepare for possible future children
            });

            // 2️⃣ Construire la hiérarchie POS
            categories.forEach(cat => {

                // 💡 si pas de parent renseigné → la catégorie est enfant directe de All
                let parent_id = (cat.parent_id && cat.parent_id[0]) || ROOT;

                // 💡 parent non trouvé ? → rattacher à All (sécurité)
                if (!self.category_by_id[parent_id]) {
                    parent_id = ROOT;
                }

                self.category_parent[cat.id] = parent_id;
                self.category_childs[parent_id].push(cat.id);
            });

            // 3️⃣ Calcul des ancêtres pour le breadcrumb
            function buildAncestors(id, chain) {
                self.category_ancestors[id] = chain.slice();
                chain.push(id);

                (self.category_childs[id] || []).forEach(child_id =>
                    buildAncestors(child_id, chain)
                );

                chain.pop();
            }

            buildAncestors(ROOT, []);
        },
        category_contains: function (categ_id, product_id) {
            var product = this.product_by_id[product_id];
            if (!product) return false;
            var cid = product.categ_id ? product.categ_id[0] : null;
            while (cid && cid !== categ_id) {
                cid = this.category_parent[cid];
            }
            return !!cid;
        },

        // --- Produits ---
        _product_search_string: function (product) {
            var str = product.display_name;
            if (product.barcode) str += '|' + product.barcode;
            if (product.default_code) str += '|' + product.default_code;
            if (product.description) str += '|' + product.description;
            if (product.description_sale) str += '|' + product.description_sale;
            return product.id + ':' + str.replace(/[\n:]/g, '') + '\n';
        },

        add_products: function (products) {
            if (!Array.isArray(products)) products = [products];

            var stored_categories = this.product_by_category_id;

            products.forEach(product => {
                if (product.available_in_pos) {
                    var categ_id = product.categ_id ? product.categ_id[0] : this.root_category_id;

                    if (!stored_categories[categ_id]) stored_categories[categ_id] = [];
                    stored_categories[categ_id].push(product.id);

                    var ancestors = this.get_category_ancestors_ids(categ_id);
                    ancestors.forEach(ancestor => {
                        if (!stored_categories[ancestor]) stored_categories[ancestor] = [];
                        stored_categories[ancestor].push(product.id);
                    });
                }
                this.product_by_id[product.id] = product;
                if (product.barcode) this.product_by_barcode[product.barcode] = product;
            });
        },

        get_product_by_id: function (id) { return this.product_by_id[id]; },
        get_product_by_barcode: function (barcode) { return this.product_by_barcode[barcode]; },

        get_product_by_category: function (category_id) {
            var product_ids = this.product_by_category_id[category_id] || [];
            return product_ids.map(id => this.product_by_id[id]).filter(p => p && p.active && p.available_in_pos);
        },

        search_product_in_category: function (category_id, query) {
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g, '.');
                query = query.replace(/ /g, '.+');
                var re = RegExp("([0-9]+):.*?" + utils.unaccent(query), "gi");
            } catch (e) {
                return [];
            }

            var results = [];
            var search_string = this.category_search_string[category_id] || '';
            var r;
            while ((r = re.exec(search_string)) !== null && results.length < this.limit) {
                var id = Number(r[1]);
                var product = this.get_product_by_id(id);
                if (product && product.active && product.available_in_pos) results.push(product);
            }
            return results;
        },

        is_product_in_category: function (category_ids, product_id) {
            if (!Array.isArray(category_ids)) category_ids = [category_ids];
            var cat = this.get_product_by_id(product_id).categ_id ? this.get_product_by_id(product_id).categ_id[0] : null;
            while (cat) {
                if (category_ids.includes(cat)) return true;
                cat = this.get_category_parent_id(cat);
            }
            return false;
        },

        // --- Partenaires ---
        _partner_search_string: function (partner) {
            var str = partner.name || '';
            if (partner.barcode) str += '|' + partner.barcode;
            if (partner.address) str += '|' + partner.address;
            if (partner.phone) str += '|' + partner.phone.split(' ').join('');
            if (partner.mobile) str += '|' + partner.mobile.split(' ').join('');
            if (partner.email) str += '|' + partner.email;
            if (partner.vat) str += '|' + partner.vat;
            return partner.id + ':' + str.replace(':', '').replace(/\n/g, ' ') + '\n';
        },

        add_partners: function (partners) {
            var updated_count = 0;
            var new_write_date = '';

            partners.forEach(partner => {
                var local_date = (this.partner_write_date || '').replace(/^(\d{4}-\d{2}-\d{2}) ((\d{2}:?){3})$/, '$1T$2Z');
                var dist_date = (partner.write_date || '').replace(/^(\d{4}-\d{2}-\d{2}) ((\d{2}:?){3})$/, '$1T$2Z');

                if (this.partner_write_date &&
                    this.partner_by_id[partner.id] &&
                    new Date(local_date).getTime() + 1000 >= new Date(dist_date).getTime()) return;

                if (new_write_date < partner.write_date) new_write_date = partner.write_date;
                if (!this.partner_by_id[partner.id]) this.partner_sorted.push(partner.id);
                this.partner_by_id[partner.id] = partner;
                updated_count++;
            });

            this.partner_write_date = new_write_date || this.partner_write_date;

            if (updated_count) {
                this.partner_search_string = "";
                this.partner_by_barcode = {};
                for (var id in this.partner_by_id) {
                    var partner = this.partner_by_id[id];
                    if (partner.barcode) this.partner_by_barcode[partner.barcode] = partner;
                    partner.address = (partner.street ? partner.street + ', ' : '') +
                        (partner.zip ? partner.zip + ', ' : '') +
                        (partner.city ? partner.city + ', ' : '') +
                        (partner.state_id ? partner.state_id[1] + ', ' : '') +
                        (partner.country_id ? partner.country_id[1] : '');
                    this.partner_search_string += this._partner_search_string(partner);
                }
                this.partner_search_string = utils.unaccent(this.partner_search_string);
            }
            return updated_count;
        },

        get_partner_write_date: function () { return this.partner_write_date || "1970-01-01 00:00:00"; },
        get_partner_by_id: function (id) { return this.partner_by_id[id]; },
        get_partner_by_barcode: function (barcode) { return this.partner_by_barcode[barcode]; },
        get_partners_sorted: function (max_count) {
            max_count = max_count ? Math.min(max_count, this.partner_sorted.length) : this.partner_sorted.length;
            return this.partner_sorted.slice(0, max_count).map(id => this.partner_by_id[id]);
        },
        search_partner: function (query) {
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g, '.').replace(/ /g, '.+');
                var re = RegExp("([0-9]+):.*?" + utils.unaccent(query), "gi");
            } catch (e) { return []; }

            var results = [], r;
            while ((r = re.exec(this.partner_search_string)) !== null && results.length < this.limit) {
                results.push(this.get_partner_by_id(Number(r[1])));
            }
            return results;
        },

        // --- Orders ---
        add_order: function (order) {
            var orders = this.load('orders', []);
            var order_id = order.uid;

            var existing = orders.find(o => o.id === order_id);
            if (existing) { existing.data = order; this.save('orders', orders); return order_id; }

            this.remove_unpaid_order(order);
            orders.push({ id: order_id, data: order });
            this.save('orders', orders);
            return order_id;
        },
        remove_order: function (order_id) {
            var orders = this.load('orders', []);
            orders = orders.filter(o => o.id !== order_id);
            this.save('orders', orders);
        },
        remove_all_orders: function () { this.save('orders', []); },
        get_orders: function () { return this.load('orders', []); },
        get_order: function (order_id) {
            return this.get_orders().find(o => o.id === order_id);
        },

        save_unpaid_order: function (order) {
            var orders = this.load('unpaid_orders', []);
            var serialized = order.export_as_JSON();
            var existing = orders.find(o => o.id === order.uid);
            if (existing) { existing.data = serialized; this.save('unpaid_orders', orders); return order.uid; }
            orders.push({ id: order.uid, data: serialized });
            this.save('unpaid_orders', orders);
            return order.uid;
        },
        remove_unpaid_order: function (order) {
            var orders = this.load('unpaid_orders', []);
            orders = orders.filter(o => o.id !== order.uid);
            this.save('unpaid_orders', orders);
        },
        remove_all_unpaid_orders: function () { this.save('unpaid_orders', []); },
        get_unpaid_orders: function () { return this.load('unpaid_orders', []).map(o => o.data); },

        get_unpaid_orders_to_sync: function (ids) {
            return this.load('unpaid_orders', []).filter(o => ids.includes(o.id) && (o.data.server_id || o.data.lines.length || o.data.statement_ids.length));
        },
        set_order_to_remove_from_server: function (order) {
            if (order.server_id !== undefined) {
                var to_remove = this.load('unpaid_orders_to_remove', []);
                to_remove.push(order.server_id);
                this.save('unpaid_orders_to_remove', to_remove);
            }
        },
        get_ids_to_remove_from_server: function () {
            return this.load('unpaid_orders_to_remove', []);
        },
        set_ids_removed_from_server: function (ids) {
            var to_remove = this.load('unpaid_orders_to_remove', []);
            to_remove = to_remove.filter(id => !ids.includes(id));
            this.save('unpaid_orders_to_remove', to_remove);
        },

        // --- Cashier ---
        set_cashier: function (cashier) { this.save('cashier', cashier || null); },
        get_cashier: function () { return this.load('cashier'); },

        // --- Storage ---
        load: function (store, deft) {
            if (this.cache[store] !== undefined) return this.cache[store];
            var data = localStorage[this.name + '_' + store];
            if (data) { data = JSON.parse(data); this.cache[store] = data; return data; }
            return deft;
        },
        save: function (store, data) {
            localStorage[this.name + '_' + store] = JSON.stringify(data);
            this.cache[store] = data;
        },

        clear: function () {
            Array.from(arguments).forEach(store => localStorage.removeItem(this.name + '_' + store));
        }
    });

    return PosDB;
});
