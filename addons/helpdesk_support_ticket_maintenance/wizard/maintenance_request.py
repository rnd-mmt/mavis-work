# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, Warning

class MaintenanceRequestWizard(models.TransientModel):
    _name = 'maintenance.request.wizard'


    user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        required=True,
    )
    maintenance_team_id = fields.Many2one(
        'maintenance.team',
        string='Maintenance Team',
        required=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        default=lambda self: self.env['hr.employee'].search
        ([('user_id', '=', self.env.uid)], limit=1),
        required=True,
    )
    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Equipment',
    )

    # @api.multi #odoo13
    def create_maintenance_request(self):
        active_id = self._context.get('active_id')
        helpdesk_support = self.env['helpdesk.support'].browse(active_id)
        maintenance_obj = self.env['maintenance.request']
        if not helpdesk_support.subject:
            raise Warning(_('Please enter subject of ticket.'))
        vals = {
            'name': helpdesk_support.subject,
            # 'technician_user_id': self.user_id.id, #odoo13
            'user_id': self.user_id.id,
            'maintenance_team_id': self.maintenance_team_id.id,
            'employee_id': self.employee_id.id,
            'equipment_id': self.equipment_id.id,
            'description': helpdesk_support.description,
            'helpdesk_support_id': helpdesk_support.id
        }
        maintenance_request = maintenance_obj.sudo().create(vals)
        helpdesk_support.maintenance_id = maintenance_request.id

        maintenance_request_material_obj = self.env['maintenance.request.material']
        maintenance_equipment_obj = self.env['maintenance.equipment.checklist']

        for material in self.equipment_id.material_ids:
            material_vals = {
                 'product_id': material.product_id.id,
                 'quantity': material.quantity,
                 'description': material.product_id.name,
                 'uom_id': material.uom_id.id,
            }
            maintenance_request_material_obj.sudo().create(material_vals)

        for checklist in self.equipment_id.equipment_checklist_ids:
            checklist_vals = {
                 'name': checklist.name,
                 'note': checklist.note,
            }
            maintenance_equipment_obj.sudo().create(checklist_vals)

        action = self.env.ref('maintenance.hr_equipment_request_action')
        result = action.read()[0]
        result['domain'] = [('id', '=', maintenance_request.id)]
        return result
