from odoo import models, api, _


class AccountAccount(models.Model):
    _inherit = "account.account"

    @api.model
    def get_import_templates(self):
        return [{
            'label': _('Export a template for the chart of accounts'),
            'template': '/l10n_mg_reports_c/static/xls/account_account.xls'
        }]
