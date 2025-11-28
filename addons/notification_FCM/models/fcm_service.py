import requests
from odoo import models, api

class FCMService(models.AbstractModel):
    _name = 'fcm.service'
    _description = 'Service to send Firebase Cloud Messaging notifications'

    FCM_URL = "https://fcm.googleapis.com/fcm/send"

    @api.model
    def send_notification(self, token, title, body, data=None):
        server_key = self.env['ir.config_parameter'].sudo().get_param('fcm.server.key')

        if not server_key:
            raise ValueError("FCM server key not set in system parameters")

        headers = {
            'Authorization': f'key={server_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'to': token,
            'notification': {
                'title': title,
                'body': body
            },
            'data': data or {}
        }

        response = requests.post(self.FCM_URL, json=payload, headers=headers)
        return response.json()
