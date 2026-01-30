# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp

class CoPrestSheet(models.Model):
    _name = 'commission.prestataire.sheet'
    _description = 'Feuille de commission prestataire'
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

    @api.depends('coprest_line_ids','coprest_line_ids.coprest_amount')
    def _amount_all(self):
        for record in self:
            coprest_amount = 0
            for line in record.coprest_line_ids:
                coprest_amount += line.coprest_amount
            record.amount_total = coprest_amount

    STATES = {'done': [('readonly', True)], 'cancel': [('readonly', True)]}

    name = fields.Char(string='Nom', readonly=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed','Confirmé'),
        ('done', 'Fait'),
    ], string='Status', copy=False, default='draft', tracking=True, states=STATES)
    partner_id = fields.Many2one('res.partner', string='Prestataire', index=True, required=True, states=STATES, tracking=True)
    date_from = fields.Date(states=STATES, required=True, default=fields.Date.today)
    date_to = fields.Date(states=STATES, required=True, default=fields.Date.today)
    user_id = fields.Many2one('res.users', string='Utilisateur', states=STATES, default=lambda self: self.env.user.id, required=True, tracking=True)
    coprest_line_ids = fields.One2many('commission.prestataire', 'coprest_sheet_id',
        string='Ligne de commission', states=STATES)
    payment_invoice_id = fields.Many2one('account.move', string='Paiement facture', readonly=True)
    payment_status = fields.Selection([
        ('not_inv', 'Non payé'),
        ('draft', 'Brouillon'),
        ('open', 'En cours'),
        ('paid', 'Payé'),
        ('cancel', 'Annulé'), 
    ], string='Etat de paiement facture', copy=False, default='not_inv', readonly=True, compute="_payment_status")    
    note = fields.Text("Note")
    company_id = fields.Many2one('res.company', states=STATES,
        string='Société', default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', related="company_id.currency_id",
        string='Devise')
    amount_total = fields.Float(compute="_amount_all", string="Total")

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise UserError(_("Vous ne pouvez pas supprimer un enregistrement qui n'est ni brouillon ni annulé."))
        return super(CoPrestSheet, self).unlink()

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('commission.prestataire.sheet')
        return super(CoPrestSheet, self).create(values)

    def action_done(self):
        self.state = 'done'

    def action_draft(self):
        self.state = 'draft'

    def action_cancel(self):
        self.state = 'cancel'

    def get_data(self):
        self.coprest_line_ids.write({'coprest_sheet_id': False})
        commission_lines = self.env['commission.prestataire'].search([
            ('partner_id','=',self.partner_id.id),
            ('create_date','>=',self.date_from),
            ('create_date','<=',self.date_to),
            ('state','=', 'serv_paid'),
            ('coprest_sheet_id','=',False)])
        commission_lines.write({'coprest_sheet_id': self.id})

    def create_payment_bill(self):
        action = self.env["ir.actions.actions"]._for_xml_id("commission_prestataire.action_view_coprest_invoice")
        action['context'] = {
            'active_model':'commission.prestataire', 
            'active_ids': self.coprest_line_ids.ids, 
            'coprest_sheet_id': self.id,
            'default_hide_groupby_partner': True,
        }
        return action