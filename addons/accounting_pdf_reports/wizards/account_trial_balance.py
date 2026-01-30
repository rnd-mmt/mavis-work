# -*- coding: utf-8 -*-

from odoo import fields, models
#== POUR EXPORT EXCEL ==
import json
from odoo.tools import date_utils

class AccountBalanceReport(models.TransientModel):
    _inherit = "account.common.account.report"
    _name = 'account.balance.report'
    _description = 'Trial Balance Report'

    journal_ids = fields.Many2many('account.journal', 'account_balance_report_journal_rel', 'account_id', 'journal_id', string='Journals', required=True, default=[])

    def _print_report(self, data):
        data = self.pre_print_report(data)
        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env.ref('accounting_pdf_reports.action_report_trial_balance').report_action(records, data=data)

    #==POUR EXPORT EXCEL==
    def _print_xlsx(self , data):
        data = self.pre_print_report(data)
        data['form'].update({ 'report_trial_balance_name' : "trial_balance"})
        return {
            'data': {'model': 'accounting.report',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': "Balance de vérification",
                     },
            'report_type': 'xlsx',
        }
