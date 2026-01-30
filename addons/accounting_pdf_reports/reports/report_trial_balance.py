# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError
#== POUR EXPORT EXCEL ==
import json
from odoo.tools import date_utils


class ReportTrialBalance(models.AbstractModel):
    _name = 'report.accounting_pdf_reports.report_trialbalance'
    _description = 'Trial Balance Report'


    def _get_accounts(self, accounts, display_account):
        """ compute the balance, debit and credit for the provided accounts
            :Arguments:
                `accounts`: list of accounts record,
                `display_account`: it's used to display either all accounts or those accounts which balance is > 0
            :Returns a list of dictionary of Accounts with following key and value
                `name`: Account name,
                `code`: Account code,
                `credit`: total amount of credit,
                `debit`: total amount of debit,
                `balance`: total amount of balance,
        """

        account_result = {}
        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        tables = tables.replace('"','')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        # compute the balance, debit and credit for the provided accounts
        request = ("SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" +\
                   " FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id")
        params = (tuple(accounts.ids),) + tuple(where_params)
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row

        account_res = []
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            if account.id in account_result:
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = account_result[account.id].get('balance')
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
            if display_account == 'movement' and (not currency.is_zero(res['debit']) or not currency.is_zero(res['credit'])):
                account_res.append(res)
        return account_res

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))
        display_account = data['form'].get('display_account')
        accounts = docs if model == 'account.account' else self.env['account.account'].search([])
        account_res = self.with_context(data['form'].get('used_context'))._get_accounts(accounts, display_account)
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Accounts': account_res,
            # == POUR EXPORT EXCEL ==
            'form' : data['form'],
        }

    #==POUR EXPORT EXCEL ==
    def generate_xlsx(self, data, workbook ,company_and_currency):
        context = dict(self.env.context) 
        context.update({'active_model': 'account.balance.report'})
        report_data_partner = self.with_context(context)._get_report_values(None, data)
        company = company_and_currency['company']
        currency_format_str = company_and_currency['currency']
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#87CEEB',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        header_format_h1 = workbook.add_format({
            'bold': True,
            'bg_color': '#87CEEB',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 16
        })
        
        format_important = workbook.add_format({
            'bold': True,
            'align': 'left',
            'valign': 'vcenter',
        })
        
        
        currency_format = workbook.add_format({
            'num_format':  currency_format_str,
            'align': 'right',
        })
        sheet = workbook.add_worksheet('Bilan')
        sheet.set_column('A:A', 55)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 25)
        sheet.set_column('D:D', 25)
        sheet.set_column('E:E', 25)
        
        sheet.write('A1', f'{company.name}: Balance de vérification', header_format_h1)
        row_num = 3
        
        sheet.write(row_num, 0, 'Afficher le compte :', header_format)
        display_account = {
            'all': 'Tous les comptes',
            'movement': 'Avec mouvements',
            'not_zero': 'Avec solde non nul'
        }.get(report_data_partner['form']['display_account'], '')
        sheet.write(row_num, 1, display_account, format_important)
        
        row_num += 1
        if report_data_partner['form'].get('date_from'):
            sheet.write(row_num, 0, 'Date de :', header_format)
            sheet.write(row_num, 1, report_data_partner['form']['date_from'], workbook.add_format({'num_format': 'dd/mm/yyyy'}))
        
        row_num += 1
        if report_data_partner['form'].get('date_to'):
            sheet.write(row_num, 0, 'Date à :', header_format)
            sheet.write(row_num, 1, report_data_partner['form']['date_to'], workbook.add_format({'num_format': 'dd/mm/yyyy'}))
        
        row_num += 1
        sheet.write(row_num, 0, 'Mouvements cibles :', header_format)
        target_moves = {
            'all': 'Toutes les écritures',
            'posted': 'Toutes les écritures publiées'
        }.get(report_data_partner['form']['target_move'], '')
        sheet.write(row_num, 1, target_moves, format_important)

        row_num += 2
        headers = ['Code', 'Compte', 'Débit', 'Crédit', 'Solde']
        for col_num, header in enumerate(headers):
            sheet.write(row_num, col_num, header, header_format)

        row_num += 1
        accounts = report_data_partner.get('Accounts', [])
        
        for account in accounts:
            sheet.write(row_num, 0, account.get('code', ''))
            sheet.write(row_num, 1, account.get('name', ''))
            sheet.write(row_num, 2, account.get('debit', 0.0), currency_format)
            sheet.write(row_num, 3, account.get('credit', 0.0), currency_format)
            sheet.write(row_num, 4, account.get('balance', 0.0), currency_format)
            row_num += 1