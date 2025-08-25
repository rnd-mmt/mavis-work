# custom_fcm_notifications/models/mail_message.py
from odoo import models
import requests
import html

class MailMessage(models.Model):
    _inherit = 'mail.message'

    def create(self, vals):  # sourcery skip: use-named-expression
        res = super(MailMessage, self).create(vals)
        if vals.get('model') in ('mail.channel', 'res.partner') or vals.get('message_type') in ('notification', 'comment'):
            channel = None
            partner_ids = []
            if vals.get('model') == 'mail.channel':
                channel = self.env['mail.channel'].browse(vals.get('res_id'))
            elif vals.get('model') == 'res.partner':
                partner_ids = vals.get('partner_ids', [])
            else:
                return res

            users_to_notify = []
            if channel:
                users_to_notify = self.env['res.users'].search([('partner_id', 'in', channel.channel_partner_ids.ids)])
            elif partner_ids:
                users_to_notify = self.env['res.users'].search([('partner_id', 'in', partner_ids)])

            for user in users_to_notify:
                fcm_token = user.fcm_token
                if fcm_token:
                    body = html.unescape(vals.get('body', '')[:1000]).replace('<p>', '').replace('</p>', '')
                    notification = {
                        'title': 'Nouveau message' if vals.get('model') == 'mail.channel' else 'Nouvelle notification',
                        'body': body,
                    }
                    requests.post('https://fcm.googleapis.com/fcm/send', json={
                        'to': fcm_token,
                        'notification': {
                            'title': notification['title'],
                            'body': notification['body'],
                        },
                        'data': {
                            'channel_id': str(vals.get('res_id')) if channel else '',
                            'message_type': vals.get('message_type', ''),
                        },
                        'priority': 'high',
                    }, headers={'Authorization': 'key=BAoOoLUwDo8je2N8oNQrDTE9M6yOZyHB7oPp9fFD6WxMIb4jxwOVvdekvPGQESvVAhvtqmiie2lY2O9OIV-uzoU'})
        return res