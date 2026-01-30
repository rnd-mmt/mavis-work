# -*- coding: utf-8 -*-

{
    'name': 'Gestionnaire de commission prestataire',
    'category': 'Medical',
    'summary': 'Option permettant de donner une commission à un prestataire',
    'description': """
        
    """,
    'version': '1.0.0',
    'author': 'Harnetprod',
    'support': 'rabemanoela@gmail.com',
    'website': '',
    'license': 'OPL-1',
    'depends': ['acs_hms'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'wizard/commission_make_invoice_views.xml',
        'reports/commission_sheet_report.xml',
        'views/commission_view.xml',
        'views/commission_sheet_view.xml',
        'views/hms_base_view.xml',
        'views/res_config_settings_views.xml',
        'views/account_view.xml',
        'views/menu_item.xml',
    ],
    'images': [
        'static/description/hms_commission_almightycs_cover.jpg',
    ],
    'installable': True,
    'application': True,
    'sequence': 1,
    'price': 50,
    'currency': 'EUR',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: