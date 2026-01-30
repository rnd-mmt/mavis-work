# -*- coding: utf-8 -*-

from odoo import models, fields

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'
    
    helpdesk_support_id = fields.Many2one(
        'helpdesk.support',
        string='Helpdesk Support',
        readonly=True,
    )
