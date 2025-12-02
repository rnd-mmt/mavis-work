from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class FCMController(http.Controller):
    
    @http.route('/fcm/register', type='json', auth='user', methods=['POST'])
    def register_device(self, **kw):
        device_id = kw.get('device_id')
        fcm_token = kw.get('fcm_token')
        device_name = kw.get('device_name')
        os = kw.get('os')

        if not device_id or not fcm_token:
            return {"status": "error", "message": "device_id and fcm_token are required"}
        
        try:
            user = request.env.user
            device = request.env['mobile.device'].sudo().search([('device_id', '=', device_id)], limit=1)

            if device:
                device.sudo().write({
                    'user_id': user.id,
                    'fcm_token': fcm_token,
                    'device_name': device_name,
                    'os': os,
                    'logged_in': True,
                    'last_seen': fields.Datetime.now(),
                })
            else:
                request.env['mobile.device'].sudo().create({
                    'device_id': device_id,
                    'user_id': user.id,
                    'fcm_token': fcm_token,
                    'device_name': device_name,
                    'os': os,
                    'logged_in': True,
                })
            return {'status': 'ok', 'message': 'Device registered'}
        except Exception as e:
            _logger.exception("FCM register failed!")  # Affiche la stack trace complète
            _logger.debug(str(e))
            return {'status': 'error', 'message': str(e)}

    @http.route('/fcm/unregister', type='json', auth='user', methods=['POST'])
    def unregister(self, device_id=None, **kw):
        device = request.env['mobile.device'].search([('device_id', '=', device_id)], limit=1)
        if device:
            device.write({
                'logged_in': False,
                # 'fcm_token': False,
            })
        return {"status": "ok"}

    @http.route('/called', type='json', auth='public', csrf=False, methods=['POST'])
    def get_static(self, device_id=None, **kw):
        _logger.warning('------------------ ROUTE -- + JSON called !')
        return {'device_id': device_id}