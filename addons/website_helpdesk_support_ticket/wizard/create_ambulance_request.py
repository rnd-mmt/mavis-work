# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, Warning
from datetime import timedelta, datetime

class AmbulanceRequestWizard(models.TransientModel):
    _name = 'create.ambulance.request.wizard'
    _description = "Create Ambulance Request"

    date = fields.Datetime('Date', default=fields.Datetime.now, required=True)
    date_to = fields.Datetime('Date Till', default=fields.datetime.now() + timedelta(minutes=120), required=True)
    pick_location = fields.Char('Pick Location')
    drop_location = fields.Char('Drop Location')
    user_id = fields.Many2one('res.users', ondelete='restrict', string='Responsible',
                              help="Nurse/User", default=lambda self: self.env.user, required=True,
                              domain=[('share', '=', False)])
    vehicle_id = fields.Many2one('fleet.vehicle', ondelete='restrict', string='Vehicle',
                                 help="Ambulance Vehicle", required=True)
    driver_id = fields.Many2one('res.partner', ondelete='restrict', string='Driver',
                                help="Responsible Person", required=True,
                                domain=[('is_driver','=',True)])
    remark = fields.Text('Remark')

    def action_create_ambulance_request(self):
        active_id = self._context.get('active_id')
        helpdesk_support = self.env['helpdesk.support'].browse(active_id)
        ambulance_obj = self.env['acs.ambulance.service']

        vals = {
            'patient_id': helpdesk_support.patient_id.id,
            'date': self.date,
            'date_to' : self.date_to,
            'pick_location': self.pick_location,
            'drop_location': self.drop_location,
            'user_id': self.user_id.id,
            'vehicle_id': self.vehicle_id.id,
            'driver_id': self.driver_id.id,
            'remark': self.remark,
            'helpdesk_support_id': helpdesk_support.id
        }
        ambulance_request = ambulance_obj.sudo().create(vals)
        action = self.env.ref('acs_hms_ambulance.action_acs_ambulance_service')
        result = action.read()[0]
        result['domain'] = [('id', '=', ambulance_request.id)]
        return result



