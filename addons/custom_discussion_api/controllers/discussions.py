from odoo import http
from odoo.http import request

import logging

_logger = logging.getLogger(__name__)

class Discussions(http.Controller):

    @http.route('/my/discussions', type='json', auth='public', csrf=False)
    def get_combined_discussions(self):
        _logger.warning('Route /my/discussions appelée !')
        # 1. Récupération des canaux
        channel_slots = request.env['mail.channel'].channel_fetch_slot()
        canaux_list = []
        for slot in channel_slots.values():
            canaux_list.extend(slot)

        # 2. Dernier message pour chaque canal
        canaux_with_last_message = []
        for canal in canaux_list:
            history = request.env['mail.channel'].channel_fetch_message(canal['id'], limit=1)
            last_message = history[0] if history else None
            canaux_with_last_message.append({
                **canal,
                'type': 'canal',
                'last_item_date': last_message['date'] if last_message else canal.get('create_date'),
                'last_message': last_message
            })

        # 3. Notifications
        notifications = request.env['mail.message'].search_read(
            [('message_type', '=', 'notification')],
            fields=['body', 'date', 'author_id', 'model', 'res_id', 'message_type'],
            order='date desc',
            limit=50
        )
        notif_with_details = [
            {**notif, 'type': 'notification', 'last_item_date': notif['date']}
            for notif in notifications
        ]

        # 4. Fusion + tri
        all_items = canaux_with_last_message + notif_with_details
        all_items.sort(key=lambda x: x['last_item_date'], reverse=True)

        return all_items
