# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    account_report_template_id = fields.Many2one(
        comodel_name='ir.actions.report',
        string='Invoice Report Template',
        domain="[('model', '=', 'account.move'), ('report_type', '=', 'qweb-pdf')]",
        help="Default report template for invoices specific to this company.",
        company_dependent=True
    )

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    account_report_template_id = fields.Many2one(
        related='company_id.account_report_template_id',
        string='Invoice Report Template',
        readonly=False,
        domain="[('model', '=', 'account.move'), ('report_type', '=', 'qweb-pdf')]",
        help="Default report template for invoices specific to the selected company."
    )