# -*- coding: utf-8 -*-

from odoo import fields, models, _
# == POUR EXPORT EXCEL ==
import json
from odoo.tools import date_utils


class AccountPartnerLedger(models.TransientModel):
    _inherit = "account.common.partner.report"
    _name = "account.report.partner.ledger"
    _description = "Account Partner Ledger"

    amount_currency = fields.Boolean("With Currency",
                                     help="It adds the currency column on report if the "
                                          "currency differs from the company currency.")
    reconciled = fields.Boolean('Reconciled Entries')

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled, 'amount_currency': self.amount_currency})
        return self.env.ref('accounting_pdf_reports.action_report_partnerledger').report_action(self, data=data)

    #=== POUR EXPORT EXCEL GRAND LIVRE DES TIERS ===
    def _print_xlsx(self , data):
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled, 'amount_currency': self.amount_currency ,  'report_partner_ledger_name' : "partner_ledger"})
        return {
            'data': {'model': 'accounting.report',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': "Grand livre des partenaires",
                     },
            'report_type': 'xlsx',
        }
