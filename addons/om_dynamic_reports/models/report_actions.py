# -*- coding: utf-8 -*-
# License: Odoo Proprietary License v1.0

from odoo import api, models


try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class DynamicReportActions(models.TransientModel):
    _inherit = 'dynamic.report.config'

    def _get_account_ids(self):
        s_domain = []
        ac_ids = self._context.get('sel_account_ids', [])
        if ac_ids:
            s_domain += [('id', 'in', ac_ids)]
        return self.env['account.account'].search(s_domain)

