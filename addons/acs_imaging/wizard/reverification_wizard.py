# coding: utf-8

from odoo import models, api, fields


class AcsEditableReason(models.TransientModel):
    _name = 'imaging.editable.reason'
    _description = "Motif de remise en état éditable"

    editable_reason = fields.Text(string="Motif de revérification", required=True)

    def editable_state(self):
        record = self.env['patient.imaging.test'].search([('id','=',self.env.context.get('active_id'))])
        record.editable_reason = self.editable_reason
        record.action_verified()
        return True