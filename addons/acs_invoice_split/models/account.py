# -*- coding: utf-8 -*-

from odoo import api,fields,models,_
from odoo.exceptions import ValidationError

import odoo.modules as addons
loaded_modules = addons.module.loaded

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    company_acronym = fields.Char("Contact Acronym")
    invoice_contact_type = fields.Selection([
        ('BG', 'Public'),
        ('BA', 'Privé'),
    ], string='Invoice Contact Type', default='BG')
    invoice_contact_bank = fields.Selection([
        ('BOA MADAGASCAR', 'BOA MADAGASCAR'),
        ('BAOBAB', 'BAOBAB'),
    ], string='Invoice Contact Type', default='BOA MADAGASCAR')
    type_paid = fields.Selection([
        ('ESPECE', 'ESPECE'),
        ('VIREMENT', 'VIREMENT'),
        ('CHEQUE', 'CHEQUE'),
        ('M-VOLA', 'M-VOLA'),
        ('ORANGE MONEY', 'ORANGE MONEY'),
      #  ('MOBILE MONEY', 'MOBILE MONEY'),
        ('TPE', 'TPE'),
    ], string='Mode de paiement', default='ESPECE')
    
class AccountMove(models.Model):
    _inherit = "account.move"

    # ====  info sur paiement field
    amount_insurance = fields.Monetary(string='Part assurance', default=0.0, currency_field='company_currency_id')
    amount_patient = fields.Monetary(string='Part Patient', default=0.0, currency_field='company_currency_id')
    amount_insurance_words = fields.Char("Montant part assurance (In Words)", compute="_compute_amount_words")
    amount_patient_words = fields.Char("Montant part patient (In Words)", compute="_compute_amount_words")
    #==== historique assurance ====
    ceiling_type = fields.Selection([
        ('fonctionnaire','Type fonctionnaire'),
        ('no_ceiling', 'Sans Plafond'),
        ('with_ceiling', 'Avec Plafond sur montant total'),
        ('with_ceiling_article', 'Avec Plafond par particle'),
    ], 'Type plafond/Profil')
    percentage_by_assurance = fields.Float(string='Taux Assurance (%)', default=0.00)
    percentage_by_patient = fields.Float(string='Taux Patient (%)', default=0.00)
    ceiling = fields.Monetary(string="Plafond", default=0.0, currency_field='company_currency_id')
    result_taux_assurance = fields.Monetary(string="Resultat taux assurance", default=0.0,
                                                  currency_field='company_currency_id')
    result_taux_patient = fields.Monetary(string="Resultat taux patient", default=0.0,
                                                currency_field='company_currency_id')
    initial_amount = fields.Monetary(string='Montant Initial', default=0.00, currency_field='company_currency_id')
    exceeding = fields.Monetary(string="Dépassement", default=0.0, currency_field='company_currency_id')
    patient_display_name = fields.Char(compute='_compute_patient_display_name', store=True)
    type_paid = fields.Selection([
        ('ESPECE', 'ESPECE'),
        ('VIREMENT', 'VIREMENT'),
        ('CHEQUE', 'CHEQUE'),
        ('M-VOLA', 'M-VOLA'),
        ('ORANGE MONEY', 'ORANGE MONEY'),
      #  ('MOBILE MONEY', 'MOBILE MONEY'),
        ('TPE', 'TPE'),
    ], string='Mode de paiement')

    @api.depends('amount_total')
    def _compute_amount_words(self):
        for invoice in self:
            invoice.amount_insurance_words = invoice.currency_id.amount_to_text(invoice.amount_insurance)
            invoice.amount_patient_words = invoice.currency_id.amount_to_text(invoice.amount_patient)

    def is_miscellaneous_customer(self):
        return 'pay' in self.description_fact.lower()

    def print_invoice_report(self):
        if self.company_id:
            template = self.company_id.account_report_template_id.xml_id
            return self.env.ref(template).report_action(self)

    @api.depends('partner_id', 'invoice_source_email', 'partner_id.name')
    def _compute_patient_display_name(self):
        for invoice in self:
            invoice.patient_display_name = invoice.patient_id.name

    @api.model
    def get_name_length(self):
        return len(self.patient_display_name)

    @api.model
    def get_partner_name_length(self):
        return len(self.invoice_partner_display_name)

    def remove_before_space(self, name):
        if name.startswith("DR "):
            return name[3:]
        if name.startswith("PR "):
            return name[3:]
        return name

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    qty_to_split = fields.Float(string='Split Qty')
    price_to_split = fields.Float(string='Split Price')
    copied_line_id = fields.Many2one('account.move.line', 'Copied Invoice Line')
    # ===POUR FACTURE ASSURANCE ===
    price_subtotal_before_split = fields.Monetary(string='Subtotal avant', store=True,
                                                  currency_field='currency_id')
    price_unit_before_split = fields.Float(string='Unit Price', digits='Product Price')

    def copy_data(self, default=None):
        if default is None:
            default = {}
        if self.env.context.get('from_split_invoice'):
            default['copied_line_id'] = self.id
        return super(AccountMoveLine, self).copy_data(default)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountMoveLine, self).create(vals_list)
        for line in res:
            if "sale" in loaded_modules and line.copied_line_id:
                sale_lines = self.env['sale.order.line'].search([('invoice_lines','in',line.copied_line_id.id)])
                for order_line in sale_lines:
                    order_line.with_context(check_move_validity=False).invoice_lines = [(4,line.id)]
        return res
