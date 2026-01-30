# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HelpdeskSupport(models.Model):
    _inherit = 'helpdesk.support'

    maintenance_id = fields.Many2one(
        'maintenance.request',
        string='Maintenance Request',
        readonly=True,
    )
    maintenance_request_count = fields.Integer(
        compute='_compute_maintenance_request_count', 
        string='Maintenance Request Count'
    )
    maintenance_request_ids = fields.One2many(
        'maintenance.request',
        'helpdesk_support_id',
        string='Maintenance Requests'
    )

    # @api.multi #odoo13
    @api.depends('maintenance_request_ids')
    def _compute_maintenance_request_count(self):
        for rec in self:
            rec.maintenance_request_count = len(rec.maintenance_request_ids)

    # @api.multi #odoo13
    def action_view_maintenance_request(self):
        self.ensure_one()
        action = self.env.ref('maintenance.hr_equipment_request_action').read()[0]
        action['domain'] = [('helpdesk_support_id', '=', self.id)]
        return action
        
#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
