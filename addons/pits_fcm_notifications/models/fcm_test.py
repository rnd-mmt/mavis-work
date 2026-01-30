# -*- coding: utf-8 -*-
# Part of PIT Solutions AG. See LICENSE file for full copyright and licensing details.
#################################################################################
# Author      : PIT Solutions AG. (<https://www.pitsolutions.ch/>)
# Copyright(c): 2019 - Present PIT Solutions AG.
# License     : See LICENSE file for full copyright and licensing details.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.odoo.com/documentation/user/12.0/legal/licenses/licenses.html#odoo-apps>
#################################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from pyfcm import FCMNotification
from odoo.exceptions import UserError



class FCMTest(models.Model):
    _name = "fcm.test"
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', 'Partner')
    message_title = fields.Char('Message Title')
    message_body = fields.Text('Message Body')

    def test_fcm(self):
        self.ensure_one()
        self.partner_id.sudo().generate_fcm_notification(message_title=self.message_title,
                                                            message_body=self.message_body)
