from odoo import models, fields

class MobileDevice(models.Model):
    _name = 'mobile.device'
    _description = 'Mobile Device registered for push notifications'

    user_id = fields.Many2one('res.users', string='User', required=True)
    fcm_token = fields.Char('FCM Token', required=True)
    device_id = fields.Char('Device Unique ID', required=True)
    device_name = fields.Char('Device Name')
    os = fields.Char('Operating System')
    logged_in = fields.Boolean('Logged In', default=True)
    last_seen = fields.Datetime('Last Seen', default=fields.Datetime.now)
    create_date = fields.Datetime(readonly=True)
    write_date = fields.Datetime(readonly=True)

    _sql_constraints = [
        ('unique_device', 'unique(device_id)', 'This device is already registered!')
    ]
