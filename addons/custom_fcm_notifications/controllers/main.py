# custom_fcm_notifications/controllers/main.py
from odoo import http
from odoo.http import request

class FCMController(http.Controller):
    @http.route('/api/register_fcm_token', type='json', auth='public', methods=['POST'])
    def register_fcm_token(self, user_id, fcm_token):
        user = request.env['res.users'].sudo().browse(int(user_id))
        if user.exists():
            user.write({'fcm_token': fcm_token})
            return {'status': 'success', 'message': 'Token registered'}
        return {'status': 'error', 'message': 'User not found'}