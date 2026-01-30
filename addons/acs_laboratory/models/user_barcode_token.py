from odoo import models, fields, api
from datetime import datetime

class UserBarcodeToken(models.Model):
    _name = 'user.barcode.token'
    _description = 'Token de code-barres utilisateur'
    _order = 'create_date desc'
    
    user_id = fields.Many2one(
        'res.users',
        string='Utilisateur',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    token = fields.Char(
        string='Token complet',
        required=True,
        readonly=True,
        index=True,
        help='Token UUID pour authentification'
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True,
        help='Désactiver pour invalider le token'
    )
    
    create_date = fields.Datetime(
        string='Date de création',
        readonly=True,
        default=fields.Datetime.now
    )
    
    last_used = fields.Datetime(
        string='Dernière utilisation',
        readonly=True
    )
    
    @api.constrains('user_id')
    def _check_unique_active_token(self):
        """Vérifie qu'un utilisateur n'a qu'un seul token actif à la fois"""
        for token in self:
            if token.active:
                existing = self.search([
                    ('user_id', '=', token.user_id.id),
                    ('active', '=', True),
                    ('id', '!=', token.id)
                ])
                if existing:
                    raise ValidationError(
                        "Un utilisateur ne peut avoir qu'un seul token actif à la fois."
                    )