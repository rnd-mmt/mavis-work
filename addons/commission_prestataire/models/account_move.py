# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    coprest_partner_ids = fields.Many2many("res.partner", "invoice_coprest_rel", "invoice_id", "partner_id", "Liste prestataires")
    coprest_ids = fields.One2many('commission.prestataire', 'invoice_id', 'Ligne commission prestataire')
    coprest_type = fields.Selection([
        ('automatic', 'Automatic'),
        ('fix_amount', 'On Fix Amount'),
    ], string='Type de commission', default='automatic', required=True)
    coprest_created = fields.Boolean("Commission créée")
    coprest_on = fields.Float('Commission sur')
    hospital_invoice_type = fields.Selection(selection_add=[('coprest', 'Commission prestataire')])


    @api.onchange('amount_untaxed')
    def onchange_total_amount(self):
        if self.company_id.coprest_on_invoice_amount:
            self.coprest_on = self.amount_untaxed

    @api.onchange('ref_physician_id')
    def onchange_ref_physician(self):
        if self.ref_physician_id and self.ref_physician_id.prest_commission:
            self.coprest_partner_ids = [(4, self.ref_physician_id.id)]

    @api.onchange('physician_id')
    def onchange_physician(self):
        if self.physician_id:
            #ACS NOTE: no need but sudo do not work for portal access.
            physician = self.env['hms.physician'].sudo().search([('id','=',self.sudo().physician_id.id)])
            if physician.prest_commission:
                self.coprest_partner_ids = [(4, physician.partner_id.id)]

    def create_coprest_commission(self, partner, amount, coprest_on):
        Commission = self.env['commission.prestataire']
        commission_line = Commission.search([('partner_id','=',partner.id),('invoice_id','=',self.id)], limit=1)
        if commission_line:
            commission_line.write({
                'coprest_amount': amount,
                'coprest_on': coprest_on,
            })
        else:
            Commission.create({
                'partner_id': partner.id,
                'coprest_amount': amount,
                'coprest_on': coprest_on,
                'invoice_id': self.id,
            })            

    def compute_coprest_commission(self, partner):
        amount = coprest_on = 0
        Rule = self.env['commission.prestataire.rule']
        
        for line in self.invoice_line_ids:
            if line.product_id:
                matching_rule = False
                product_tmpl_id = line.product_id.product_tmpl_id.id
                product_categ_id = line.product_id.categ_id.id
                if partner.coprest_rule_ids:
                    coprest_ids = partner.coprest_rule_ids.ids
                    matching_rule = Rule.search([('id','in',coprest_ids),
                        ('product_id','=',product_tmpl_id)], limit=1)
                    if not matching_rule:
                        matching_rule = Rule.search([('id','in',coprest_ids),
                        ('product_category_id','=',product_categ_id)], limit=1)

                if not matching_rule and partner.coprest_role_id:
                    role_commission_ids = partner.coprest_role_id.coprest_rule_ids.ids
                    matching_rule = Rule.search([('id','in', role_commission_ids),
                        ('product_id','=',product_tmpl_id)], limit=1)
                    if not matching_rule:
                        matching_rule = Rule.search([('id','in', role_commission_ids),
                        ('product_category_id','=',product_categ_id)], limit=1)

                if matching_rule:
                    if matching_rule.get_number == True:
                        amount += (matching_rule.percentage * line.price_subtotal)/100 + (matching_rule.part_prest * line.quantity)
                        coprest_on += line.price_subtotal
                    else:
                        amount += (matching_rule.percentage * line.price_subtotal) / 100 + matching_rule.part_prest
                        coprest_on += line.price_subtotal


                elif partner.coprest_percentage:
                    amount += (partner.coprest_percentage * line.price_subtotal)/100
                    coprest_on += line.price_subtotal

            self.create_coprest_commission(partner, amount, coprest_on)
        return amount

    def update_coprest_values(self):
        Commission = self.env['commission.prestataire']
        for rec in self:
            if rec.coprest_type=='automatic':
                for partner in rec.coprest_partner_ids:
                    self.compute_coprest_commission(partner)
            else:
                if rec.coprest_on==0:
                    raise UserError(_("Please Set Amount to calculate Commission"))

                for partner in rec.coprest_partner_ids:
                    amount = (partner.coprest_percentage * self.coprest_on)/100
                    self.create_coprest_commission(partner, amount, self.coprest_on)

            #remove extra lines
            commission_line = Commission.search([('partner_id','not in',rec.coprest_partner_ids.ids),('invoice_id','=',self.id),('service_state','=',self.payment_state)])
            commission_line.sudo().unlink()

    def finalize_coprest(self):
        for rec in self:
            if not rec.coprest_ids:
                raise UserError(_("No Commission Lines to Finalize! Please create them first."))
            rec.coprest_created = True
            rec.coprest_ids.action_done()

#====CREATION COMMISSION PRESTATAIRE AUTOMATIQUE LORS D4UN ENREGISTREMENT DE PAIEMENT
    def action_register_payment(self):
        for rec in self:
            if rec.coprest_partner_ids:
                if rec.coprest_ids:
                    for line in rec.coprest_ids:
                        line.state = 'serv_paid'
        return super(AccountMove, self).action_register_payment()

    def button_draft(self):
        for rec in self:
            if rec.coprest_partner_ids:
                if rec.coprest_ids:
                    for line in rec.coprest_ids:
                        line.state = 'draft'
        return super(AccountMove, self).button_draft()

    def button_cancel(self):
        for rec in self:
            if rec.coprest_partner_ids:
                if rec.coprest_ids:
                    for line in rec.coprest_ids:
                        line.state = 'cancel'
        return super(AccountMove, self).button_cancel()

    def action_reverse(self):
        for rec in self:
            if rec.coprest_partner_ids:
                if rec.coprest_ids:
                    for line in rec.coprest_ids:
                        line.state = 'cancel'
        return super(AccountMove, self).action_reverse()