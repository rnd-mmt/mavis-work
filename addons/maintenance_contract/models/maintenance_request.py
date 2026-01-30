from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError

class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    # down_time = fields.Float('Downtime', compute='_compute_down_time', store=True)
    down_time = fields.Float('Inactivité', store=True, compute='_compute_down_time', digits=(20, 4))
    total_duration = fields.Float('total duration', compute='_compute_total_duration', digits=(20, 4))
    percentage_downtime = fields.Float('Downtime', compute='_compute_percentage_downtime', digits=(20, 4))
    percentage_uptime = fields.Float('Uptime', compute='_compute_percentage_uptime', digits=(20, 4))    

    task_ids = fields.One2many(
        comodel_name='project.task',
        inverse_name='maintenance_request_id',
        string='Tasks'
    )
    
    contract_expired = fields.Boolean('Contract expired', compute='_compute_expired', store=True)

    @api.depends('equipment_id')
    def _compute_expired(self):
        for request in self:
            request.contract_expired = request.equipment_id.last_contract_is_expired


    @api.depends('task_ids.duration')
    def _compute_down_time(self):
        for record in self:
            record.down_time = sum( task.duration for task in record.task_ids if task.duration)

    def _compute_total_duration(self):
        contract_obj = self.env['maintenance.contract'].search([])
        for request in self:
            contract = self.env['maintenance.contract'].search([('equipment_id','=', self.equipment_id.id),('state','=', 'open')])
            # contract = contract_obj.filtered(lambda contract: request.equipment_id.id in contract.equipment_ids.ids)[:1]
            if contract:
                if contract.date_start and contract.date_end:
                    delta = contract.date_end - contract.date_start
                    # request.total_duration = delta.total_seconds() / 3600
                    hours_delta = delta.total_seconds() / 3600.0
                    request.total_duration = hours_delta
            else:
                request.total_duration = 0.0

    @api.depends('total_duration', 'down_time')
    def _compute_percentage_downtime(self):
        a = float(self.down_time)
        b = float(self.total_duration)
        if b != 0.0:
            self.percentage_downtime = "{:.2f}".format((a / b) * 100)
        else : self.percentage_downtime = 0.0

    @api.depends('percentage_downtime')
    def _compute_percentage_uptime(self):
        for record in self:
            record.percentage_uptime = 100.0 - record.percentage_downtime if record.percentage_downtime else 0.0


    def show_related_task(self):
        pass


class ProjectTask(models.Model):
    _inherit = "project.task"

    maintenance_request_id = fields.Many2one(
        'maintenance.request',
        string="Maintenance Request",
        ondelete='set null'
    )




