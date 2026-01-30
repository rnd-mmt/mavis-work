# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import date


class MaintenanceContractEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    contract_duration = fields.Float(string='Contract Duration', compute='_compute_contract_duration')
    total_down_time = fields.Float(string='Total Down Time', compute='_compute_total_down_time')
    total_up_time = fields.Float(string='Total Up Time', compute='_compute_total_up_time')
    equipment_percentage_downtime = fields.Float(string='Downtime', compute='_compute_equipment_percentage_downtime')
    equipment_percentage_uptime = fields.Float(string='Uptime', compute='_compute_percentage_uptime')
    is_up = fields.Boolean(string='Is Up', default=True, compute='_compute_is_up')

    contract_ids = fields.Many2many('maintenance.contract', string='Contrats de maintenance')
    last_contract_id = fields.Many2one('maintenance.contract', string='Dernier Contrat') #compute='_compute_last_contract', store=True
    last_contract_is_expired = fields.Boolean(
        string="Contrat Expiré",
        compute='_compute_last_contract_is_expired',
       # store=True
    )

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
        ('RF', 'RF (Radio Fluoroscopy)'),], 
    string="Modalité", default="CT")

    project_id = fields.Many2one('project.project', string="Projet associé", readonly=False)

    @api.model
    def create(self, vals):
        equipment = super(MaintenanceContractEquipment, self).create(vals)
        project = self.env['project.project'].create({
            'name': f"Projet - {equipment.name}",
            'user_id': self.env.user.id,
        })
        equipment.project_id = project.id
        return equipment

    @api.depends('contract_ids', 'contract_ids.date_start', 'contract_ids.date_end')
    def _compute_last_contract(self):
        for equipment in self:
            last_contract = None
            latest_end_date = None
            for contract in equipment.contract_ids:
                if latest_end_date is None or contract.date_end > latest_end_date:
                    latest_end_date = contract.date_end
                    last_contract = contract.id
            equipment.last_contract_id = last_contract

    @api.depends('last_contract_id')
    def _compute_last_contract_is_expired(self):
        for equipment in self:
            if equipment.last_contract_id.state != 'open':
                equipment.last_contract_is_expired = True
            else:
                equipment.last_contract_is_expired = False
    
        
    def _compute_contract_duration(self):
        contract_obj = self.env['maintenance.contract'].search([])
        for record in self:
            contract = contract_obj.search([('equipment_id','=', record.id), ('is_expired', '=', False)], limit=1)
            if contract:
                if contract.date_start and contract.date_end:
                    delta = contract.date_end - contract.date_start
                    hours_delta = delta.total_seconds() / 3600.0
                    record.contract_duration = hours_delta
                else:
                    record.contract_duration = 0.0
            else:
                record.contract_duration = 0.0

    def _compute_total_down_time(self):
        for equipment in self:
            related_requests = self.env['maintenance.request'].search([('equipment_id', '=', equipment.id),('contract_expired', '=', False)])
            equipment.total_down_time = sum(request.down_time for request in related_requests if request.down_time)
    
    
    @api.depends('total_down_time', 'contract_duration')
    def _compute_total_up_time(self):
        for record in self:
            if record.total_down_time:
                record.total_up_time = abs(record.contract_duration - record.total_down_time)
            else:
                # Get the related contract's start date
                contract = self.env['maintenance.contract'].search([('equipment_id', '=', record.id)], limit=1)
                if contract and contract.date_start:
                    # Calculate the up time based on the current date and contract start date
                    delta = date.today() - contract.date_start
                    record.total_up_time = delta.total_seconds() / 3600.0
                else:
                    record.total_up_time = 0.0
    
    

    @api.depends('equipment_percentage_downtime')
    def _compute_percentage_uptime(self):
        for record in self:
                if record.equipment_percentage_downtime:
                    record.equipment_percentage_uptime = abs(100.0 - record.equipment_percentage_downtime)
                else:
                    # Get the related contract's start date
                    contract = self.env['maintenance.contract'].search([('equipment_id', '=', record.id)], limit=1)
                    if contract and contract.date_start:
                        # Calculate the duration since the contract's start date in hours
                        uptime_duration_days = (date.today() - contract.date_start).days
                        uptime_duration_hours = uptime_duration_days * 24  # Convert days to hours

                        # Ensure contract_duration is non-zero to avoid division by zero
                        if record.contract_duration > 0:
                            # Calculate uptime percentage based on contract duration
                            record.equipment_percentage_uptime = (uptime_duration_hours / record.contract_duration) * 100
                        else:
                            record.equipment_percentage_uptime = 0.0
                    else:
                        record.equipment_percentage_uptime = 0.0
                        
                # Ensure the uptime percentage does not exceed 100%
                if record.equipment_percentage_uptime > 100.0:
                    record.equipment_percentage_uptime = 100.0


    @api.model
    def _compute_is_up(self):
        equipments = self.search([])
        for equipment in equipments:
            maintenance_requests = self.env['maintenance.request'].search([('equipment_id', '=', equipment.id)])
            task_timers = []
            for request in maintenance_requests:
                tasks = self.env['project.task'].search([('maintenance_request_id', '=', request.id)])
                task_timers.extend(task.task_timer for task in tasks)
            if task_timers:
                if any(task_timers):
                    equipment.is_up = False
                else:
                    equipment.is_up = True
            else:
                equipment.is_up = True


    @api.depends('contract_duration', 'total_down_time')
    def _compute_equipment_percentage_downtime(self):
        a = float(self.total_down_time)
        b = float(self.contract_duration)
        if b != 0.0:
            self.equipment_percentage_downtime = "{:.2f}".format((a / b) * 100)
        else:
            self.equipment_percentage_downtime = 0.0
                        
    def action_open_linked_contract(self):
        self.ensure_one()
        contract = self.env['maintenance.contract'].search([('equipment_id', '=', self.id)], limit=1)
        if contract:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Maintenance Contract',
                'view_mode': 'form',
                'res_model': 'maintenance.contract',
                'res_id': contract.id,
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Maintenance Contract',
                'view_mode': 'form',
                'res_model': 'maintenance.contract',
                'target': 'current',
                'context': {
                    'default_equipment_id': self.id,
                }
            }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: