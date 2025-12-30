from odoo import models, api
import logging

_logger = logging.getLogger(__name__)
class MailActivityFCM(models.Model):
    _inherit = 'mail.activity'
    _logger.info("Modèle mail.activity +++ étendu pour FCM")
    
    @api.model
    def create(self, vals):
        _logger.warning("CREATE appelé - vals: %s", vals)
        activity = super().create(vals)
        _logger.warning("FCM ///// | id=%s", activity.id)
        self._handle_fcm(activity)
        return activity

    def _handle_fcm(self, activity):
        _logger.warning(
            "ACTIVITÉ ///// | id=%s | model=%s | res_id=%s | user=%s",
            activity.id,
            activity.res_model,
            activity.res_id,
            activity.user_id.name
        )

        self._send_fcm_notification_for_activity(activity)

    def activity_notify(self):
        res = super().activity_notify()

        for activity in self:
            _logger.warning(
                "FCM notify | model=%s | res_id=%s | user=%s",
                activity.res_model,
                activity.res_id,
                activity.user_id.name
            )
            self._send_fcm_notification_for_activity(activity)

        return res
    
    # def _after_create(self):
    #     super()._after_create()
    #     _logger.error("🔥 AFTER_CREATE MAIL.ACTIVITY APPELÉ 🔥")
    #     for activity in self:
    #         if activity.user_id:
    #             _logger.info(
    #                 f"📅 Activité planifiée pour {activity.user_id.name} "
    #                 f"(ID {activity.id})"
    #             )
    #             activity._notify_activity_creation()

    def write(self, vals):
        res = super().write(vals)
        _logger.info(f" Activité mise à jour: IDs {self.ids} avec vals={vals}")
        if 'user_id' in vals:
            for activity in self:
                if activity.user_id:
                    _logger.info(f"🔄 Activité {activity.id} réassignée à {activity.user_id.name}")
                    activity._send_fcm_notification_for_activity(activity)
        return res

    def _send_fcm_notification_for_activity(self, activity):
        _logger.info(f" Envoi notification FCM pour l'activité {activity.id}")
        """Envoyer une notification FCM pour une activité"""
        try:
            # Vérifier que l'utilisateur assigné a un partenaire
            if not activity.user_id or not activity.user_id.partner_id:
                _logger.warning(f"⚠️ Pas d'utilisateur ou partenaire pour l'activité {activity.id}")
                return
            
            # Récupérer les tokens FCM de l'utilisateur
            partner = activity.user_id.partner_id
            fcm_tokens = self.env['fcm.device'].get_partner_tokens(partner.id)
            
            if not fcm_tokens:
                _logger.info(f"ℹ️ Aucun token FCM pour le partenaire {partner.name}")
                return
            
            # Récupérer ou créer le canal de chat pour cette activité
            channel_uuid = self._get_or_create_activity_channel(activity.id, partner.id)
            
            # Données pour la notification
            notification_data = {
                'type': 'mail_activity_assigned',
                'model': 'mail.activity',
                'record_id': str(activity.id),
                'action': 'OPEN_ACTIVITY_CHAT',
                'channel_uuid': channel_uuid,
                
                # Données spécifiques à l'activité
                'activity_type': activity.activity_type_id.name or '',
                'summary': activity.summary or '',
                'res_model': activity.res_model or '',
                'res_name': activity.res_name or '',
                'res_id': str(activity.res_id) if activity.res_id else '',
                'date_deadline': activity.date_deadline.isoformat() if activity.date_deadline else '',
                'user_id': str(activity.user_id.id) if activity.user_id else '',
                
                # Pour le routing mobile
                'partner_id': str(partner.id),
                'timestamp': fields.Datetime.now().isoformat(),
                'sound': 'default',
                'vibrate': 'true',
            }
            
            # Titre et message personnalisés
            title = self._get_activity_notification_title(activity)
            body = self._get_activity_notification_body(activity)
            
            # Ajouter l'icône selon le type d'activité
            icon = self._get_activity_icon(activity.activity_type_id.name)
            if icon:
                title = f"{icon} {title}"
            
            _logger.info(f" --Envoi notification activité {activity.id} à {partner.name}")
            _logger.info(f" --Données: {notification_data}")
            
            # Envoyer à tous les appareils de l'utilisateur
            for token in fcm_tokens:
                self.env['fcm.service'].send_notification(
                    token=token,
                    title=title,
                    body=body,
                    data=notification_data
                )
                
        except Exception as e:
            _logger.error(f"❌ Erreur envoi notification FCM activité: {str(e)}")
    
    def _get_or_create_activity_channel(self, activity_id, partner_id):
        _logger.info(f" Récupération/création canal pour activité {activity_id} et partenaire {partner_id}")
        """Récupérer ou créer un canal de chat pour une activité"""
        activity = self.browse(activity_id)
        
        # Chercher un canal existant lié à cette activité
        existing_channel = self.env['mail.channel'].search([
            ('activity_ids', 'in', [activity_id]),
            ('channel_partner_ids', 'in', [partner_id])
        ], limit=1)
        
        if existing_channel:
            return existing_channel.uuid
        
        # Déterminer les participants
        partner_ids = [partner_id]
        if activity.user_id and activity.user_id.partner_id.id != partner_id:
            partner_ids.append(activity.user_id.partner_id.id)
        
        # Nom du canal
        channel_name = f"Activité: {activity.summary or activity.activity_type_id.name or 'Nouvelle activité'}"
        if activity.res_name:
            channel_name = f"{channel_name} - {activity.res_name}"
        
        # Créer un nouveau canal
        channel = self.env['mail.channel'].create({
            'name': channel_name[:64],  # Limiter la longueur
            'public': 'private',
            'channel_type': 'chat',
            'channel_partner_ids': [(6, 0, partner_ids)],
            'activity_ids': [(4, activity_id)],
        })
        
        # Ajouter un message d'introduction
        intro_message = f" Canal créé pour l'activité: {activity.summary or 'Sans titre'}"
        if activity.date_deadline:
            intro_message += f"\n⏰ Échéance: {activity.date_deadline.strftime('%d/%m/%Y')}"
        
        channel.message_post(
            body=intro_message,
            author_id=self.env.ref('base.partner_root').id,
            message_type='comment',
            subtype_xmlid='mail.mt_comment'
        )
        
        return channel.uuid
    
    def _get_activity_notification_title(self, activity):
        _logger.info(f" Génération titre notification pour l'activité {activity.id}")
        """Générer le titre de la notification"""
        activity_type = activity.activity_type_id.name or "Activité"
        
        if activity.res_name:
            return f"{activity_type} - {activity.res_name}"
        else:
            return f"Nouvelle {activity_type}"
    
    def _get_activity_notification_body(self, activity):
        _logger.info(f" Génération corps notification pour l'activité {activity.id}")
        """Générer le corps de la notification"""
        parts = []
        
        if activity.summary:
            parts.append(activity.summary)
        
        if activity.note:
            # Nettoyer le HTML pour la notification
            note_text = activity.note.replace('<p>', '').replace('</p>', '\n')
            note_text = note_text.replace('<br>', '\n')
            note_text = note_text[:100] + ('...' if len(note_text) > 100 else '')
            parts.append(note_text)
        
        if activity.date_deadline:
            deadline_str = activity.date_deadline.strftime('%d/%m/%Y')
            parts.append(f"⏰ Échéance: {deadline_str}")
        
        if not parts:
            parts.append("Nouvelle activité assignée")
        
        return " | ".join(parts)
    
    def _get_activity_icon(self, activity_type):
        """Retourner l'icône selon le type d'activité"""
        icon_map = {
            'To Do': '✅',
            'Call': '📞',
            'Meeting': '👥',
            'Email': '📧',
            'Upload Document': '📄',
            'Deadline': '⏰',
            'Reminder': '🔔',
        }
        return icon_map.get(activity_type, '')
    
    # Extension de la méthode create originale
    @api.model
    def create(self, values):
        """Surcharger create pour journaliser"""
        activity = super().create(values)
        _logger.info(f"📝 Activité créée: {activity.id} - {activity.summary}")
        return activity