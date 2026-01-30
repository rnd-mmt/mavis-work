# -*- coding: utf-8 -*-
import re
import pprint

from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

from datetime import datetime
from datetime import date, timedelta

#TODO: Update this function to create the time sheet lines based on the contract's duration and time sheets.'

class MaintenanceContract(models.Model):
    _name = 'maintenance.contract'
    _description = 'maintenance_contract.maintenance_contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom', readonly=True, required=True, copy=False, default='New')
    active = fields.Boolean(default=True)
    analytic_account = fields.Many2one('account.analytic.account', company_dependent=True, string='Compte analytique',
                                       domain=lambda self: [("company_id", "=", self.env.company.id)],
                                       help="Compte analytique", store=True)
    company_id = fields.Many2one('res.company', string='Société', store=True, default=lambda self: self.env.company, required=True)
    date_start = fields.Date(string='Date de début de contrat',  required=True)
    date_end = fields.Date(string='Date de fin de contrat', required=True)
    department_id = fields.Many2one('hr.department', store=True, readonly=False, string="Départment")
    description = fields.Text(string='Description')
    equipment_id = fields.Many2one(comodel_name='maintenance.equipment', string="Equipement", copy=False, required=True)
    first_contract_date = fields.Date(string='Première date de contrat')
    state = fields.Selection([
        ('draft', 'Nouveau'),
        ('open', 'En cours'),
        ('close', 'Expiré'),
        ('cancel', 'Annulé')
    ], string='Status', group_expand='_group_expand_states', copy=False, tracking=True, help='Status of the contract',
        default='draft')
    system_code = fields.Char(string='Code Système')
    is_running = fields.Boolean(string="Is running", default=True)

    is_expired = fields.Boolean(string="Expiré", readonly=True, default=False, compute="_compute_is_expired") #, compute="_compute_is_expired"

    attachment_count = fields.Integer(string='Attachment Count',compute='_get_attachment_count', store=True)

    attachment_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[('res_model', '=', 'maintenance.contract')],
        string="Attachments"
    )

    contract_type = fields.Selection([
        ('top', 'TOP'),
        ('plus', 'PLUS'),
        ('pro', 'PRO'),
    ], string='Type de contrat', default='top')
    
    @api.depends('date_end')
    def _compute_is_expired(self):
        for record in self:
            if record.date_end :
                record.is_expired = record.date_end < date.today()
                if record.is_expired :
                    record.state = 'close'
                    record.is_running = False
                # else : 
                #     record.state = 'open'
            else:
                record.is_expired = False

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('maintenance.contract') or False
        record = super(MaintenanceContract, self).create(vals)
        return record

    def action_open(self):
        self.state = 'open'
        self.equipment_id.last_contract_id = self.id
        self.is_running = True

    def action_cancel(self):
        self.state = 'cancel'
        self.is_running = False
    
    def reactive_contract(self):
        self.ensure_one()
        default_values = {
            'equipment_id': self.equipment_id.id, 
            'is_expired': False,
            'date_start': date.today(),
            'date_end': date.today() + timedelta(days=365),
            'state': 'open',
        }
        new_active_contract = self.copy(default=default_values)
        if new_active_contract:
            context = dict(self.env.context)
            context['form_view_initial_mode'] = 'edit'

            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'maintenance.contract',
                'res_id': new_active_contract.id,
                'context': context,
            }
        return False
    
    
    @api.depends('attachment_ids')
    def _get_attachment_count(self):
        for contract in self:
            contract.attachment_count = len(contract.attachment_ids)

    @api.onchange('attachment_ids')
    def _onchange_attachment_ids(self):
        for contract in self:
            contract.attachment_count = len(contract.attachment_ids)

    def action_view_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents',
            'view_mode': 'tree,form',
            'res_model': 'ir.attachment',
            'domain': [('res_model', '=', 'maintenance.contract'), ('res_id', '=', self.id)],
            'context': {'default_res_model': 'maintenance.contract', 'default_res_id': self.id}
        }

    def _group_expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]
    
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        args = [('company_id', 'in', self.env.context.get('allowed_company_ids', self.env.company.ids))] + args
        return super().search(args, offset=offset, limit=limit, order=order, count=count)

    
