# -*- coding: utf-8 -*-
"""
For inter_company_transfer_ept module.
"""
from odoo import models, fields as field


class SaleReport(models.Model):
    """
    Inherited for adding relation with inter company transfer.
    @author: Maulik Barad on Date 18-Jan-2021.
    """
    _inherit = "sale.report"

    inter_company_transfer_id = field.Many2one('inter.company.transfer.ept', string="ICT",
                                               groups="intercompany_transaction_ept.inter_company_transfer_user_group,"
                                                      "intercompany_transaction_ept."
                                                      "inter_company_transfer_manager_group",
                                               copy=False, help="Reference of ICT.", readonly=True)

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if not fields:
            fields = {}
        fields['inter_company_transfer_id'] = ", s.inter_company_transfer_id as inter_company_transfer_id"
        groupby += ', s.inter_company_transfer_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
