# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Hospitalization(models.Model):
    _inherit = "acs.hospitalization"

    def _rec_count(self):
        rec = super(Hospitalization, self)._rec_count()
        for rec in self:
            rec.request_count = len(rec.img_request_ids)
            rec.test_count = len(rec.img_test_ids)

    img_request_ids = fields.One2many('acs.imaging.request', 'hospitalization_id', string='Imaging Requests')
    img_test_ids = fields.One2many('patient.imaging.test', 'hospitalization_id', string='Tests')
    request_count = fields.Integer(compute='_rec_count', string='# Imaging Requests')
    test_count = fields.Integer(compute='_rec_count', string='# Imaging Tests')

    def action_imaging_request(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.hms_action_imaging_test_request")
        action['domain'] = [('id','in',self.img_request_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_hospitalization_id': self.id}
        action['views'] = [(self.env.ref('acs_imaging.patient_imaging_test_request_form').id, 'form')]
        return action

    def action_imaging_requests(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.hms_action_imaging_test_request")
        action['domain'] = [('id','in',self.img_request_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_hospitalization_id': self.id}
        return action

    def action_view_test_results(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.action_imaging_result")
        action['domain'] = [('id','in',self.img_test_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_hospitalization_id': self.id}
        return action


class ACSAppointment(models.Model):
    _inherit='hms.appointment'

    def _rec_count(self):
        for rec in self:
            rec.request_count = len(rec.imaging_request_ids)
            rec.test_count = len(rec.img_test_ids)

    img_test_ids = fields.One2many('patient.imaging.test', 'appointment_id', string='Imaging Tests')
    imaging_request_ids = fields.One2many('acs.imaging.request', 'appointment_id', string='Imaging Requests')
    request_count = fields.Integer(compute='_rec_count', string='# Imaging Requests')
    test_count = fields.Integer(compute='_rec_count', string='# Imaging Tests')

    def action_imaging_request(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.hms_action_imaging_test_request")
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_physician_id': self.physician_id.id, 'default_appointment_id': self.id}
        action['views'] = [(self.env.ref('acs_imaging.patient_imaging_test_request_form').id, 'form')]
        return action

    def action_view_test_results(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.action_imaging_result")
        action['domain'] = [('id','in',self.img_test_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_physician_id': self.physician_id.id, 'default_appointment_id': self.id}
        return action

    def action_view_imaging_request(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.hms_action_imaging_test_request")
        action['domain'] = [('id','in',self.imaging_request_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_physician_id': self.physician_id.id, 'default_appointment_id': self.id}
        return action


class Treatment(models.Model):
    _inherit = "hms.treatment"

    def _img_rec_count(self):
        for rec in self:
            rec.request_count = len(rec.img_request_ids)
            rec.test_count = len(rec.img_test_ids)

    img_request_ids = fields.One2many('acs.imaging.request', 'treatment_id', string='Imaging Requests')
    img_test_ids = fields.One2many('patient.imaging.test', 'treatment_id', string='Tests')
    request_count = fields.Integer(compute='_img_rec_count', string='# Imaging Requests')
    test_count = fields.Integer(compute='_img_rec_count', string='# Imaging Tests')

    def action_imaging_request(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.hms_action_imaging_test_request")
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_treatment_id': self.id}
        action['views'] = [(self.env.ref('acs_imaging.patient_imaging_test_request_form').id, 'form')]
        return action

    def action_imaging_requests(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.hms_action_imaging_test_request")
        action['domain'] = [('id','in',self.img_request_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_treatment_id': self.id}
        return action

    def action_view_test_results(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.action_imaging_result")
        action['domain'] = [('id','in',self.img_test_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_treatment_id': self.id}
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: