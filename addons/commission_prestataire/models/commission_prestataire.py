# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp

class CoPrestRole(models.Model):
    _name = 'commission.prestataire.role'
    _description = 'Role de la commission prestataire'

    name = fields.Char(string='Nom', required=True)
    description = fields.Text("Description")
    coprest_rule_ids = fields.One2many("commission.prestataire.rule", "role_id", string="Règles de la Commission prestataire")


class CoPrestRule(models.Model):
    _name = 'commission.prestataire.rule'
    _description = 'Règles de la commission prestataire'
    _order = "sequence"

    sequence = fields.Integer(string='Sequence', default=50)
    rule_type = fields.Selection([
        ('role', 'Role'),
        ('user', 'User'),
    ], string='Type de règle', copy=False, default='role', required=True)
    role_id = fields.Many2one('commission.prestataire.role', string='Role')
    user_id = fields.Many2one('res.users', string='User')
    partner_id = fields.Many2one('res.partner', string='Partenaire')
    physician_id = fields.Many2one('res.partner', string='Médecin')
    rule_on = fields.Selection([
        ('product_category', 'Catégorie de produit'),
        ('product', 'Produit'),
    ], string='Règle sur', copy=False, default='product_category', required=True)
    product_category_id = fields.Many2one('product.category', string='Product Category')
    product_id = fields.Many2one('product.template', string='Product')
    percentage = fields.Float('Commission en pourcentage')
    #=====HARNEETPROD======
    part_prest = fields.Float('Rémunération prestataire')
    get_number = fields.Boolean('Nb par acte')
    description = fields.Text("Description")


class CommissionPrestataire(models.Model):
    _name = 'commission.prestataire'
    _description = 'Commission Prestataire'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _payment_status(self):
        for rec in self:
            if not rec.payment_invoice_id:
                rec.payment_status = 'not_inv'
            elif rec.payment_invoice_id.state=='draft':
                rec.payment_status = 'draft'
            elif rec.payment_invoice_id.state=='cancel':
                rec.payment_status = 'cancel'
            elif rec.payment_invoice_id.payment_state=='paid':
                rec.payment_status = 'paid'
            else:
                rec.payment_status = 'open'

    def _service_status(self):
        for rec in self:
            if not rec.invoice_id:
                rec.service_state = 'not_paid'
                self.state = 'draft'
            elif rec.invoice_id.payment_state=='not_paid':
                rec.service_state = 'not_paid'
                self.state = 'draft'
            elif rec.invoice_id.payment_state=='in_payment':
                rec.service_state = 'in_payment'
                self.state = 'draft'
            elif rec.invoice_id.payment_state=='paid':
                rec.service_state = 'paid'
                self.state = 'serv_paid'
            elif rec.invoice_id.payment_state=='partial':
                rec.service_state = 'partial'
                self.state = 'draft'
            elif rec.invoice_id.payment_state=='reversed':
                rec.service_state = 'reversed'
                self.state = 'draft'
            elif rec.invoice_id.payment_state=='invoicing_legacy':
                rec.service_state = 'invoicing_legacy'
                self.state = 'draft'
            else:
                rec.service_state = 'not_paid'
                self.state = 'draft'

    STATES = {'done': [('readonly', True)], 'cancel': [('readonly', True)]}

    name = fields.Char(string='Nom',readonly=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('serv_paid', 'Service payé'),
        ('done', 'Done'),
        ('cancel', 'Canceled'),
    ], string='Status', copy=False, default='draft', tracking=True, states=STATES)
    partner_id = fields.Many2one('res.partner', 'Prestataire', required=True, states=STATES, tracking=True)
    invoice_id = fields.Many2one('account.move', 'Facture', states=STATES, copy=False)
    coprest_on = fields.Float('Commission prestataire sur', states=STATES)
    coprest_amount = fields.Float('Montant de la commission', states=STATES)
    invoice_line_id = fields.Many2one('account.move.line', 'Ligne de facture', states=STATES)
    payment_invoice_id = fields.Many2one('account.move', related="invoice_line_id.move_id", string='Paiement facture prestataire', readonly=True)
    payment_status = fields.Selection([
        ('not_inv', 'Non payé'),
        ('draft', 'Brouillon'),
        ('open', 'En cours'),
        ('paid', 'Payé'),
        ('cancel', 'Annulé'), 
    ], string='Status facture prestataire', copy=False, default='not_inv', readonly=True, compute="_payment_status")
    service_state = fields.Selection(selection=[
        ('not_paid', 'Non payé'),
        ('in_payment', 'En cours'),
        ('paid', 'Payé'),
        ('partial', 'Partiellement payé'),
        ('reversed', 'Annulé'),
        ('invoicing_legacy', 'Invoicing App Legacy')],
        string="Status facture patient", readonly=True, copy=False,
        compute='_service_status')
    note = fields.Text("Note")
    coprest_sheet_id = fields.Many2one('commission.prestataire.sheet', 'Feuille commission prestataire', states=STATES)
    company_id = fields.Many2one('res.company', related="invoice_id.company_id", string='Hopital', store=True)

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise UserError(_("Vous ne pouvez pas supprimer un enregistrement qui n'est ni brouillon ni annulé."))
        return super(CommissionPrestataire, self).unlink()

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('commission.prestataire')
        return super(CommissionPrestataire, self).create(values)

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_draft(self):
        self.state = 'draft'

    def action_cancel(self):
        self.state = 'cancel'
