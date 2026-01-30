# -*- coding: utf-8 -*-

from odoo import fields, models
import json
from odoo.tools import date_utils

class AccountPrintJournal(models.TransientModel):
    _inherit = "account.common.journal.report"
    _name = "account.print.journal"
    _description = "Account Print Journal"

    sort_selection = fields.Selection([('date', 'Date'), ('move_name', 'Journal Entry Number'),], 'Entries Sorted by', required=True, default='move_name')
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True, default=lambda self: self.env['account.journal'].search([('type', 'in', ['sale', 'purchase'])]))

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update({'sort_selection': self.sort_selection})
        return self.env.ref('accounting_pdf_reports.action_report_journal').with_context(landscape=True).report_action(self, data=data)

    #=== POUR EXPORT EXCEL ===
    def _print_xlsx(self, data):
        data = self.pre_print_report(data)
        data['form'].update({'sort_selection': self.sort_selection ,  'report_journal_name' : "journal_audit"})
        return {
            'data': {'model': 'accounting.report',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': "journal_autidt_report",
                     },
            'report_type': 'xlsx',
        }
