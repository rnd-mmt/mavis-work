# -*- encoding: utf-8 -*-
from odoo import api, fields, models,_


class ResCompany(models.Model):
    _inherit = "res.company"

    coprest_product_id = fields.Many2one('product.product', string='Produit pour commission prestataire')
    coprest_on_invoice_amount = fields.Boolean(string="Commission du prestataire selon les factures")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    coprest_product_id = fields.Many2one('product.product', related='company_id.coprest_product_id', 
        string='Produit de la commission prestataire', readonly=False)
    coprest_on_invoice_amount = fields.Boolean(related='company_id.coprest_on_invoice_amount', 
        string="Commission du prestataire selon les factures", readonly=False)