# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import logging
import psycopg2
import werkzeug.utils
import werkzeug.wrappers

from werkzeug.urls import url_encode

from odoo import api, http, registry, SUPERUSER_ID, _
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools import consteq

_logger = logging.getLogger(__name__)
class MailController(http.Controller):
    _cp_path = '/mail'

    @classmethod
    def _redirect_to_messaging(cls):
        url = '/web#%s' % url_encode({'action': 'mail.action_discuss'})
        return werkzeug.utils.redirect(url)

    @classmethod
    def _check_token(cls, token):
        base_link = request.httprequest.path
        params = dict(request.params)
        params.pop('token', '')
        valid_token = request.env['mail.thread']._notify_encode_link(base_link, params)
        return consteq(valid_token, str(token))

    @classmethod
    def _check_token_and_record_or_redirect(cls, model, res_id, token):
        comparison = cls._check_token(token)
        if not comparison:
            _logger.warning('Invalid token in route %s', request.httprequest.url)
            return comparison, None, cls._redirect_to_messaging()
        try:
            record = request.env[model].browse(res_id).exists()
        except Exception:
            record = None
            redirect = cls._redirect_to_messaging()
        else:
            redirect = cls._redirect_to_record(model, res_id)
        return comparison, record, redirect

    @classmethod
    def _redirect_to_record(cls, model, res_id, access_token=None, **kwargs):
        # access_token and kwargs are used in the portal controller override for the Send by email or Share Link
        # to give access to the record to a recipient that has normally no access.
        uid = request.session.uid
        user = request.env['res.users'].sudo().browse(uid)
        cids = False

        # no model / res_id, meaning no possible record -> redirect to login
        if not model or not res_id or model not in request.env:
            return cls._redirect_to_messaging()

        # find the access action using sudo to have the details about the access link
        RecordModel = request.env[model]
        record_sudo = RecordModel.sudo().browse(res_id).exists()
        if not record_sudo:
            # record does not seem to exist -> redirect to login
            return cls._redirect_to_messaging()

        # the record has a window redirection: check access rights
        if uid is not None:
            if not RecordModel.with_user(uid).check_access_rights('read', raise_exception=False):
                return cls._redirect_to_messaging()
            try:
                # We need here to extend the "allowed_company_ids" to allow a redirection
                # to any record that the user can access, regardless of currently visible
                # records based on the "currently allowed companies".
                cids = request.httprequest.cookies.get('cids', str(user.company_id.id))
                cids = [int(cid) for cid in cids.split(',')]
                try:
                    record_sudo.with_user(uid).with_context(allowed_company_ids=cids).check_access_rule('read')
                except AccessError:
                    # In case the allowed_company_ids from the cookies (i.e. the last user configuration
                    # on his browser) is not sufficient to avoid an ir.rule access error, try to following
                    # heuristic:
                    # - Guess the supposed necessary company to access the record via the method
                    #   _get_mail_redirect_suggested_company
                    #   - If no company, then redirect to the messaging
                    #   - Merge the suggested company with the companies on the cookie
                    # - Make a new access test if it succeeds, redirect to the record. Otherwise, 
                    #   redirect to the messaging.
                    suggested_company = record_sudo._get_mail_redirect_suggested_company()
                    if not suggested_company:
                        raise AccessError('')
                    cids = cids + [suggested_company.id]
                    record_sudo.with_user(uid).with_context(allowed_company_ids=cids).check_access_rule('read')
            except AccessError:
                return cls._redirect_to_messaging()
            else:
                record_action = record_sudo.get_access_action(access_uid=uid)
        else:
            record_action = record_sudo.get_access_action()
            if record_action['type'] == 'ir.actions.act_url' and record_action.get('target_type') != 'public':
                url_params = {
                    'model': model,
                    'id': res_id,
                    'active_id': res_id,
                    'action': record_action.get('id'),
                }
                view_id = record_sudo.get_formview_id()
                if view_id:
                    url_params['view_id'] = view_id
                url = '/web/login?redirect=#%s' % url_encode(url_params)
                return werkzeug.utils.redirect(url)

        record_action.pop('target_type', None)
        # the record has an URL redirection: use it directly
        if record_action['type'] == 'ir.actions.act_url':
            return werkzeug.utils.redirect(record_action['url'])
        # other choice: act_window (no support of anything else currently)
        elif not record_action['type'] == 'ir.actions.act_window':
            return cls._redirect_to_messaging()

        url_params = {
            'model': model,
            'id': res_id,
            'active_id': res_id,
            'action': record_action.get('id'),
        }
        view_id = record_sudo.get_formview_id()
        if view_id:
            url_params['view_id'] = view_id

        if cids:
            url_params['cids'] = ','.join([str(cid) for cid in cids])
        url = '/web?#%s' % url_encode(url_params)
        return werkzeug.utils.redirect(url)

    @http.route('/mail/thread/data', methods=['POST'], type='json', auth='user')
    def mail_thread_data(self, thread_model, thread_id, request_list, **kwargs):
        res = {}
        thread = request.env[thread_model].with_context(active_test=False).search([('id', '=', thread_id)])
        if 'attachments' in request_list:
            res['attachments'] = thread.env['ir.attachment'].search([('res_id', '=', thread.id), ('res_model', '=', thread._name)], order='id desc')._attachment_format(commands=True)
        return res

    @http.route('/mail/read_followers', type='json', auth='user')
    def read_followers(self, res_model, res_id):
        request.env['mail.followers'].check_access_rights("read")
        request.env[res_model].check_access_rights("read")
        request.env[res_model].browse(res_id).check_access_rule("read")
        follower_recs = request.env['mail.followers'].search([('res_model', '=', res_model), ('res_id', '=', res_id)])

        followers = []
        follower_id = None
        for follower in follower_recs:
            if follower.partner_id == request.env.user.partner_id:
                follower_id = follower.id
            followers.append({
                'id': follower.id,
                'partner_id': follower.partner_id.id,
                'channel_id': follower.channel_id.id,
                'name': follower.name,
                'display_name': follower.display_name,
                'email': follower.email,
                'is_active': follower.is_active,
                # When editing the followers, the "pencil" icon that leads to the edition of subtypes
                # should be always be displayed and not only when "debug" mode is activated.
                'is_editable': True
            })
        return {
            'followers': followers,
            'subtypes': self.read_subscription_data(follower_id) if follower_id else None
        }

    @http.route('/mail/read_subscription_data', type='json', auth='user')
    def read_subscription_data(self, follower_id):
        """ Computes:
            - message_subtype_data: data about document subtypes: which are
                available, which are followed if any """
        request.env['mail.followers'].check_access_rights("read")
        follower = request.env['mail.followers'].sudo().browse(follower_id)
        follower.ensure_one()
        request.env[follower.res_model].check_access_rights("read")
        request.env[follower.res_model].browse(follower.res_id).check_access_rule("read")

        # find current model subtypes, add them to a dictionary
        subtypes = request.env['mail.message.subtype'].search([
            '&', ('hidden', '=', False),
            '|', ('res_model', '=', follower.res_model), ('res_model', '=', False)])
        followed_subtypes_ids = set(follower.subtype_ids.ids)
        subtypes_list = [{
            'name': subtype.name,
            'res_model': subtype.res_model,
            'sequence': subtype.sequence,
            'default': subtype.default,
            'internal': subtype.internal,
            'followed': subtype.id in followed_subtypes_ids,
            'parent_model': subtype.parent_id.res_model,
            'id': subtype.id
        } for subtype in subtypes]
        return sorted(subtypes_list,
                      key=lambda it: (it['parent_model'] or '', it['res_model'] or '', it['internal'], it['sequence']))

    @http.route('/mail/view', type='http', auth='public')
    def mail_action_view(self, model=None, res_id=None, access_token=None, **kwargs):
        """ Generic access point from notification emails. The heuristic to
            choose where to redirect the user is the following :

         - find a public URL
         - if none found
          - users with a read access are redirected to the document
          - users without read access are redirected to the Messaging
          - not logged users are redirected to the login page

            models that have an access_token may apply variations on this.
        """
        # ==============================================================================================
        # This block of code disappeared on saas-11.3 to be reintroduced by TBE.
        # This is needed because after a migration from an older version to saas-11.3, the link
        # received by mail with a message_id no longer work.
        # So this block of code is needed to guarantee the backward compatibility of those links.
        if kwargs.get('message_id'):
            try:
                message = request.env['mail.message'].sudo().browse(int(kwargs['message_id'])).exists()
            except:
                message = request.env['mail.message']
            if message:
                model, res_id = message.model, message.res_id
        # ==============================================================================================

        if res_id and isinstance(res_id, str):
            try:
                res_id = int(res_id)
            except ValueError:
                res_id = False
        return self._redirect_to_record(model, res_id, access_token, **kwargs)

    @http.route('/mail/assign', type='http', auth='user', methods=['GET'])
    def mail_action_assign(self, model, res_id, token=None):
        comparison, record, redirect = self._check_token_and_record_or_redirect(model, int(res_id), token)
        if comparison and record:
            try:
                record.write({'user_id': request.uid})
            except Exception:
                return self._redirect_to_messaging()
        return redirect

    @http.route('/mail/<string:res_model>/<int:res_id>/avatar/<int:partner_id>', type='http', auth='public')
    def avatar(self, res_model, res_id, partner_id):
        headers = [('Content-Type', 'image/png')]
        status = 200
        content = 'R0lGODlhAQABAIABAP///wAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='  # default image is one white pixel
        if res_model in request.env:
            try:
                # if the current user has access to the document, get the partner avatar as sudo()
                request.env[res_model].browse(res_id).check_access_rule('read')
                if partner_id in request.env[res_model].browse(res_id).sudo().exists().message_ids.mapped('author_id').ids:
                    status, headers, _content = request.env['ir.http'].sudo().binary_content(
                        model='res.partner', id=partner_id, field='image_128', default_mimetype='image/png')
                    # binary content return an empty string and not a placeholder if obj[field] is False
                    if _content != '':
                        content = _content
                    if status == 304:
                        return werkzeug.wrappers.Response(status=304)
            except AccessError:
                pass
        image_base64 = base64.b64decode(content)
        headers.append(('Content-Length', len(image_base64)))
        response = request.make_response(image_base64, headers)
        response.status = str(status)
        return response

    @http.route('/mail/needaction', type='json', auth='user')
    def needaction(self):
        return request.env['res.partner'].get_needaction_count()

    @http.route('/mail/init_messaging', type='json', auth='user')
    def mail_init_messaging(self):
        values = {
            'needaction_inbox_counter': request.env['res.partner'].get_needaction_count(),
            'starred_counter': request.env['res.partner'].get_starred_count(),
            'channel_slots': request.env['mail.channel'].channel_fetch_slot(),
            'mail_failures': request.env['mail.message'].message_fetch_failed(),
            'commands': request.env['mail.channel'].get_mention_commands(),
            'mention_partner_suggestions': request.env['res.partner'].get_static_mention_suggestions(),
            'shortcodes': request.env['mail.shortcode'].sudo().search_read([], ['source', 'substitution', 'description']),
            'menu_id': request.env['ir.model.data'].xmlid_to_res_id('mail.menu_root_discuss'),
            'moderation_counter': request.env.user.moderation_counter,
            'moderation_channel_ids': request.env.user.moderation_channel_ids.ids,
            'partner_root': request.env.ref('base.partner_root').sudo().mail_partner_format(),
            'public_partner': request.env.ref('base.public_partner').sudo().mail_partner_format(),
            'public_partners': [partner.mail_partner_format() for partner in request.env.ref('base.group_public').sudo().with_context(active_test=False).users.partner_id],
            'current_partner': request.env.user.partner_id.mail_partner_format(),
            'current_user_id': request.env.user.id,
        }
        return values

    @http.route('/mail/count_messaging_unread', type='json', auth='user')
    def mail_count_messaging_unread(self):
        if not request.uid:
            return []
        
        uid = request.uid
        user = request.env['res.users'].sudo().browse(uid)
        partner = user.partner_id

        # Recherche des canaux où ce partner est membre
        channels = request.env['mail.channel'].sudo().search([
            ('channel_partner_ids', 'in', [partner.id])
        ])

        result = []
        # The above Python code snippet is iterating over a list of channels and retrieving
        # information about unread messages for each channel and a specific partner. It does the following:
        for channel in channels:
            partner_info = request.env['mail.channel.partner'].sudo().search([
                ('channel_id', '=', channel.id),
                ('partner_id', '=', partner.id),
            ], limit=1)

            if partner_info and partner_info.seen_message_id:
                unread_count = request.env['mail.message'].sudo().search_count([
                    ('model', '=', 'mail.channel'),
                    ('res_id', '=', channel.id),
                    ('id', '>', partner_info.seen_message_id.id),
                ])
            else:
                unread_count = request.env['mail.message'].sudo().search_count([
                    ('model', '=', 'mail.channel'),
                    ('res_id', '=', channel.id),
                ])

            result.append({
                'id': channel.id,
                'uuid': channel.uuid,
                'name': channel.name,
                'channel_type': channel.channel_type,
                'unread_count': unread_count,
            })
        return result
    
    #---------------------- OLD --------------------- 
    # @http.route('/mail/discussions/all', type='json', auth='user')
    # def get_combined_discussions(self, limit=30, offset=0):
        try:
            limit = int(limit)
            offset = int(offset)
            partner = request.env.user.partner_id

            # --- 1️⃣ Précharger tous les canaux et last messages ---
            channel_slots = request.env['mail.channel'].channel_fetch_slot()
            all_channels = [c for slot in channel_slots.values() for c in slot]
            channel_ids = [c['id'] for c in all_channels]

            # Précharger mail.channel.partner pour ce partenaire
            partner_info_map = {
                p.channel_id.id: p
                for p in request.env['mail.channel.partner'].sudo().search([
                    ('channel_id', 'in', channel_ids),
                    ('partner_id', '=', partner.id)
                ])
            }

            # Précharger le dernier message par canal
            messages = request.env['mail.message'].sudo().search([
                ('model', '=', 'mail.channel'),
                ('res_id', 'in', channel_ids),
                ('message_type', 'in', ['comment', 'user_notification', 'notification'])
            ], order='date desc')

            last_message_map = {}
            for msg in messages:
                if msg.res_id not in last_message_map:
                    last_message_map[msg.res_id] = msg

            # Préparer toutes les discussions
            canaux_with_last_message = []
            for canal in all_channels:
                last_message = last_message_map.get(canal['id'])
                partner_info = partner_info_map.get(canal['id'])

                if partner_info and partner_info.seen_message_id:
                    unread_count = sum(
                        1 for m in messages
                        if m.res_id == canal['id'] and m.id > partner_info.seen_message_id.id
                    )
                else:
                    unread_count = sum(1 for m in messages if m.res_id == canal['id'])

                if last_message:
                    clean_text = last_message.body or "Nouveau message"
                    last_author_name = getattr(last_message.author_id, 'name', 'Unknown')
                    last_author_id = getattr(last_message.author_id, 'id', None)
                    is_mine = last_author_id == partner.id

                    display_name = canal['name']
                    display_text = clean_text

                    if canal['channel_type'] == 'chat':
                        # Pour chat privé, afficher le nom de l'autre membre
                        other_members = [m['id'] for m in canal.get('members', []) if m['id'] != partner.id]
                        if other_members:
                            other_member = request.env['res.partner'].sudo().browse(other_members[0])
                            display_name = other_member.name or other_member.email
                        if is_mine:
                            display_text = f"⤻ Vous : {clean_text}"
                    else:
                        display_text = f"⤻ {'Vous' if is_mine else last_author_name} : {clean_text}"

                    canaux_with_last_message.append({
                        'uuid': canal['uuid'],
                        'name': display_name,
                        'conversation_type': canal['channel_type'],
                        'text': display_text,
                        'time': last_message.date,
                        'channelId': canal['id'],
                        'email': getattr(last_message.author_id, 'email', ''),
                        'unreadCount': unread_count
                    })

            # --- 2️⃣ Précharger toutes les notifications non lues ---
            system_user_id = request.env.ref('base.user_root').id
            notifications = request.env['mail.message'].sudo().search([
                ('message_type', 'in', ['user_notification', 'notification']),
                ('author_id', '=', system_user_id)
            ], order='date desc', limit=limit + 10)

            unread_notifications = request.env['mail.notification'].sudo().search([
                ('res_partner_id', '=', partner.id),
                ('is_read', '=', False)
            ])
            unread_map = {n.mail_message_id.id: True for n in unread_notifications}

            # Regrouper par modèle
            grouped_by_model = {}
            for notif in notifications:
                model_key = notif.model or 'other'
                if model_key not in grouped_by_model:
                    grouped_by_model[model_key] = {
                        'messages': [],
                        'unreadCount': 0,
                        'lastMessageTime': notif.date
                    }

                grouped_by_model[model_key]['messages'].append(notif)
                grouped_by_model[model_key]['unreadCount'] += 1 if unread_map.get(notif.id) else 0
                grouped_by_model[model_key]['lastMessageTime'] = max(
                    grouped_by_model[model_key]['lastMessageTime'], notif.date
                )

            # Mapping pour titre plus lisible
            model_titles = {
                'sale.order': 'Bon de commande',
                'account.move': 'Facture',
                'account.bank.statement': 'Relevé bancaire',
                'res.partner': 'Contact',
                'mail.channel': 'Canal de discussion',
                'stock.picking': 'Transfert de stock' 
            }

            notif_with_details = []
            for model, group in grouped_by_model.items():
                if all(not (m.body or '').strip() for m in group['messages']):
                    continue

                last_message = group['messages'][0]
                last_body = (last_message.body or '').strip()
                res_id = last_message.res_id if last_message and last_message.res_id else 0

                notif_with_details.append({
                    'uuid': f'group_{model}',
                    'name': model_titles.get(model, model),
                    'conversation_type': 'notification',
                    'text': f"{last_body}",
                    'time': group['lastMessageTime'],
                    'channelId': None,
                    'email': '',
                    'unreadCount': group['unreadCount'],
                    'target': {
                        'model': model,
                        'res_id': res_id
                    }
                })

            # --- 3️⃣ Fusionner et trier ---
            combined_list = canaux_with_last_message + notif_with_details
            combined_list.sort(key=lambda x: x['time'], reverse=True)
            paginated_list = combined_list[offset:offset + limit]

            return paginated_list

        except Exception as e:
            _logger.error(f"Erreur dans get_combined_discussions: {str(e)}")
            raise
    
    @http.route('/mail/discussions/all', type='json', auth='user')
    def get_combined_discussions(self, limit=30, offset=0, filter_type='all'):
        """
        Un seul endpoint avec 4 options:
        - filter_type='all' → Tout combiné (comportement actuel)
        - filter_type='channels' → Canaux seulement
        - filter_type='activities' → Activités seulement
        - filter_type='notifications' → Notifications système seulement
        """
        try:
            limit = int(limit)
            offset = int(offset)
            partner = request.env.user.partner_id
            
            # if filter_type == 'channels':
            #     return self._get_channels(partner, limit, offset)
            # elif filter_type == 'activities':
            #     return self._get_activities(partner, limit, offset)
            # elif filter_type == 'notifications':
            #     return self._get_system_notifications(partner, limit, offset)
            # else:  # 'all' ou par défaut
            #     return self._get_all_combined(partner, limit, offset)
            self._get_all_combined(partner, limit, offset)
                
        except Exception as e:
            _logger.error(f"Erreur dans get_combined_discussions: {str(e)}")
            raise

    # -------------------------------------------------------------------
    # 1. Fonction pour les CANAUX seulement
    # -------------------------------------------------------------------
    def _get_channels(self, partner, limit, offset):
        """Retourne seulement les canaux de discussion"""
        # Récupérer les canaux
        channel_slots = request.env['mail.channel'].channel_fetch_slot()
        all_channels = [c for slot in channel_slots.values() for c in slot]
        channel_ids = [c['id'] for c in all_channels]
        
        # Messages des canaux (comment + email seulement)
        messages = request.env['mail.message'].sudo().search([
            ('model', '=', 'mail.channel'),
            ('res_id', 'in', channel_ids),
            ('message_type', 'in', ['comment', 'email'])
        ], order='date desc')
        
        # Précharger les informations de canal partenaire
        partner_info_map = {
            p.channel_id.id: p
            for p in request.env['mail.channel.partner'].sudo().search([
                ('channel_id', 'in', channel_ids),
                ('partner_id', '=', partner.id)
            ])
        }
        
        # Dernier message par canal
        last_message_map = {}
        for msg in messages:
            if msg.res_id not in last_message_map:
                last_message_map[msg.res_id] = msg
        
        # Formater les canaux
        formatted_channels = []
        for canal in all_channels:
            last_message = last_message_map.get(canal['id'])
            if not last_message:
                continue
            
            partner_info = partner_info_map.get(canal['id'])
            
            # Calcul messages non lus
            if partner_info and partner_info.seen_message_id:
                unread_count = sum(
                    1 for m in messages
                    if m.res_id == canal['id'] and m.id > partner_info.seen_message_id.id
                )
            else:
                unread_count = sum(1 for m in messages if m.res_id == canal['id'])
            
            # Formatage du texte
            clean_text = last_message.body or "Nouveau message"
            is_mine = last_message.author_id.id == partner.id
            
            display_name = canal['name']
            display_text = clean_text

            if canal['channel_type'] == 'chat':
                other_members = [m['id'] for m in canal.get('members', []) if m['id'] != partner.id]
                if other_members:
                    other_member = request.env['res.partner'].sudo().browse(other_members[0])
                    display_name = other_member.name or other_member.email
                if is_mine:
                    display_text = f"⤻ Vous : {clean_text}"
            else:
                display_text = f"⤻ {'Vous' if is_mine else last_message.author_id.name} : {clean_text}"
            
            formatted_channels.append({
                'uuid': canal['uuid'],
                'name': display_name,
                'conversation_type': canal['channel_type'],
                'text': display_text[:100] + ('...' if len(display_text) > 100 else ''),
                'time': last_message.date,
                'channelId': canal['id'],
                'email': getattr(last_message.author_id, 'email', ''),
                'unreadCount': unread_count,
                'filter_type': 'channel'
            })
        
        # Trier et paginer
        formatted_channels.sort(key=lambda x: x['time'], reverse=True)
        return formatted_channels[offset:offset + limit]

    # -------------------------------------------------------------------
    # 2. Fonction pour les ACTIVITÉS seulement
    # -------------------------------------------------------------------
    # def _get_activities(self, partner, limit, offset):
    #     """Retourne seulement les activités (user_notifications)"""
    #     system_user_id = request.env.ref('base.user_root').id
        
    #     # Récupérer les user_notifications
    #     user_notifications = request.env['mail.message'].sudo().search([
    #         ('message_type', 'in', ['user_notification', 'notification']),
    #         ('partner_ids', 'in', [partner.id]),
    #         ('author_id', '!=', system_user_id)  # Exclure les notifications système
    #     ], order='date desc', limit=limit + offset + 20)
        
    #     # _logger.debug(f"Activity notifications fetched: {len(user_notifications)} for partner {partner.id}")
    #     # _logger.debug(f"Activity notifications IDs: {[n.model for n in user_notifications]}")
    #     # Lier aux activités pour avoir le type
    #     activity_ids = [n.res_id for n in user_notifications if n.model == 'mail.activity']
    #     activities = request.env['mail.activity'].sudo().search([
    #         ('id', 'in', activity_ids)
    #     ])
        
    #     # Mapping activité -> type
    #     activity_type_map = {}
    #     for activity in activities:
    #         if activity.activity_type_id:
    #             activity_type_map[activity.id] = activity.activity_type_id.name
    #         else:
    #             activity_type_map[activity.id] = 'To Do'
        
    #     # Grouper par type d'activité
    #     activity_groups = {}
    #     for notif in user_notifications:
    #         # Déterminer le type
    #         if notif.model == 'mail.activity' and notif.res_id:
    #             activity_type = activity_type_map.get(notif.res_id, 'To Do')
    #         else:
    #             activity_type = 'Notification'
            
    #         if activity_type not in activity_groups:
    #             activity_groups[activity_type] = {
    #                 'messages': [],
    #                 'unreadCount': 0,
    #                 'lastMessageTime': notif.date
    #             }
            
    #         activity_groups[activity_type]['messages'].append(notif)
    #         activity_groups[activity_type]['lastMessageTime'] = max(
    #             activity_groups[activity_type]['lastMessageTime'], notif.date
    #         )
        
    #     # Titres des activités
    #     activity_titles = {
    #         'Email': 'Email',
    #         'Call': 'Appel téléphonique',
    #         'To Do': 'Tâche à faire',
    #         'Upload Document': 'Document à uploader',
    #         'Exception': 'Exception',
    #         'Order Upsell': 'Vente incitative',
    #         'Meeting': 'Réunion',
    #         'Contract to Renew': 'Contrat à renouveler',
    #         'Time Off Approval': 'Approbation congés',
    #         'Time Off Second Approve': '2ème approbation congés',
    #         'Allocation Approval': 'Approbation allocation',
    #         'Allocation Second Approve': '2ème approbation allocation',
    #         'Maintenance Request': 'Demande maintenance',
    #         'Expense Approval': 'Approbation frais',
    #         'Reminder': 'Rappel',
    #         'Session open over 7 days': 'Session ouverte > 7 jours',
    #         'Alert Date Reached': 'Date d\'alerte atteinte',
    #     }
        
    #     # Formater les groupes
    #     formatted_activities = []
    #     for activity_type, group in activity_groups.items():
    #         _logger.debug(f"Processing activity type: {activity_type} with {len(group['messages'])} messages")
    #         if not group['messages']:
    #             continue
            
    #         last_message = group['messages'][0]
    #         last_body = (last_message.body or '').strip()
    #         total_count = len(group['messages'])
            
    #         formatted_activities.append({
    #             'uuid': f'activity_{activity_type}',
    #             'name': activity_titles.get(activity_type, activity_type),
    #             'conversation_type': 'activity',
    #             'text': f"{last_body[:80]}...",
    #             'time': group['lastMessageTime'],
    #             'channelId': None,
    #             'email': getattr(last_message.author_id, 'email', ''),
    #             'unreadCount': total_count,
    #             'target': {
    #                 'model': 'mail.activity',
    #                 'type': activity_type
    #             },
    #             'filter_type': 'activity'
    #         })
        
    #     # Trier et paginer
    #     formatted_activities.sort(key=lambda x: x['time'], reverse=True)
    #     return formatted_activities[offset:offset + limit]

    def _get_activities(self, partner, limit, offset):
        """Retourne les activités groupées par type, dans votre format existant"""
        system_user_id = request.env.ref('base.user_root').id
        
        # Récupérer les user_notifications
        user_notifications = request.env['mail.message'].sudo().search([
            ('message_type', 'in', ['user_notification', 'notification']),
            ('partner_ids', 'in', [partner.id]),
            ('author_id', '!=', system_user_id)
        ], order='date desc', limit=limit + offset + 100)  # Prendre plus pour le regroupement
        
        # Grouper par type d'activité
        from collections import defaultdict
        activity_groups = defaultdict(list)
        
        for notif in user_notifications:
            # Extraire le type d'activité du sujet
            activity_type = self._extract_activity_type_from_subject(notif.subject)
            
            if not activity_type:
                activity_type = 'Notification'
            
            activity_groups[activity_type].append(notif)
        
        # Titres des activités
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
        
        # Formater les groupes dans votre structure
        formatted_activities = []
        
        for activity_type, messages in activity_groups.items():
            if not messages:
                continue
            
            # Trier les messages par date (du plus récent au plus ancien)
            messages.sort(key=lambda m: m.date or m.create_date, reverse=True)
            
            # Prendre le dernier message pour l'aperçu
            last_message = messages[0]
            
            # Extraire les infos pour l'aperçu
            preview_info = self._get_activity_preview_info(last_message)
            
            # Compter les non-lus (is_internal = False)
            unread_count = sum(1 for m in messages if not m.is_internal)
            
            # Nombre total dans ce groupe
            total_count = len(messages)
            
            # Nom d'affichage
            display_name = activity_titles.get(activity_type, activity_type)
            
            # Créer l'UUID basé sur le type d'activité
            activity_uuid = f'activity_{activity_type.lower().replace(" ", "_")}'
            
            formatted_activities.append({
                'uuid': activity_uuid,
                'name': display_name,
                'conversation_type': 'activity',
                'text': preview_info['text'],  # Texte d'aperçu
                'time': last_message.date.isoformat() if last_message.date else None,
                'channelId': None,  # Pas de canal pour les activités
                'email': getattr(last_message.author_id, 'email', '') if last_message.author_id else '',
                'unreadCount': unread_count,
                'target': {
                    'model': 'mail.activity',
                    'type': activity_type,
                    'record_name': preview_info.get('record_name'),
                    'deadline': preview_info.get('deadline')
                },
                'metadata': {
                    'total_count': total_count,
                    'has_unread': unread_count > 0,
                    'icon': self._get_activity_icon(activity_type),
                    'color': self._get_activity_color(activity_type),
                    'last_message_id': last_message.id
                },
                'filter_type': 'activity'
            })
            
            _logger.debug(
                f"Activity group created: {display_name} - "
                f"Total: {total_count}, Unread: {unread_count}, "
                f"Last: {last_message.date}"
            )
        
        # Trier par date du dernier message (décroissant)
        formatted_activities.sort(
            key=lambda x: x['time'] or '1970-01-01T00:00:00',
            reverse=True
        )
        
        # Pagination
        paginated_result = formatted_activities[offset:offset + limit]
        
        _logger.info(
            f"📊 Activity groups returned: {len(paginated_result)} of {len(formatted_activities)} "
            f"(limit: {limit}, offset: {offset})"
        )
        
        return paginated_result

    # Helpers
    def _extract_activity_type_from_subject(self, subject):
        """Extrait le type d'activité du sujet du message"""
        if not subject:
            return 'Notification'
        
        import re
        
        # Pattern: "S00079: À faire vous a été attribué"
        match = re.search(r':\s*([^:]+)\s+(vous a été attribué|assigned to you)', subject, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Chercher des mots-clés spécifiques
        keywords = [
            ('À faire', 'À faire'),
            ('To Do', 'To Do'),
            ('Appeler', 'Appeler'),
            ('Call', 'Call'),
            ('Rappel', 'Rappel'),
            ('Reminder', 'Reminder'),
            ('Exception', 'Exception'),
            ('Meeting', 'Meeting'),
            ('Email', 'Email'),
            ('Upload Document', 'Upload Document'),
            ('Order Upsell', 'Order Upsell'),
            ('Contract to Renew', 'Contract to Renew'),
            ('Time Off Approval', 'Time Off Approval'),
            ('Time Off Second Approve', 'Time Off Second Approve'),
            ('Allocation Approval', 'Allocation Approval'),
            ('Allocation Second Approve', 'Allocation Second Approve'),
            ('Maintenance Request', 'Maintenance Request'),
            ('Expense Approval', 'Expense Approval'),
            ('Session open over 7 days', 'Session open over 7 days'),
            ('Alert Date Reached', 'Alert Date Reached'),
        ]
        
        for keyword, activity_type in keywords:
            if keyword in subject:
                return activity_type
        
        return 'Notification'

    def _get_activity_preview_info(self, message):
        """Extrait les infos pour l'aperçu d'une activité"""
        import re
        import html
        
        # Nettoyer le HTML du body
        if message.body:
            # Extraire la date d'échéance
            deadline_match = re.search(
                r'à fermer pour\s*<span>([^<]+)</span>|to close for\s*<span>([^<]+)</span>',
                message.body
            )
            deadline = None
            if deadline_match:
                deadline = deadline_match.group(1) or deadline_match.group(2)
            
            # Extraire le nom de l'enregistrement du body
            record_match = re.search(
                r'le\s*<span>([^<]+)</span>|on\s*<span>([^<]+)</span>',
                message.body
            )
            record_name = None
            if record_match:
                record_name = record_match.group(1) or record_match.group(2)
        else:
            deadline = None
            record_name = None
        
        # Si pas de record_name dans le body, utiliser record_name du message
        if not record_name and message.record_name:
            record_name = message.record_name
        
        # Construire le texte d'aperçu
        if record_name and deadline:
            preview_text = f"{record_name} • Échéance: {deadline}"
        elif record_name:
            preview_text = f"{record_name}"
        elif deadline:
            preview_text = f"Échéance: {deadline}"
        else:
            # Fallback: sujet tronqué
            preview_text = message.subject or "Nouvelle activité"
            if len(preview_text) > 60:
                preview_text = preview_text[:57] + "..."
        
        return {
            'text': preview_text,
            'record_name': record_name,
            'deadline': deadline,
            'model': message.model
        }

    def _get_activity_icon(self, activity_type):
        """Retourne l'emoji/icône pour le type d'activité"""
        icon_map = {
            'À faire': '✅',
            'To Do': '✅',
            'Appeler': '📞',
            'Call': '📞',
            'Rappel': '🔔',
            'Reminder': '🔔',
            'Exception': '⚠️',
            'Meeting': '👥',
            'Email': '📧',
            'Upload Document': '📎',
            'Order Upsell': '📈',
            'Contract to Renew': '📄',
            'Time Off Approval': '🏖️',
            'Time Off Second Approve': '🏖️',
            'Allocation Approval': '⏰',
            'Allocation Second Approve': '⏰',
            'Maintenance Request': '🔧',
            'Expense Approval': '💰',
            'Session open over 7 days': '⏳',
            'Alert Date Reached': '🚨',
            'Notification': '🔔',
        }
        return icon_map.get(activity_type, '🔔')

    def _get_activity_color(self, activity_type):
        """Retourne la couleur pour le type d'activité"""
        color_map = {
            'À faire': '#4CAF50',      # Vert
            'To Do': '#4CAF50',
            'Appeler': '#2196F3',      # Bleu
            'Call': '#2196F3',
            'Rappel': '#FF9800',       # Orange
            'Reminder': '#FF9800',
            'Exception': '#F44336',    # Rouge
            'Meeting': '#9C27B0',      # Violet
            'Email': '#00BCD4',        # Cyan
            'Upload Document': '#607D8B', # Gris
            'Order Upsell': '#FF5722', # Rouge-orange
            'Contract to Renew': '#795548', # Marron
            'Time Off Approval': '#009688', # Turquoise
            'Time Off Second Approve': '#009688',
            'Allocation Approval': '#3F51B5', # Indigo
            'Allocation Second Approve': '#3F51B5',
            'Maintenance Request': '#8BC34A', # Vert clair
            'Expense Approval': '#673AB7', # Violet profond
            'Session open over 7 days': '#FFC107', # Jaune
            'Alert Date Reached': '#E91E63', # Rose
            'Notification': '#9E9E9E', # Gris
        }
        return color_map.get(activity_type, '#9E9E9E')













    # -------------------------------------------------------------------
    # 3. Fonction pour les NOTIFICATIONS SYSTÈME seulement
    # -------------------------------------------------------------------
    def _get_system_notifications(self, partner, limit, offset):
        """Retourne seulement les notifications système"""
        system_user_id = request.env.ref('base.user_root').id
        
        # Récupérer les notifications système
        notifications = request.env['mail.message'].sudo().search([
            ('message_type', 'in', ['user_notification', 'notification']),
            ('author_id', '=', system_user_id)
        ], order='date desc', limit=limit + offset + 20)
        
        _logger.debug(f"System notifications fetched: {len(notifications)} for partner {partner.id}")
        
        # Notifications non lues
        unread_notifications = request.env['mail.notification'].sudo().search([
            ('res_partner_id', '=', partner.id),
            ('is_read', '=', False)
        ])
        unread_map = {n.mail_message_id.id: True for n in unread_notifications}
        
        # Grouper par modèle
        grouped_by_model = {}
        for notif in notifications:
            model_key = notif.model or 'other'
            
            if model_key not in grouped_by_model:
                grouped_by_model[model_key] = {
                    'messages': [],
                    'unreadCount': 0,
                    'lastMessageTime': notif.date
                }
            
            grouped_by_model[model_key]['messages'].append(notif)
            if unread_map.get(notif.id):
                grouped_by_model[model_key]['unreadCount'] += 1
            grouped_by_model[model_key]['lastMessageTime'] = max(
                grouped_by_model[model_key]['lastMessageTime'], notif.date
            )
        
        # Titres des modèles
        model_titles = {
            'sale.order': 'Bon de commande',
            'account.move': 'Facture',
            'account.bank.statement': 'Relevé bancaire',
            'res.partner': 'Contact',
            'mail.channel': 'Canal de discussion',
            'stock.picking': 'Transfert de stock',
            'mail.activity': 'Activité',
        }
        
        # Formater les groupes
        formatted_notifications = []
        for model, group in grouped_by_model.items():
            if all(not (m.body or '').strip() for m in group['messages']):
                continue
            
            last_message = group['messages'][0]
            last_body = (last_message.body or '').strip()
            res_id = last_message.res_id if last_message and last_message.res_id else 0
            
            formatted_notifications.append({
                'uuid': f'group_{model}',
                'name': model_titles.get(model, model),
                'conversation_type': 'notification',
                'text': f"{last_body[:80]}...",
                'time': group['lastMessageTime'],
                'channelId': None,
                'email': '',
                'unreadCount': group['unreadCount'],
                'target': {
                    'model': model,
                    'res_id': res_id
                },
                'filter_type': 'notification'
            })
        
        # Trier et paginer
        formatted_notifications.sort(key=lambda x: x['time'], reverse=True)
        return formatted_notifications[offset:offset + limit]

    # -------------------------------------------------------------------
    # 4. Fonction pour TOUT combiné (comportement original)
    # -------------------------------------------------------------------
    def _get_all_combined(self, partner, limit, offset):
        """Retourne tout combiné - votre logique originale"""
        # Appeler les 3 fonctions
        channels = self._get_channels(partner, limit//3 + 10, 0)
        activities = self._get_activities(partner, limit//3 + 10, 0)
        notifications = self._get_system_notifications(partner, limit//3 + 10, 0)
        
        # Combiner
        combined_list = channels + activities + notifications
        
        # Trier par date
        combined_list.sort(key=lambda x: x['time'], reverse=True)
        
        # Paginer
        paginated_list = combined_list[offset:offset + limit]
        
        # Ajouter un flag pour indiquer le type (pour le tri mobile)
        for item in paginated_list:
            if 'filter_type' not in item:
                if item['conversation_type'] == 'channel':
                    item['filter_type'] = 'channel'
                elif item['conversation_type'] == 'activity':
                    item['filter_type'] = 'activity'
                elif item['conversation_type'] == 'notification':
                    item['filter_type'] = 'notification'
        
        return paginated_list
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    @http.route('/mail/get_suggested_recipients', type='json', auth='user')
    def message_get_suggested_recipients(self, model, res_ids):
        records = request.env[model].browse(res_ids)
        try:
            records.check_access_rule('read')
            records.check_access_rights('read')
        except:
            return {}
        return records._message_get_suggested_recipients()
    
    @http.route('/mail/channel/seen', type='json', auth='user', methods=['POST'])
    def channel_seen(self, channel_id=None, last_message_id=None, uuid=None):
        """
        Mark messages in a channel as seen up to last_message_id for the current user.
        """
        try:
            user = request.env.user
            partner = user.partner_id
            
            # 🔹 Cas 1 : groupe de notifications
            if uuid and uuid.startswith("group_"):
                model = uuid.replace("group_", "", 1)

                if not last_message_id:
                    return {
                        'jsonrpc': '2.0',
                        'error': {'code': 400, 'message': 'Missing last_message_id for notifications'}
                    }

                # Marquer toutes les notifs du modèle comme lues jusqu’à last_message_id
                domain = [
                    ('res_partner_id', '=', partner.id),
                    ('is_read', '=', False),
                    ('mail_message_id.model', '=', model),
                    ('mail_message_id.id', '<=', int(last_message_id))
                ]
                notifications = request.env['mail.notification'].sudo().search(domain)
                notifications.write({'is_read': True})

                # Recalcul du unread_count
                unread_count = request.env['mail.notification'].sudo().search_count([
                    ('res_partner_id', '=', partner.id),
                    ('is_read', '=', False),
                    ('mail_message_id.model', '=', model),
                ])

                return {
                    'jsonrpc': '2.0',
                    'result': {
                        'success': True,
                        'uuid': uuid,
                        'last_message_id': last_message_id,
                        'unreadCount': unread_count
                    }
                }
                
            # 🔹 Cas 2 : channel normal
            if not channel_id or not last_message_id:
                return {
                    'jsonrpc': '2.0',
                    'error': {'code': 400, 'message': 'Missing channel_id or last_message_id'}
                }

            # Fetch the channel
            channel = request.env['mail.channel'].sudo().browse(int(channel_id)).exists()
            if not channel:
                return {'jsonrpc': '2.0', 'error': {'code': 404, 'message': 'Channel not found'}}

            # Ensure user is a member
            if partner.id not in channel.channel_partner_ids.mapped('id'):
                return {'jsonrpc': '2.0', 'error': {'code': 403, 'message': 'User not a member of the channel'}}

            # Fetch the last message
            message = request.env['mail.message'].sudo().browse(int(last_message_id)).exists()
            if not message or message.model != 'mail.channel' or message.res_id != channel.id:
                return {'jsonrpc': '2.0', 'error': {'code': 404, 'message': 'Invalid message_id for this channel'}}

            # Update seen_message_id
            channel_partner = request.env['mail.channel.partner'].sudo().search([
                ('channel_id', '=', channel.id),
                ('partner_id', '=', partner.id)
            ], limit=1)
            if channel_partner:
                channel_partner.write({'seen_message_id': last_message_id})
            else:
                return {'jsonrpc': '2.0', 'error': {'code': 404, 'message': 'Channel partner record not found'}}

            # Update notifications in one query
            notifications = request.env['mail.notification'].sudo().search([
                ('res_partner_id', '=', partner.id),
                ('is_read', '=', False),
                ('mail_message_id.model', '=', 'mail.channel'),
                ('mail_message_id.res_id', '=', channel.id),
                ('mail_message_id.id', '<=', last_message_id)
            ])
            notifications.write({'is_read': True})

            # Recalculate unread_count
            unread_count = request.env['mail.message'].sudo().search_count([
                ('model', '=', 'mail.channel'),
                ('res_id', '=', channel.id),
                ('id', '>', last_message_id)
            ])

            return {
                'jsonrpc': '2.0',
                'result': {
                    'success': True,
                    'channel_id': channel.id,
                    'last_message_id': last_message_id,
                    'unreadCount': unread_count
                }
            }

        except (AccessError, ValidationError) as e:
            return {'jsonrpc': '2.0', 'error': {'code': 403, 'message': f'Access error: {str(e)}'}}
        except Exception as e:
            _logger.error(f"Erreur dans channel_seen: {str(e)}")
            return {'jsonrpc': '2.0', 'error': {'code': 500, 'message': f'Internal server error: {str(e)}'}}
        