# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class PriceSimulationLine(models.TransientModel):
    _name = 'pricelist.simulator.line.wizard'
    _description = 'Move Confirmation Line'

    
    @api.depends('quantity', 'sale_price')
    def _compute_amount(self):
        for line in self:
            line.amount_total = line.quantity * line.sale_price

    price_id = fields.Many2one('pricelist.simulator.wizard', string='Service', readonly=True)
    product = fields.Many2one('product.product', string='Product', tracking=True)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product.uom_id.category_id', readonly=True)
    sale_price = fields.Float(string='Sale Price', readonly=True, tracking=True)
    quantity = fields.Float(string='Quantity', tracking=True)
    amount_total = fields.Float(compute="_compute_amount", string="Sub Total")

    @api.onchange('product')
    def onchange_test(self):
        if self.product:
            self.sale_price = self.product.lst_price
            self.product_uom = self.product.uom_id.id
            self.quantity = 1

class PriceSimulation(models.TransientModel):
    _name = 'pricelist.simulator.wizard'
    _description = "Wizard for pricelist simulator"

    pricelist_id = fields.Many2one('product.pricelist', string='Liste de prix')
    service_line = fields.One2many('pricelist.simulator.line.wizard','price_id', string='Ligne de service')
    total_price = fields.Float(compute="_get_total_price", string='Total')

    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id.id)

    prise_charge = fields.Selection([
       # ('fonctionnaire', 'Fonctionnaire'),
       # ('prise_en_charge_100', 'Prise en charge 100%'),
        ('sans_plafond', 'Sans plafond'),
        ('plafond_motant_total', 'Avec plafond sur motant total'),
        ('plafond_par_article', 'Avec plafond par article'),
    ], 'Prise en charge')
    percentage = fields.Float("Ticket modérateur", default=100)
    total_plafond = fields.Float("Plafond")
    amount_assurance = fields.Float(string="Part assurance", default=0.0)
    amount_patient = fields.Float(string="Part patient", default=0.0)
    type_pricelist = fields.Boolean(related="pricelist_id.for_insurance")

    @api.depends('service_line', 'service_line.amount_total')
    def _get_total_price(self):
        for rec in self:
            rec.total_price = sum(line.amount_total for line in rec.service_line)

    @api.depends('total_price', 'percentage', 'total_plafond', 'prise_charge')
    def calculate_payment(self):
        for record in self:
            record.amount_assurance = 0.0
            record.amount_patient = 0.0
            if record.prise_charge in ['prise_en_charge_100','fonctionnaire']:
                record.amount_assurance = record.total_price
                record.amount_patient = 0.0
            elif record.prise_charge == 'sans_plafond':
                insurance_result = (record.percentage / 100) * record.total_price
                record.amount_assurance = insurance_result
                record.amount_patient = record.total_price - insurance_result
            elif record.prise_charge == "plafond_motant_total":
                insurance_result = (record.percentage / 100) * record.total_price
                if insurance_result <= record.total_plafond:
                    record.amount_assurance = insurance_result
                    record.amount_patient = record.total_price - insurance_result
                else:
                    record.amount_assurance = record.total_plafond
                    record.amount_patient = record.total_price - record.total_plafond
            elif record.prise_charge == 'plafond_par_article':
                total_assurance = 0.0
                total_patient = 0.0
                total_plafond = self.total_plafond
                for line in record.service_line:
                    insurance_result_line = (record.percentage / 100) * line.sale_price
                    if insurance_result_line <= total_plafond:
                        total_assurance += insurance_result_line
                        total_patient += line.sale_price - insurance_result_line
                    else:
                        total_assurance += total_plafond
                        total_patient += line.sale_price - total_plafond
                record.amount_assurance = total_assurance
                record.amount_patient = total_patient

    def update_price(self):
        if not self.pricelist_id:
            return
        for line in self.service_line:
            if line.product:
                price_dict = line.product.with_context(pricelist=self.pricelist_id.id)
                line.sale_price = price_dict.price
        self._get_total_price()
        # Split invoice based on insurance
        self.calculate_payment()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pricelist.simulator.wizard',
            'name': _('Simulateur de prix'),
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

