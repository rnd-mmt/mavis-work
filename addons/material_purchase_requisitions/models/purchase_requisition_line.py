# -*- coding: utf-8 -*-

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp

class MaterialPurchaseRequisitionLine(models.Model):
    _name = "material.purchase.requisition.line"
    _description = 'Material Purchase Requisition Lines'

    
    requisition_id = fields.Many2one(
        'material.purchase.requisition',
        string='Demandes',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Produit',
        required=True,
    )
#     layout_category_id = fields.Many2one(
#         'sale.layout_category',
#         string='Section',
#     )
    description = fields.Char(
        string='Description',
        required=True,
    )
    qty = fields.Float(
        string='Quantité',
        default=1,
        required=True,
    )
    uom = fields.Many2one(
        'uom.uom',#product.uom in odoo11
        string='Unité de Measure',
        required=True,
    )
    partner_id = fields.Many2many(
        'res.partner',
        string='Vendeurs',
    )
    requisition_type = fields.Selection(
        selection=[
                    ('internal','Internal Picking'),
                    ('purchase','Purchase Order'),
        ],
        string='Action de la demande',
        default='internal',
        required=True,
    )
    demandeur = fields.Many2one(
        'res.partner',
        string='Demandeur',
        copy=True,
    )
    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            rec.description = rec.product_id.name
            rec.uom = rec.product_id.uom_id.id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
