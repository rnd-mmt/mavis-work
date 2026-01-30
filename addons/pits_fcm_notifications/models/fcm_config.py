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



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    fcm_server_key = fields.Char('Server Key')


    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        param.set_param('pits_fcm_notifications.fcm_server_key', self.fcm_server_key)
        return res

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update({
            'fcm_server_key': params.get_param('pits_fcm_notifications.fcm_server_key', ''),
        })
        return res