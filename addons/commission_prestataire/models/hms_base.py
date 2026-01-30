# -*- coding: utf-8 -*-

from odoo import fields, models, api, SUPERUSER_ID

class ResPartner(models.Model):
    _inherit = "res.partner"

    coprest_role_id = fields.Many2one('commission.prestataire.role', string='Role')
    coprest_ids = fields.One2many('commission.prestataire', 'partner_id', 'Paramètre de commission')
    prest_commission = fields.Boolean('Donner une commission prestataire')
    coprest_percentage = fields.Float('Part en Percentage')
    coprest_rule_ids = fields.One2many("commission.prestataire.rule", "partner_id", string="Règles de la Commission")

    def coprest_action(self):
        action = self.env["ir.actions.actions"]._for_xml_id("commission_prrestataire.commission_prestataire_action")
        action['domain'] = [('partner_id','=',self.id)]
        action['context'] = {'default_partner_id': self.id, 'search_default_not_invoiced': 1}
        return action


class Physician(models.Model):
    _inherit = "hms.physician"


    def coprest_action(self):
        action = self.env["ir.actions.actions"]._for_xml_id("commission_prestataire.coprest_action")
        action['domain'] = [('partner_id','=',self.partner_id.id)]
        action['context'] = {'default_partner_id': self.partner_id.id, 'search_default_not_invoiced': 1}
        return action


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: