# -*- coding: utf-8 -*-

from odoo import models, fields

class TypeOfSubject(models.Model):
    _name = 'type.of.subject'
    _description = "Type of Subject"
    
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
   # ticket_type_id = fields.Many2one(
   #     'ticket.type',
   #     string='Type of ticket',
   #     domain="[('company_id', '=', company_id)]",
   #     readonly=False,
        #        readonly=True,
   # )
