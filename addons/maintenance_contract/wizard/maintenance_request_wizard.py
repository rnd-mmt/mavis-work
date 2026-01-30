from odoo import models, api, fields, _

class MaintenanceRequestWizard(models.TransientModel):
    _inherit = 'maintenance.request.wizard'

    @api.model
    def default_get(self, fields):
        res = super(MaintenanceRequestWizard, self).default_get(fields)
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        if active_model == 'helpdesk.support' and active_id:
            helpdesk_ticket = self.env[active_model].browse(active_id)    
            if helpdesk_ticket.equipment_id:
                res.update({'equipment_id': helpdesk_ticket.equipment_id.id})
        return res