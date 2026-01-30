# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountFinancialReport(models.Model):
    _inherit = "account.financial.report"

    @api.depends('parent_id', 'parent_id.level')
    def _get_level(self):
        '''Returns a dictionary with key=the ID of a record and value = the level of this
           record in the tree structure.'''
        for report in self:
            level = 0
            if report.parent_id:
                level = report.parent_id.level + 1
            report.level = level

    code = fields.Char('Code')
    sequence = fields.Integer()
    level = fields.Integer(compute='_get_level', string='Level', store=True)
    formulas = fields.Char()
    domain = fields.Char(default=None)
    hide_if_zero = fields.Boolean(default=False)
    hide_if_empty = fields.Boolean(default=False)
    is_hidden = fields.Boolean(default=False)
    type_financial_report_mg = fields.Selection(string="Type of financial report",
                                                selection=[('balance_sheet', "Active balance sheet"),
                                                           ('balance_cp_p', "Balance Sheet Equity And Liabilities"),
                                                           ('income_statement', "Profit and loss account"),
                                                           ('cash_flow', "Cash flow"),
                                                           ('product_details', "Product details"),
                                                           ('charge_details', "Details of charges")])
    monetary_unit_mg = fields.Boolean(string="Monetary unit", default=False)
    note_mg = fields.Boolean(string="Note", default=False)
    last_year_mg = fields.Boolean(string="N-1", default=False)
    financial_report_id = fields.Many2one('account.financial.report', 'Financial Report')
    children_ids = fields.One2many('account.financial.report', 'parent_id', string='Children')
    type = fields.Selection([
        ('sum', 'View'),
        ('accounts', 'Accounts'),
        ('account_type', 'Account Type'),
        ('account_report', 'Report Value'),
        ('sum_mg', 'View MG'),
        ('report_mg_pl', 'Profit and Loss MG'),
        ('report_mg_cf', 'Cash FLow MG'),
        ('product_details', 'Product details MG'),
        ('charge_details', 'Charge details MG'),
        ('report_mg_cp_p', 'Equity and liabilities MG'),
        ('sum_active', 'Report Active balance Sheet Value'),
    ], 'Type', default='sum')

    green_on_positive = fields.Boolean('Is growth good when positive', default=True)
    is_hidden = fields.Boolean("Hide line in report", default=False)
    groupby = fields.Char("Group by")
    first_parent_id = fields.Many2one('account.financial.report', 'Report name', compute="_get_report_name")

    def _get_report_name(self):
        for report in self:
            rep = report
            while rep.parent_id:
                rep = rep.parent_id
            report.first_parent_id = rep.id
