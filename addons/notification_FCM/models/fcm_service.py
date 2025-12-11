import json
import requests
from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)
class FCMService(models.AbstractModel):
    _name = 'fcm.service'
    _description = 'Service to send Firebase Cloud Messaging notifications'

    FCM_URL = "https://fcm.googleapis.com/fcm/send"

    @api.model
    def send_notification(self, token, title, body, data=None):
        _logger.info("---- Envoi notification FCM ----")
        server_key = self.env['ir.config_parameter'].sudo().get_param('fcm.server.key')
        _logger.info(f"Server key found: {'Yes' if server_key else 'No'}")
        _logger.info(f"Token: {token}")
        
        if not server_key:
            _logger.error("server key not found")
            return {"success": False, "error": "Clé FCM manquante"}
        token_test = "dQ2EANG0QT-AOxYNpgGz8G:APA91bG0ixlC6jqyMDL2UKxJAtTexKYFvsSWKIBNNPSy1YCBzF7yXVYcuRCQP8wRclljQwSRIMIPYOsfIWcNJXkEXF052hT-KAFyI25KWBxRMLhawedK_kQ"
        server_key_test = "AIzaSyCgipeBUtz-0awhcu9GnJRm1qVNXPXyNdk"
    
        notification_payload = {
            'to': token_test,
            'notification': {
                'title': title, 
                'body': body,   
                'sound': 'default'
            },
            'data': data or {},
            'priority': 'high'
        }
        
        _logger.info(f"Payload FCM: {json.dumps(notification_payload, indent=2)}")

        try:
            headers = {
                'Authorization': f'key={server_key_test}',
                'Content-Type': 'application/json'
            }
            _logger.info(f"Headers: {headers}")
            response = requests.post(self.FCM_URL, json=notification_payload, headers=headers, timeout=10)
            _logger.info(f"📥 Réponse HTTP: {response.status_code}")
            _logger.info(f"📥 Corps réponse: {response.text}")
            
            if response.status_code == 200:
                if response.text.strip():
                    return response.json()
                else:
                    _logger.warning("⚠️ Réponse FCM vide")
                    return {"success": False, "error": "Réponse vide"}
            else:
                _logger.error(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            _logger.error(f"💥 Exception FCM: {str(e)}")
            return {"success": False, "error": str(e)}

    @api.model
    def send_notification_to_users(self, user_ids, title, body, data=None):
        """ENVOYER DIRECTEMENT AUX USERS - Méthode principale"""
        _logger.info(f"----------------Envoi notification FCM aux utilisateurs: {user_ids}")
        _logger.info(f"Title: {title}")
        _logger.info(f"Body: {body}")
        _logger.info(f"Data: {data}")
        
        if not user_ids:
            return []
        
        results = []
        
        for user_id in user_ids:
            user = self.env['res.users'].browse(user_id)
            if not user.exists():
                continue
                
            # Chercher les devices MOBILE de cet utilisateur
            devices = self.env['mobile.device'].search([
                ('user_id', '=', user.id),
                ('logged_in', '=', True),
                ('fcm_token', '!=', False)
            ])
            _logger.info(f"User {user.login} has {len(devices)} registered devices for FCM.")
            
            for device in devices:
                _logger.info(f"Sending FCM to user {user.login}, device {device.device_name} with token {device.fcm_token[:30]}...")
                # Log détaillé du device
                _logger.info(f"📱 Device details for {user.login}:")
                _logger.info(f"   ID: {device.id}")
                _logger.info(f"   Name: {device.device_name}")
                _logger.info(f"   OS: {device.os}")
                _logger.info(f"   Device ID: {device.device_id}")
                _logger.info(f"   Token: {device.fcm_token}")
                _logger.info(f"   Logged in: {device.logged_in}")
                _logger.info(f"   Last seen: {device.last_seen}")
                
                result = self.send_notification(
                    token=device.fcm_token,
                    title=title,
                    body=body,
                    data=data
                )
                _logger.info(f"FCM send result for user {user.login}, device {device.device_name}: {result}")
                results.append({
                    'user': user.name,
                    'device': device.device_name,
                    'success': result.get('success', False)
                })
        
        return results
    