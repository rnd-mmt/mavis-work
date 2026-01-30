# -*- coding: utf-8 -*-

from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    custom_requisition_id = fields.Many2one(
        'material.purchase.requisition',
        string="Demandes d'achat",
        copy=False
    )

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    custom_requisition_line_id = fields.Many2one(
        'material.purchase.requisition.line',
        string="Ligne des demandes d'achat",
        copy=False
    )
