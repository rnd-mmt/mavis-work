# -*- coding: utf-8 -*-
from odoo import models, api, fields


class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'

    @api.model
    def get_auto_logout_timeout(self):
        """
        Récupère la valeur du timeout de déconnexion automatique.
        Si le paramètre n'existe pas, le crée avec la valeur par défaut.
        """
        param_key = 'web.auto_logout_minutes'
        timeout = self.get_param(param_key, False)
        
        if not timeout:
            # Créer le paramètre s'il n'existe pas
            self.set_param(param_key, '5')
            timeout = '5'
        
        return timeout
