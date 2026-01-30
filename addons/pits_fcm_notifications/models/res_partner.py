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
from pyfcm import FCMNotification
from odoo.exceptions import UserError


import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    fcm_token_ids = fields.One2many('fcm.device.token', 'partner_id', 'FCM Tokens')

    
    # partner.generate_fcm_notification(message_title='Title',message_body='Messege Body')
    def generate_fcm_notification(self,message_title=None,message_body=None):
        if not message_title:
            raise UserError(_("Messege Title can't be blank"))
        if not message_body:
            raise UserError(_("Messege Body can't be blank"))
        registration_ids = []
        for partner in self:
            registration_ids = partner.fcm_token_ids.mapped('token')
            if registration_ids:
                fcm_server_key = self.env['ir.config_parameter'].sudo().get_param('pits_fcm_notifications.fcm_server_key')
                if not fcm_server_key:
                    return False
                push_service = FCMNotification(api_key=fcm_server_key)
                _logger.info("Generating FCM Notification")
                try:
                    result = push_service.notify_multiple_devices(registration_ids=registration_ids, message_title=message_title, message_body=message_body)
                    _logger.info(result)
                except Exception as e:
                    _logger.info("Error while generating FCM Notification. %s" % (e,))
        return True





class FCMDeviceToken(models.Model):
    _name = 'fcm.device.token'

    token = fields.Char('Token', required=True)
    partner_id = fields.Many2one('res.partner', 'Partner')




    
