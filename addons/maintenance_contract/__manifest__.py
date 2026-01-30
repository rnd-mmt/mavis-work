# -*- coding: utf-8 -*-
{
    'name': "Contrat de maintenance",

    'summary': """
        Contrat de
        Maintenance""",

    'description': """
        Monitoring en temps réel pour le Contrat de Maintenance
    """,

    'author': "MMT - RND",
    'website': "https://mmt-mg.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': [
            'base',
            'maintenance',
            'project',
            'hr_timesheet',
            'website_helpdesk_support_ticket',
            'helpdesk_support_ticket_maintenance',
    ],

    'images': ['static/description/icon.png'],

    'data': [
        'security/ir.model.access.csv',
        'data/maintenance_contract_data.xml',

        'views/assets.xml',
        'views/equipment_view.xml',
        'views/intervention_timer.xml',
        'views/maintenance_contract_tree_view.xml',
        'views/maintenance_contract_form_view.xml',
        'views/maintenance_request.xml',
        #'wizard/maintenance_contract_time_sheet_wizard_view.xml'
        'views/maintenance_contract_menu.xml',
        'views/helpdesk_support_view.xml',
        'wizard/maintenance_request_wizard.xml',

    ],
    'qweb': [
        'static/src/xml/donut_chart_widget.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
