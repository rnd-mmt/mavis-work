{
    # App information
    'name': 'Inter Company Transfer and Warehouse',
    'version': '14.0.1.0',
    'category': 'Operations/Inventory',
    'license': 'OPL-1',
    'summary': 'Manages Inter Company and Inter Warehouse Transfer along with all required documents with easiest '
               'way by just simple configurations.',

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com/',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    # Dependencies
    'depends': ['delivery', 'purchase_stock', 'barcodes'],
    'external_dependencies': {'python': ['xlrd']},
    'data': [
        'data/ir_sequence.xml',
        'data/ir_cron.xml',

        'security/inter_company_transfer_security.xml',
        'security/ir.model.access.csv',

        'wizards/reverse_inter_company_transfer_ept.xml',
        'wizards/import_export_products_ept.xml',

        'views/inter_company_transfer_ept.xml',
        'views/inter_company_transfer_config_ept.xml',
        'views/inter_company_transfer_log_book_ept.xml',
        'views/inter_company_transfer_log_line_ept.xml',
        'views/account_move.xml',
        'views/purchase.xml',
        'views/res_company.xml',
        'views/sale.xml',
        'views/stock_picking.xml',
        'views/stock_warehouse.xml',
    ],

    # Odoo Store Specific
    'images': ['static/description/Inter-Company-Transfer-cover.png'],

    # Technical
    'post_init_hook': 'post_init_update_rule',
    'uninstall_hook': 'uninstall_hook_update_rule',
    'live_test_url': 'https://www.emiprotechnologies.com/free-trial?app=inter-company-transfer-ept&version=14&edition'
                     '=enterprise',
    'active': True,
    'installable': True,
    'currency': 'EUR',
    'price': 149.00,
    'auto_install': False,
    'application': True,
}
