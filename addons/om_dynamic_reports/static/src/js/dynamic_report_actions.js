odoo.define('om_dynamic_reports.DynamicReportActions', function (require) {
    "use strict";

    var DynamicReports = require('om_dynamic_reports.DynamicReports');
    var core = require("web.core");
    var session = require("web.session");

    var Qweb = core.qweb;

    DynamicReports.include({
        events: _.extend(DynamicReports.prototype.events, {
            'click li.action_item': 'selectAction',
        }),
        selectAction: function (e) {
            var act_id = $(e.currentTarget).find("a").data('action');
            var active_el = $(e.currentTarget);
            var data_id = parseInt(active_el.closest('tr').data('id'));
            this.context = {
                sel_account_ids: [data_id],
                act_id: act_id,
            };
            this._setControllerData(act_id);
            this.$el.find('select').select2();
            this._getReportContent(e);
        },
        _setControllerData: function (r_name) {
            this.report_data.account_report_id = [r_name, this._getReportName(r_name)];
            this.report_data.company_id = session.company_id;
            switch (r_name) {
                case 'journals_audit': {
                    this.$el.find('.ctrl_body').replaceWith($(Qweb.render('journals_audit', {widget: this})));
                    this.addField('target_move', 'select');
                    this.addField('sort_selection', 'select');
                    this.addField('date_from', 'input');
                    this.addField('date_to', 'input');
                    this.addField('journal_ids', 'select');

                    break;
                };
                case 'partner_ledger': {
                    this.$el.find('.ctrl_body').replaceWith($(Qweb.render('partner_ledger', {widget: this})));

                    this.addField('target_move', 'select');
                    this.addField('result_selection', 'select');
                    this.addField('reconciled', 'checkbox');
                    this.addField('date_from', 'input');
                    this.addField('date_to', 'input');
                    this.addField('journal_ids', 'select');

                    break;
                };
                case 'general_ledger': {
                    this.$el.find('.ctrl_body').replaceWith($(Qweb.render('general_ledger', {widget: this})));

                    this.addField('target_move', 'select');
                    this.addField('sortby', 'select');
                    this.addField('display_account', 'select');
                    this.addField('initial_balance', 'checkbox');
                    this.addField('date_from', 'input');
                    this.addField('date_to', 'input');
                    this.addField('journal_ids', 'select');

                    break;
                };
                case 'trial_balance': {
                    this.$el.find('.ctrl_body').replaceWith($(Qweb.render('trial_balance', {widget: this})));

                    this.addField('target_move', 'select');
                    this.addField('display_account', 'select');
                    this.addField('date_from', 'input');
                    this.addField('date_to', 'input');
                    break;
                };
                case 'aged_partner': {
                    this.$el.find('.ctrl_body').replaceWith($(Qweb.render('aged_partner', {widget: this})));

                    this.addField('target_move', 'select');
                    this.addField('result_selection', 'select');
                    this.addField('date_from', 'input');
                    this.addField('period_length', 'input');

                    this.$el.find('.ctrl_body .date_from').addClass('o_required');
                    this.$el.find('.ctrl_body .period_length').addClass('o_required');

                    break;
                };
                case 'tax_report': {
                    this.$el.find('.ctrl_body').replaceWith($(Qweb.render('tax_report', {widget: this})));
                    this.addField('date_from', 'input');
                    this.addField('date_to', 'input');

                    this.$el.find('.ctrl_body .date_from').addClass('o_required');
                    this.$el.find('.ctrl_body .date_to').addClass('o_required');

                    break;
                };
                default: {
                    this.$el.find('.ctrl_body').replaceWith($(Qweb.render('profit_loss', {widget: this})));

                    this.addField('target_move', 'select');
                    this.addField('debit_credit', 'checkbox');
                    this.addField('date_from', 'input');
                    this.addField('date_to', 'input');
                };
            };
            this.$el.find('select.account_report_id').val(this.report_data.account_report_id[0]);
        }
    });
});
