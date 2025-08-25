# custom_fcm_notifications/models/res_users.py
from odoo import fields, models

class ResUsers(models.Model):
    _inherit = 'res.users'

    fcm_token = fields.Char(string='FCM Token')