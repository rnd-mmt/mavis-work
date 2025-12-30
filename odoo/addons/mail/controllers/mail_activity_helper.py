from odoo.http import request

class MailActivityHelper:

    @staticmethod
    def get_activity_type_info(activity_type):
        """
        Retourne un dictionnaire avec display_name, icon et couleur
        basé sur la table mail_activity_type
        """
        activity = request.env['mail.activity.type'].sudo().search([
            ('name', '=', activity_type)
        ], limit=1)

        return {
            'display_name': activity.fcm_display_name or activity.name or activity_type,
            'icon': getattr(activity, 'icon', '🔔'),
            'color': activity.fcm_color or '#9E9E9E'
        }
