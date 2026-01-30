# -*- coding: utf-8 -*-

from odoo import models, fields


# class HrEmployeePublic(models.Model):
#     _inherit = "hr.employee.public"

#     dest_location_id = fields.Many2one(
#         'stock.location',
#         string='Destination Location',
#     )

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    dest_location_id = fields.Many2one(
        'stock.location',
        string='Emplacement de destination',
        groups='hr.group_hr_user'
    )
    signature = fields.Binary('Signature')

class ResUsers(models.Model):
    _inherit = "res.users"

    signature = fields.Binary('Signature')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
