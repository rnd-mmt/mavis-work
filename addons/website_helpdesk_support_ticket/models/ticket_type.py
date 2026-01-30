# -*- coding: utf-8 -*-

from odoo import models, fields

class TicketType(models.Model):
    _name = 'ticket.type'
    _description = "Ticket Type"
    
    name = fields.Char(
        'Name',
        required=True,
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.user.company_id,
        string='Company',
        readonly=False,
        #        readonly=True,
    )
    subject_type_id = fields.Many2one(
        'type.of.subject',
        domain="[('company_id', '=', company_id)]",
        string="Type of Subject",
        copy=True,
    )
