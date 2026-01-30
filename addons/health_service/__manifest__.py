# -*- coding: utf-8 -*-
{ 
    'name': 'Service Santé',
    'summary': 'Lister les services à donner aux patients pour faciliter la creation de facture',
    'description': """
        
    """,
    'version': '1.0.0',
    'category': 'Medical',
    'author': 'Harnetprod',
    'support': '',
    'website': '',
    'license': 'OPL-1',
    'depends': ['acs_hms_base', 'acs_hms_document_preview', 'sms'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        'report/health_service_report.xml',
        'report/proforma_report.xml',

        'data/health_service_data.xml',
        'views/health_service_view.xml',
        'views/menu_item.xml',
        'report/report.xml',
        'report/health_service_report.xml',

        'wizard/create_service_view.xml',
        'wizard/price_simulator_wizard_view.xml',
        'wizard/service_line_category_wizard_view.xml',
    ],
    'qweb':[
        'static/src/xml/create_service.xml',
    ],
    'images': [
        'static/description/logo.png',
    ],
    'installable': True,
    'application': True,
    'sequence': 1,
    'price': 61,
    'currency': 'EUR',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: