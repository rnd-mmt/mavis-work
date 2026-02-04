# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import SUPERUSER_ID, tools
from odoo.http import request, route
from odoo.addons.bus.controllers.main import BusController
from .mail_activity_helper import MailActivityHelper

_logger = logging.getLogger(__name__)

class MailChatController(BusController):

    def _default_request_uid(self):
        """ For Anonymous people, they receive the access right of SUPERUSER_ID since they have NO access (auth=none)
            !!! Each time a method from this controller is call, there is a check if the user (who can be anonymous and Sudo access)
            can access to the resource.
        """
        return request.session.uid and request.session.uid or SUPERUSER_ID

    # --------------------------
    # Extends BUS Controller Poll
    # --------------------------
    def _poll(self, dbname, channels, last, options):
        if request.session.uid:
            partner_id = request.env.user.partner_id.id

            if partner_id:
                channels = list(channels)       # do not alter original list
                for mail_channel in request.env['mail.channel'].search([('channel_partner_ids', 'in', [partner_id])]):
                    channels.append((request.db, 'mail.channel', mail_channel.id))
                # personal and needaction channel
                channels.append((request.db, 'res.partner', partner_id))
                channels.append((request.db, 'ir.needaction', partner_id))
        return super(MailChatController, self)._poll(dbname, channels, last, options)

    # --------------------------
    # Anonymous routes (Common Methods)
    # --------------------------
    @route('/mail/chat_post', type="json", auth="public", cors="*")
    def mail_chat_post(self, uuid, message_content, **kwargs):
        mail_channel = request.env["mail.channel"].sudo().search([('uuid', '=', uuid)], limit=1)
        if not mail_channel:
            return False

        # find the author from the user session
        if request.session.uid:
            author = request.env['res.users'].sudo().browse(request.session.uid).partner_id
            author_id = author.id
            email_from = author.email_formatted
        else:  # If Public User, use catchall email from company
            author_id = False
            email_from = mail_channel.anonymous_name or mail_channel.create_uid.company_id.catchall_formatted
        # post a message without adding followers to the channel. email_from=False avoid to get author from email data
        body = tools.plaintext2html(message_content)
        message = mail_channel.with_context(mail_create_nosubscribe=True).message_post(author_id=author_id,email_from=email_from, body=body,message_type='comment',subtype_xmlid='mail.mt_comment')
        return message and message.id or False
    
    @route(['/mail/chat_history'], type='json', auth='public', cors='*')
    def mail_chat_history(self, uuid, last_id=False, limit=20):
        """
        Récupère l'historique des messages pour un chat, un canal ou une notification.
        :param uuid: UUID du canal (chat/channel) ou groupe de notifications (ex: group_sale.order)
        :param last_id: ID du dernier message chargé pour pagination
        :param limit: Nombre maximum de messages à récupérer
        :return: Liste de messages formatés
        """
        formatted_messages = []

        channel = request.env['mail.channel'].sudo().search([('uuid', '=', uuid)], limit=1)
        if channel:
            messages = channel.channel_fetch_message(last_id, limit)
            message_ids = [m['id'] for m in messages]
            attachments = request.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'mail.message'),
                ('res_id', 'in', message_ids)
            ])
            attachment_map = {}
            for att in attachments:
                attachment_map.setdefault(att.res_id, []).append({
                    'name': att.name,
                    'mimetype': att.mimetype,
                    'url': f"/web/content/{att.id}?download=true"
                })
            for m in messages:
                m['attachments'] = attachment_map.get(m['id'], [])
            return messages

        # ★★★ 2. Gérer les ACTIVITÉS si l'uuid commence par 'activity_' ★★★
        if uuid.startswith('activity_'):
            return self._get_activity_history(uuid, last_id, limit)

        # Gérer les notifications si l'uuid commence par 'group_'
        if uuid.startswith('group_'):
            model = uuid.replace('group_', '')
            if not model:
                return []

            # Domaine pour les notifications automatisées
            domain = [
                ('message_type', 'in', ['user_notification', 'notification']),
                ('model', '=', model),
                ('author_id', '=', request.env.ref('base.user_root').id)  # OdooBot
            ]
            if last_id:
                domain.append(('id', '<', last_id))

            messages = request.env['mail.message'].sudo().search(
                domain, order='date desc', limit=limit
            )
            
            # Récupérer les pièces jointes
            message_ids = [msg.id for msg in messages]
            _logger.warning('TTT ---1------ %s', message_ids)
            attachments = request.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'mail.message'),
                ('res_id', 'in', message_ids)
            ])
            
            _logger.warning('TTT --2------- %s', attachments)
            attachment_map = {}
            for att in attachments:
                attachment_map.setdefault(att.res_id, []).append({
                    'name': att.name,
                    'mimetype': att.mimetype,
                    'url': f"/web/content/{att.id}?download=true"
                })

            # Formatter les messages
            for msg in messages:
                formatted_messages.append({
                    'id': msg.id,
                    'body': msg.body or '',
                    'date': msg.date or '',
                    'author': msg.author_id.name or 'System',
                    'author_id': msg.author_id.id if msg.author_id else 0,
                    'model': msg.model or '',
                    'res_id': msg.res_id or 0,
                    'url': f"{request.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={msg.res_id}&model={msg.model}&view_type=form" if msg.res_id else '',
                    'message_type': msg.message_type,
                    'attachments': attachment_map.get(msg.id, [])
                })
                _logger.warning('Message: ID=%s, Model=%s, Res_id=%s', msg.id, msg.model, msg.res_id)
        return formatted_messages

    def _get_activity_history(self, uuid, last_id=False, limit=20):
        """
        Récupère l'historique des activités
        """
        formatted_activities = []
        
        # Extraire le type d'activité de l'UUID
        # Format: "activity_all" ou "activity_À faire" ou "activity_123"
        activity_part = uuid.replace('activity_', '')
        
        # Domaine de base
        domain = [
            ('user_id', '=', request.env.user.id),
            ('date_deadline', '!=', False)
        ]
        
        # Filtrer par type si spécifié
        if activity_part != 'all' and not activity_part.isdigit():
            # C'est un type spécifique: "activity_À faire", "activity_Appeler", etc.
            domain.append(('activity_type_id.name', '=', activity_part))
        
        # Pagination
        if last_id:
            domain.append(('id', '<', last_id))
        
        # Récupérer les activités
        activities = request.env['mail.activity'].sudo().search(
            domain, 
            order='date_deadline asc',  # Les plus urgentes en premier
            limit=limit
        )
        
        # Formater comme des messages
        for activity in activities:
            # Construire le texte d'affichage
            display_name = self._get_activity_display_name(activity.activity_type_id.name)
    
            # Exemple 
            info = MailActivityHelper.get_activity_type_info(activity.activity_type_id.name)
            icon = info['icon']
            # color = info['color']
            # display_name = info['display_name']

            # icon = self._get_activity_icon(activity.activity_type_id.name)
            activity_type = activity.activity_type_id.name or "Activité"
            res_name = activity.res_name or ""

            # Construire l'URL vers l'enregistrement
            url = ""
            if activity.res_model and activity.res_id:
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                url = f"{base_url}/web#id={activity.res_id}&model={activity.res_model}&view_type=form"

            # Texte HTML enrichi
            activity_text = f"""
                <i class="fa {icon}"></i> <b>{activity_type}</b> {res_name} • Échéance: {activity.date_deadline} 
                <a href="{url}" target="_blank">Voir le détail</a>
                """
            
            # Formater comme un message
            formatted_activities.append({
                'id': activity.id,
                'body': activity_text,
                'date': activity.date_deadline.isoformat() if activity.date_deadline else '',
                'author': activity.user_id.name,
                'author_id': activity.user_id.id,
                'model': 'mail.activity',
                'res_id': activity.id,
                'url': url,
                'message_type': 'activity',
                'metadata': {
                    'type': activity.activity_type_id.name,
                    'display_name': display_name,
                    'summary': activity.summary or '',
                    'note': activity.note or '',
                    'state': activity.state,
                    'res_model': activity.res_model,
                    'res_id': activity.res_id,
                    'res_name': activity.res_name,
                    'icon': self._get_activity_icon(activity.activity_type_id.name),
                    'color': self._get_activity_color(activity.activity_type_id.name)
                },
                'attachments': []  # Pas de pièces jointes pour les activités
            })
            
        return formatted_activities

    def _get_activity_display_name(self, activity_type):
        """Convertit le type d'activité en nom d'affichage"""
        activity_titles = {
            'À faire': 'Tâches à faire',
            'To Do': 'Tâches à faire',
            'Appeler': 'Appels à faire',
            'Call': 'Appels à faire',
            'Rappel': 'Rappels',
            'Reminder': 'Rappels',
            'Exception': 'Exceptions',
            'Meeting': 'Réunions',
            'Email': 'Emails',
            'Upload Document': 'Documents à uploader',
            'Order Upsell': 'Ventes incitatives',
            'Contract to Renew': 'Contrats à renouveler',
            'Time Off Approval': 'Congés à approuver',
            'Time Off Second Approve': '2ème approbation congés',
            'Allocation Approval': 'Allocations à approuver',
            'Allocation Second Approve': '2ème approbation allocations',
            'Maintenance Request': 'Demandes maintenance',
            'Expense Approval': 'Frais à approuver',
            'Session open over 7 days': 'Sessions ouvertes > 7 jours',
            'Alert Date Reached': 'Dates d\'alerte atteintes',
            'Notification': 'Notifications',
        }
        return activity_titles.get(activity_type, activity_type)

    def _get_activity_icon(self, activity_type):
        """Retourne l'emoji pour le type d'activité"""
        icon_map = {
            'À faire': '✅', 'To Do': '✅',
            'Appeler': '📞', 'Call': '📞',
            'Rappel': '🔔', 'Reminder': '🔔',
            'Exception': '⚠️', 'Meeting': '👥',
            'Email': '📧', 'Upload Document': '📎',
            'Order Upsell': '📈', 'Contract to Renew': '📄',
            'Time Off Approval': '🏖️', 'Time Off Second Approve': '🏖️',
            'Allocation Approval': '⏰', 'Allocation Second Approve': '⏰',
            'Maintenance Request': '🔧', 'Expense Approval': '💰',
            'Session open over 7 days': '⏳', 'Alert Date Reached': '🚨',
            'Notification': '🔔',
        }
        return icon_map.get(activity_type, '🔔')

    def _get_activity_color(self, activity_type):
        """Retourne la couleur pour le type d'activité"""
        color_map = {
            'À faire': '#4CAF50', 'To Do': '#4CAF50',
            'Appeler': '#2196F3', 'Call': '#2196F3',
            'Rappel': '#FF9800', 'Reminder': '#FF9800',
            'Exception': '#F44336', 'Meeting': '#9C27B0',
            'Email': '#00BCD4', 'Upload Document': '#607D8B',
            'Order Upsell': '#FF5722', 'Contract to Renew': '#795548',
            'Time Off Approval': '#009688', 'Time Off Second Approve': '#009688',
            'Allocation Approval': '#3F51B5', 'Allocation Second Approve': '#3F51B5',
            'Maintenance Request': '#8BC34A', 'Expense Approval': '#673AB7',
            'Session open over 7 days': '#FFC107', 'Alert Date Reached': '#E91E63',
            'Notification': '#9E9E9E',
        }
        return color_map.get(activity_type, '#9E9E9E')
