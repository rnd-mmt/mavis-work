from odoo import models, api

class AutoLogoutConfig(models.Model):
    _name = 'auto_logout.config'
    _description = 'Auto Logout config helper'

    @api.model
    def get_auto_logout_minutes(self):
        return self.env['ir.config_parameter'].sudo().get_param('web.auto_logout_minutes', default='5')
    