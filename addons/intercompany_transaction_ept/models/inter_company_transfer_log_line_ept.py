# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class InterCompanyTransferLogLineEpt(models.Model):
    """
    For managing the Log details of Inter Company and Internal Warehouse Transfers.
    @author: Maulik Barad.
    """
    _name = "inter.company.transfer.log.line.ept"
    _description = 'Inter Company Transfer Log Line'

    ict_message = fields.Text(string="Message")
    ict_log_type = fields.Selection([('error', 'Error'), ('mismatch', 'Mismatch'), ('info', 'Info')], string="Log Type")
    ict_log_id = fields.Many2one('inter.company.transfer.log.book.ept', string="ICT Process Log", ondelete='cascade')
