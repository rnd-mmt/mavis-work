# -*- coding: utf-8 -*-
{
    'name': "Journal Entry Import",

    'summary': """
            Journal Entry Import tools
        """,

    'description': """
        After JE import, uninstall this module
    """,

    'author': "Etechconsulting-mg",
    'website': "http://www.etechconsulting-mg.com",

    'category': 'Uncategorized',
    'version': '0.1',

    
    'depends': ['base','account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_move_views.xml',
    ],
    
    'demo': [
        'demo/demo.xml',
    ],
}
