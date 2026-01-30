# -*- coding: utf-8 -*-

from odoo import models
# == IMPRESSION EXCEL ===
import json
from odoo.tools import date_utils

class AccountTaxReport(models.TransientModel):
    _inherit = "account.common.report"
    _name = 'account.tax.report.wizard'
    _description = 'Tax Report'

    def _print_report(self, data):
        return self.env.ref('accounting_pdf_reports.action_report_account_tax').report_action(self, data=data)

    def _print_xlsx(self , data):
        data['form'].update({ 'report_tax' : "tax_report"})
        return {
            'data': {'model': 'accounting.report',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': "Rapport Fiscal",
                     },
            'report_type': 'xlsx',
        }
