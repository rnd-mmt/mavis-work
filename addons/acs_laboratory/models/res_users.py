import uuid
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    barcode_token_id = fields.Many2one(
        'user.barcode.token',
        string='Carte',
        ondelete='set null',
        copy=False  # Important : ne pas copier le token lors du duplicate
    )

    current_token = fields.Char(
        related='barcode_token_id.token',
        string='Token actuel',
        readonly=True,
        store=False  # Ne pas stocker en base, toujours lu depuis la relation
    )

    token_active = fields.Boolean(
        related='barcode_token_id.active',
        string='Token activé',
        readonly=False
    )
    
    # Champ technique pour gérer l'affichage du bouton
    is_in_edit_mode = fields.Boolean(
        string='En mode édition',
        compute='_compute_is_in_edit_mode',
        store=False,
        help='Champ technique pour afficher le bouton uniquement en mode édition'
    )
    
    @api.model
    def create(self, vals):
        """Création d'utilisateur avec génération automatique de token"""
        try:
            # Créer l'utilisateur
            user = super(ResUsers, self).create(vals)
            
            # Générer le token
            user._generate_token_on_create()
            
            return user
            
        except Exception as e:
            _logger.error("Erreur lors de la création de l'utilisateur avec token: %s", str(e))
            raise
    
    @api.depends_context('edit_mode')
    def _compute_is_in_edit_mode(self):
        """Calcule si l'utilisateur est en mode édition"""
        for user in self:
            # Le mode édition est déterminé par le contexte
            # ou par le paramètre dans l'URL
            user.is_in_edit_mode = self.env.context.get('edit_mode', False)
    
    def regenerate_token(self):
        """Génère un nouveau token UUID pour l'utilisateur"""
        for user in self:
            # Vérifier les permissions si nécessaire
            if not self.env.is_admin():
                raise UserError("Seuls les administrateurs peuvent régénérer des tokens.")
            
            # Supprimer l'existant avec vérification
            if user.barcode_token_id:
                # Vous pourriez vouloir archiver plutôt que supprimer
                user.barcode_token_id.unlink()
            
            # Créer un nouveau token
            token_record = self.env['user.barcode.token'].create({
                'user_id': user.id,
                'token': str(uuid.uuid4()),  # UUID v4 générique
                'active': True,
            })
            
            # Assigner le nouveau token avec write pour déclencher onchange
            user.write({
                'barcode_token_id': token_record.id,
            })
            return True

    def action_regenerate_token(self):
        """Action wrapper pour l'interface utilisateur"""
        self.ensure_one()
        self.regenerate_token()

        # Retourne une action qui actualise le formulaire
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Succès',
                'message': 'Token régénéré avec succès',
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def create(self, vals):
        """Surcharge de la création pour générer un token automatiquement"""
        user = super(ResUsers, self).create(vals)
        
        # Créer automatiquement un token pour les nouveaux utilisateurs
        if not user.barcode_token_id:
            user.regenerate_token()
        
        return user
