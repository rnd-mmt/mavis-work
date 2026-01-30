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

{
    'name': "PITS Firebase Cloud Message Notifications",

    'summary': """
        This module will generate Firebase Cloud Message Notifications""",
    'author': "PIT Solutions AG",
    'website': "https://www.pitsolutions.ch",
    'category': 'Extra Tools',
    'version': '14.0.0.1.0',
    'currency': 'EUR',
    'price': 50,
    'license' : 'OPL-1',
    'depends': ['base_setup'],
    'external_dependencies': {
        'python': ['pyfcm']
    },
    'data': [
        'security/ir.model.access.csv',
        'data/fcm_data.xml',
        'views/fcm_test_view.xml',
        'views/res_partner_view.xml',
        'views/fcm_config_view.xml',
    ],
    'images': [
        'static/description/banner.png'
    ]
}
