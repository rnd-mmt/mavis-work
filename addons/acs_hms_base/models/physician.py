# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PhysicianSpecialty(models.Model):
    _name = 'physician.specialty'
    _description = "Physician Specialty"

    code = fields.Char(string='Code')
    name = fields.Char(string='Specialty', required=True, translate=True)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Name must be unique!'),
    ]


class PhysicianDegree(models.Model):
    _name = 'physician.degree'
    _description = "Physician Degree"

    name = fields.Char(string='Degree')

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Name must be unique!'),
    ]


class Physician(models.Model):
    _name = 'hms.physician'
    _description = "Physician"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # _inherits = {'res.users': 'user_id'}
    _inherits = {
        'res.partner': 'partner_id',
    }

    # name = fields.Char(string='Nom du médecin', tracking=True)
    partner_id = fields.Many2one('res.partner', required=True, ondelete='restrict', auto_join=True,
                                 string='Related Partner', help='Partner-related data of the Patient', tracking=True)
    user_id = fields.Many2one('res.users',string='Related User', required=False,
         ondelete='cascade', help='User-related data of the physician')
    code = fields.Char(string='Physician Code', default='/', tracking=True)
    degree_ids = fields.Many2many('physician.degree', 'physician_rel_education', 'physician_ids','degree_ids', string='Degree')
    specialty_id = fields.Many2one('physician.specialty', ondelete='set null', string='Specialty', help='Specialty Code', tracking=True)
    medical_license = fields.Char(string='Medical License', tracking=True)
    medecin_smi = fields.Boolean(string='Médecin SMI', default=False, tracking=True)
    biologiste = fields.Boolean(string='Biologiste consortium', default=False, tracking=True)
    id_employee = fields.Char(string='Biometric ID', tracking=True)

    @api.model
    def create(self, values):
        if values.get('code','/') == '/':
            values['code'] = self.env['ir.sequence'].next_by_code('hms.physician')
        # if values.get('email'):
        #     values['login'] = values['email']
        return super(Physician, self).create(values)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: