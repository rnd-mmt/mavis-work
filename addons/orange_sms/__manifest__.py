# -*- coding: utf-8 -*-

{
    "name": "Orange SMS",
    "summary": "Send SMS using Orange SMS Gateway, overwriting the default Odoo IAP SMS.",
    "description": """
    This module is used to overwrite the Odoo default SMS IAP with the Orange SMS.
    
    To Configure:
        * Go to the Settings > General Settings. 
        * Search for SMS Settings.
        * Add the Orange Details like: Auth Token, Number From.
        * Overwrite Odoo SMS if check then system will use Orange SMS Settings, if not then Odoo SMS IAP. 
    """,
    "version": "14.0.0.1",
    "category": "Extra Tools",
    "website": "https://polyline.xyz",
    "author": "Ahmed Mnasri",
    "url": "https://www.polyline.xyz",
    "price": 65,
    "currency": 'EUR',
    'license': 'OPL-1',
    "depends": [
        'sms',
    ],
    "data": [
        'views/configuration.xml',
        'views/sms_view.xml',
    ],
    "application": False,
    "installable": True,
    "active": True,
    "live_test_url": 'https://youtu.be/qGV3vOg7yfk',
    "images": ['static/description/Banner.gif']
}
