# -*- coding: utf-8 -*-
{
    'name': "l10n mg pdf report",
    'summary': """
        l10n mg report for odoo community
        """,
    'description': """
        This module allows to report useful accounts for the Malagasy accounting in PDF and Excel format
    """,
    'author': "eTech Consulting",
    'website': "http://www.etechconsulting-mg.com",
    'license': 'AGPL-3',
    'category': 'Accounting/Accounting',
    'version': '14.0.1.0.0',
    'depends': [
        'base',
        'l10n_mg',
        'om_account_accountant',
        'accounting_pdf_reports',
        'account',
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/report_mg_view.xml',
        'views/view_button.xml',
        'data/balance_sheet_active.xml',
        'data/profit_and_loss_mg.xml',
        'data/balance_sheet_equity_and_liabilities.xml',
        'data/account_produits_details.xml',
        'data/account_charges_details.xml',
        'data/account_result_nature_view.xml',
        'data/account_result_fonction_view.xml',
        # 'data/direct_cash_flow_mg.xml',
        # 'data/indirect_cash_flow_mg.xml',
        'wizard/cash_flow_wizard_view.xml',
        'views/direct_cash_flow_template.xml',
        'views/indirect_cash_flow_template.xml',
        'views/account_reports_settings.xml',
        'views/pdf_template.xml',
        'views/account_report_view.xml',
        'views/evcp_view.xml',
        'views/evcp_template.xml',
        'views/action_manager.xml',
        'views/report_invoice.xml',
        'report/report.xml',

    ],
    'qweb': ['views/hide_button.xml', ],
    'demo': [],
}
