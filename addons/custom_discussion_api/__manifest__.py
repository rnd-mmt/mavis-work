{
    'name': 'Custom Discussion API',
    'version': '1.0',
    'depends': [
        'mail',  # Pour utiliser les canaux, messages, etc.
        'bus'    # Pour le temps réel (si nécessaire)
    ],
    'data': [],
    'installable': True,
    'application': False,
}
