# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, Warning

class CreateAppointmentWizard(models.TransientModel):
    _name = 'create.appointment.wizard'
    _description = "Create Appointment"

    physician_id = fields.Many2one('hms.physician', ondelete='restrict', string='Physician', index=True, help='Physician\'s Name')
    urgency = fields.Selection([
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('medical_emergency', 'Medical Emergency'),
    ], string='Urgency Level', default='normal')
    date = fields.Datetime(string='Date', default=fields.Datetime.now, tracking=True, copy=False)

    def create_appointment(self):
        active_id = self._context.get('active_id')
        helpdesk_support = self.env['helpdesk.support'].browse(active_id)
        appointment_obj = self.env['hms.appointment']

        vals = {
            'patient_id': helpdesk_support.patient_id.id,
            'urgency': self.urgency,
            'physician_id': self.physician_id.id,
            'helpdesk_support_id': helpdesk_support.id
        }
        create_rdv = appointment_obj.sudo().create(vals)
        action = self.env.ref('acs_hms.action_appointment')
        result = action.read()[0]
        result['domain'] = [('id', '=', create_rdv.id)]
        return result



