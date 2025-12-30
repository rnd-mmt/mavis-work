{
    'name': 'Notifications FCM et Automatisation',
    'version': '1.0.0',
    'summary': 'Notifications push mobiles et automatisation des actions',
    'description': '''
        Module combiné gérant :
        1. Notifications FCM pour mobile
        2. Automatisation des notifications métier
        3. Intégration complète avec les modèles Odoo
    ''',
    'depends': ['base', 'mail', 'sale'],
    'external_dependencies': {
        'python': ['pyjwt', 'requests']
    },
    'data': [
        'data/mail_activity_type_fcm.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
