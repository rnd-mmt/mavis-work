# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _

class HelpdeskSupport(models.Model):

    _inherit = 'helpdesk.support'

    imaging_modality = fields.Selection([
        ('CT', 'CT (Computed Tomography)'),
        ('MR', 'MR (Magnetic Resonance)'),
        ('US', 'US (Ultrasound)'),
        ('NM', 'NM (Nuclear Medicine)'),
        ('XA', 'XA (X-ray Angiograph)'),
        ('CR', 'CR (Computed Radiography)'),
        ('MG', 'MG (Mammography)'),
        ('DX', 'DX (Digital Radiography)'),
        ('SC', 'SC (Secondary Capture)'),
        ('OT', 'OT (Other)'),
        ('PT', 'PT (Positron Emission Tomography)'),
        ('RF', 'RF (Radio Fluoroscopy)'),
    ], string="Modalité", default='OT')

    equipment_id = fields.Many2one('maintenance.equipment', string='Équipement',
                                    domain="[('imaging_modality', '=', imaging_modality)]",
                                    ondelete='restrict', index=True, check_company=True)
    timesheet_line_ids = fields.One2many('account.analytic.line', compute='_compute_timesheet_lines', store=False, string='Timesheets')

    # @api.onchange('imaging_modality')
    # def _onchange_imaging_modality(self):
    #     self.equipment_id = False
    #     if self.imaging_modality:
    #         return {
    #             'domain': {'equipment_id': [('imaging_modality', '=', self.imaging_modality)]}
    #         }
    #     return {'domain': {'equipment_id': []}}

    
    @api.depends('maintenance_request_ids.task_ids', 'maintenance_request_ids.task_ids.timesheet_ids')
    def _compute_timesheet_lines(self):
        for record in self:
            timesheet_lines = []
            for maintenance_request in record.maintenance_request_ids:
                for task in maintenance_request.task_ids:
                    timesheet_lines.extend(task.timesheet_ids.ids)
            record.timesheet_line_ids = [(6, 0, timesheet_lines)]

    # @api.model
    # def write(self, vals):
    #     res = super(HelpdeskSupport, self).write(vals)
    #     if 'timesheet_line_ids' in vals:
    #         for record in self:
    #             tasks = record.mapped('maintenance_request_ids.task_ids')
    #             for task in tasks:
    #                 task.write({'timesheet_ids': vals.get('timesheet_line_ids')})
    #     return res