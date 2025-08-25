# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import SUPERUSER_ID, tools
from odoo.http import request, route
from odoo.addons.bus.controllers.main import BusController

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

    # @route(['/mail/chat_history'], type="json", auth="public", cors="*")
    # def mail_chat_history(self, uuid, last_id=False, limit=20):
    #     channel = request.env["mail.channel"].sudo().search([('uuid', '=', uuid)], limit=1)
    #     if channel:
    #         # Récupérer les messages
    #         messages = channel.channel_fetch_message(last_id, limit)

    #         # Extraire les IDs des messages
    #         message_ids = [m['id'] for m in messages]

    #         # Récupérer toutes les pièces jointes en une seule requête
    #         attachments = request.env['ir.attachment'].sudo().search([
    #             ('res_model', '=', 'mail.message'),
    #             ('res_id', 'in', message_ids)
    #         ])

    #         # Regrouper les attachments par message
    #         attachment_map = {}
    #         for att in attachments:
    #             attachment_map.setdefault(att.res_id, []).append({
    #                 'name': att.name,
    #                 'mimetype': att.mimetype,
    #                 'url': f"/web/content/{att.id}?download=true"
    #             })

    #         # Ajouter les attachments à chaque message
    #         for m in messages:
    #             m['attachments'] = attachment_map.get(m['id'], [])

    #         return messages
    
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
