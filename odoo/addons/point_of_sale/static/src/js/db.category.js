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

            // Cache général
            this.cache = {};

            // Produits
            this.product_by_id = {};
            this.product_by_barcode = {};
            this.product_by_category_id = {};
            this.category_search_string = {};

            // Catégories
            this.category_by_id = {};
            this.category_parent = {};
            this.category_childs = {};
            this.category_ancestors = {};
            this.root_category_id = 0;

            // Partenaires
            this.partner_sorted = [];
            this.partner_by_id = {};
            this.partner_by_barcode = {};
            this.partner_search_string = "";
            this.partner_write_date = null;
        },

        set_uuid: function (uuid) {
            this.name = this.name + '_' + uuid;
        },

        add_categories: function (categories) {
            var self = this;
            if (!this.category_by_id[this.root_category_id]) {
                this.category_by_id[this.root_category_id] = { id: this.root_category_id, name: 'Root' };
            }

            // Ajouter la catégorie spéciale "All"
            const allCategory = { id: 0, name: 'All', parent_id: false, child_id: categories.map(c => c.id) };
            categories.unshift(allCategory);

            // remplir les structures
            categories.forEach(cat => { self.category_by_id[cat.id] = cat; });
            categories.forEach(cat => {
                var parent_id = cat.parent_id && cat.parent_id[0] ? cat.parent_id[0] : this.root_category_id;
                self.category_parent[cat.id] = parent_id;
                if (!self.category_childs[parent_id]) self.category_childs[parent_id] = [];
                if (!self.category_childs[parent_id].includes(cat.id)) self.category_childs[parent_id].push(cat.id);
            });

            // créer les ancêtres de chaque catégorie
            function make_ancestors(cat_id, ancestors, visited = {}) {
                if (visited[cat_id]) return; // ⚠ éviter la récursion infinie
                visited[cat_id] = true;

                self.category_ancestors[cat_id] = ancestors;
                var next = ancestors.slice(); next.push(cat_id);

                var childs = self.category_childs[cat_id] || [];
                childs.forEach(child_id => make_ancestors(child_id, next, visited));
            }


            make_ancestors(this.root_category_id, []);
            make_ancestors(0, []); // s'assurer que "All" a des ancêtres
        },
        get_category_by_id: function (categ_id) {
            if (Array.isArray(categ_id)) return categ_id.map(id => this.category_by_id[id]).filter(Boolean);
            return this.category_by_id[categ_id];
        },
        get_category_childs_ids: function (categ_id) { return this.category_childs[categ_id] || []; },
        get_category_ancestors_ids: function (categ_id) { return this.category_ancestors[categ_id] || []; },
        get_category_parent_id: function (categ_id) { return this.category_parent[categ_id] || this.root_category_id; },
        category_contains: function (categ_id, product_id) {
            var product = this.product_by_id[product_id];
            if (!product || !product.pos_categ_id) return false;
            var cid = product.pos_categ_id[0];
            while (cid && cid !== categ_id) cid = this.category_parent[cid];
            return !!cid;
        },
        // ---------- Produits ----------
        _product_search_string: function (product) {
            var str = product.display_name || '';
            [product.barcode, product.default_code, product.description, product.description_sale].forEach(f => {
                if (f) str += '|' + f;
            });
            return product.id + ':' + str.replace(/[\n:]/g, '') + '\n';
        },
        add_products: function (products) {
            if (!Array.isArray(products)) products = [products];

            var stored_categories = this.product_by_category_id || {};
            this.product_by_category_id = stored_categories;

            products.forEach(product => {

                // empêcher duplication
                if (this.product_by_id[product.id]) return;

                // sécuriser la catégorie
                var categ_id = (product.categ_id && product.categ_id[0]) ? product.categ_id[0] : 0;

                // ajouter dans base principale
                this.product_by_id[product.id] = product;

                if (product.barcode)
                    this.product_by_barcode[product.barcode] = product;

                if (Array.isArray(product.product_tmpl_id))
                    product.product_tmpl_id = product.product_tmpl_id[0];

                // ajouter dans la catégorie principale
                if (!stored_categories[categ_id]) stored_categories[categ_id] = [];
                stored_categories[categ_id].push(product.id);

                // éviter boucle infinie ancestors
                let ancestors = this.get_category_ancestors_ids(categ_id) || [];
                ancestors = ancestors.filter(a => a && a !== categ_id);

                ancestors.forEach(ancestor => {
                    if (!stored_categories[ancestor]) stored_categories[ancestor] = [];
                    if (!stored_categories[ancestor].includes(product.id)) {
                        stored_categories[ancestor].push(product.id);
                    }
                });

                // ajouter dans "All products" (catégorie racine id=0)
                if (!stored_categories[0]) stored_categories[0] = [];
                if (!stored_categories[0].includes(product.id))
                    stored_categories[0].push(product.id);

                // construction du search string
                var s = utils.unaccent(this._product_search_string(product));

                if (!this.category_search_string[categ_id])
                    this.category_search_string[categ_id] = '';
                this.category_search_string[categ_id] += s;

                ancestors.forEach(a => {
                    if (!this.category_search_string[a])
                        this.category_search_string[a] = '';
                    this.category_search_string[a] += s;
                });
            });
        },

        add_products_by_product_category: function (products) { this.add_products(products); },
        get_product_by_id: function (id) {
            return this.product_by_id[id];
        },
        get_product_by_barcode: function (barcode) { return this.product_by_barcode[barcode]; },
        get_product_by_category: function (category_id) {
            var list = [];
            var product_ids = this.product_by_category_id[category_id] || [];
            product_ids.forEach(pid => {
                var p = this.product_by_id[pid];
                if (p && p.active && p.available_in_pos) list.push(p);
            });
            return list;
        },
        search_product_in_category: function (category_id, query) {
            try { query = utils.unaccent(query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g, '.').replace(/ /g, '.+')); } catch (e) { return []; }
            var re = RegExp("([0-9]+):.*?" + query, "gi"), results = [];
            var str = this.category_search_string[category_id];
            if (!str) return [];
            var count = 0;
            while (count < this.limit) {
                var r = re.exec(str);
                if (!r) break;
                var p = this.get_product_by_id(Number(r[1]));
                if (p && p.active && p.available_in_pos) results.push(p);
                count++;
            }
            return results;
        },
        is_product_in_category: function (category_ids, product_id) {
            if (!Array.isArray(category_ids)) category_ids = [category_ids];
            var cat = this.product_by_id[product_id]?.pos_categ_id?.[0];
            while (cat) {
                if (category_ids.includes(cat)) return true;
                cat = this.get_category_parent_id(cat);
            }
            return false;
        },

        // ---------- Partenaires ----------
        _partner_search_string: function (partner) {
            var str = partner.name || '';
            [partner.barcode, partner.address, partner.phone, partner.mobile, partner.email, partner.vat].forEach(f => {
                if (f) str += '|' + (typeof f === 'string' ? f : '');
            });
            return partner.id + ':' + str.replace(/[\n:]/g, '') + '\n';
        },
        add_partners: function (partners) {
            var new_write_date = this.partner_write_date || '';

            partners.forEach(p => {

                // éviter écrasement + contrôle des write_date
                if (this.partner_by_id[p.id] &&
                    new Date(this.partner_write_date) + 1000 >= new Date(p.write_date)) return;

                if (new_write_date < p.write_date)
                    new_write_date = p.write_date;

                // ajouter dans tri
                if (!this.partner_by_id[p.id])
                    this.partner_sorted.push(p.id);

                // enregistrer
                this.partner_by_id[p.id] = p;
            });

            this.partner_write_date = new_write_date;

            // reconstruction globale du search
            this.partner_search_string = '';
            this.partner_by_barcode = {};

            for (var id in this.partner_by_id) {
                var partner = this.partner_by_id[id];

                if (partner.barcode)
                    this.partner_by_barcode[partner.barcode] = partner;

                this.partner_search_string += this._partner_search_string(partner);
            }

            this.partner_search_string = utils.unaccent(this.partner_search_string);
        },

        get_partner_write_date: function () { return this.partner_write_date || "1970-01-01 00:00:00"; },
        get_partner_by_id: function (id) { return this.partner_by_id[id]; },
        get_partner_by_barcode: function (barcode) { return this.partner_by_barcode[barcode]; },
        get_partners_sorted: function (max_count) {
            max_count = max_count ? Math.min(this.partner_sorted.length, max_count) : this.partner_sorted.length;
            return this.partner_sorted.slice(0, max_count).map(id => this.partner_by_id[id]);
        },
        search_partner: function (query) {
            try { query = utils.unaccent(query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g, '.').replace(/ /g, '.+')); } catch (e) { return []; }
            var re = RegExp("([0-9]+):.*?" + query, "gi"), results = [];
            var count = 0;
            while (count < this.limit) {
                var r = re.exec(this.partner_search_string);
                if (!r) break;
                var p = this.get_partner_by_id(Number(r[1]));
                if (p) results.push(p);
                count++;
            }
            return results;
        },


        add_order: function (order) {
            var orders = this.load('orders', []);
            orders = orders.filter(o => o.id !== order.uid);
            orders.push({ id: order.uid, data: order });
            this.save('orders', orders);
            return order.uid;
        },
        remove_order: function (order_id) { this.save('orders', this.load('orders', []).filter(o => o.id !== order_id)); },
        remove_all_orders: function () { this.save('orders', []); },
        get_orders: function () { return this.load('orders', []); },
        get_order: function (order_id) { return this.get_orders().find(o => o.id === order_id); },

        save_unpaid_order: function (order) {
            var orders = this.load('unpaid_orders', []);
            var serialized = order.export_as_JSON();
            orders = orders.filter(o => o.id !== order.uid);
            orders.push({ id: order.uid, data: serialized });
            this.save('unpaid_orders', orders);
            return order.uid;
        },
        remove_unpaid_order: function (order) { this.save('unpaid_orders', this.load('unpaid_orders', []).filter(o => o.id !== order.uid)); },
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
        get_ids_to_remove_from_server: function () { return this.load('unpaid_orders_to_remove', []); },
        set_ids_removed_from_server: function (ids) {
            var to_remove = this.load('unpaid_orders_to_remove', []).filter(id => !ids.includes(id));
            this.save('unpaid_orders_to_remove', to_remove);
        },

        // ---------- Cashier ----------
        set_cashier: function (cashier) { this.save('cashier', cashier || null); },
        get_cashier: function () { return this.load('cashier'); },

        // ---------- LocalStorage ----------
        load: function (store, deft) {
            if (this.cache[store] !== undefined) return this.cache[store];
            var data = localStorage[this.name + '_' + store];
            if (data) data = JSON.parse(data);
            this.cache[store] = data || deft;
            return this.cache[store];
        },
        save: function (store, data) { localStorage[this.name + '_' + store] = JSON.stringify(data); this.cache[store] = data; },
        clear: function () { Array.from(arguments).forEach(store => localStorage.removeItem(this.name + '_' + store)); },
        _count_props: function (obj) { return Object.keys(obj).length; },
    });

    return PosDB;
});
