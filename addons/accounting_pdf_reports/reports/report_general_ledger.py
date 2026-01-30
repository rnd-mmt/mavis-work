# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class ReportGeneralLedger(models.AbstractModel):
    _name = 'report.accounting_pdf_reports.report_general_ledger'
    _description = 'General Ledger Report'

    def _get_account_move_entry(self, accounts, init_balance, sortby, display_account):
        """
        :param:
                accounts: the recordset of accounts
                init_balance: boolean value of initial_balance
                sortby: sorting by date or partner and journal
                display_account: type of account(receivable, payable and both)

        Returns a dictionary of accounts with following key and value {
                'code': account code,
                'name': account name,
                'debit': sum of total debit amount,
                'credit': sum of total credit amount,
                'balance': total balance,
                'amount_currency': sum of amount_currency,
                'move_lines': list of move line
        }
        """
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = {x: [] for x in accounts.ids}

        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=self.env.context.get('date_from'), date_to=False, initial_bal=True)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            sql = ("""SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, 0.0 AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
                '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                NULL AS currency_id,\
                '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                '' AS partner_name\
                FROM account_move_line l\
                LEFT JOIN account_move m ON (l.move_id=m.id)\
                LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                JOIN account_journal j ON (l.journal_id=j.id)\
                WHERE l.account_id IN %s""" + filters + ' GROUP BY l.account_id')
            params = (tuple(accounts.ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)

        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = MoveLine._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('''SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,\
            m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name\
            FROM account_move_line l\
            JOIN account_move m ON (l.move_id=m.id)\
            LEFT JOIN res_currency c ON (l.currency_id=c.id)\
            LEFT JOIN res_partner p ON (l.partner_id=p.id)\
            JOIN account_journal j ON (l.journal_id=j.id)\
            JOIN account_account acc ON (l.account_id = acc.id) \
            WHERE l.account_id IN %s ''' + filters + ''' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name ORDER BY ''' + sql_sort)
        params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row.pop('account_id')].append(row)

        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
        return account_res

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))
        init_balance = data['form'].get('initial_balance', True)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in self.env['account.journal'].search([('id', 'in', data['form']['journal_ids'])])]

        accounts = docs if model == 'account.account' else self.env['account.account'].search([])
        accounts_res = self.with_context(data['form'].get('used_context',{}))._get_account_move_entry(accounts, init_balance, sortby, display_account)
        return {
            'doc_ids': docids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Accounts': accounts_res,
            'print_journal': codes,
            # == POUR EXPORT EXCEL ==
            'form' : data['form'],
        }

    # == POUR EXPORT EXCEL ==
    def generate_xlsx(self, data ,workbook ,company_and_currency):
        context = dict(self.env.context) 
        context.update({'active_model': 'account.report.general.ledger'})
        report_general_ledger = self.with_context(context)
        report_data_general_ledger = report_general_ledger._get_report_values(None, data)
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
        format_important_name = workbook.add_format({
            'bg_color': '#D3D3D3',
            'bold': True, 
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12
        })
        currency_format = workbook.add_format({
            'num_format': currency_format_str,
            'align': 'right',
        })
        currency_format_total = workbook.add_format({
            'num_format': currency_format_str,
            'align': 'right',
            'bold': True, 
            'bg_color': '#D3D3D3',
            'font_size': 12
        })

        sheet = workbook.add_worksheet('Grand livre général')
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'}) 

        sheet.set_column('A:A', 52)  # Date
        sheet.set_column('B:B', 20)  # JRNL
        sheet.set_column('C:C', 25)  # Partenaire
        sheet.set_column('D:D', 20)  # Réf
        sheet.set_column('E:E', 35)  # Mouvement
        sheet.set_column('F:F', 30)  # Libellé de l'entrée
        sheet.set_column('G:G', 22)  # Débit
        sheet.set_column('H:H', 22)  # Crédit
        sheet.set_column('I:I', 22)  # Solde
        sheet.set_column('J:J', 22)  # Devise (optionnelle)

        # Write the report title
        sheet.write('A1', f"{report_data_general_ledger['form']['company_id'][1]}: Grand livre général", header_format_h1)
        
        # Write the report header details
        sheet.write('A3', 'Journaux:', header_format)
        sheet.write('B3', ', '.join(report_data_general_ledger['print_journal']), format_important)
        
        sheet.write('A4', 'Afficher le compte:', header_format)
        display_account = {
            'all': 'Tous les comptes',
            'movement': 'Avec mouvements',
            'not_zero': 'Avec solde différent de zéro'
        }.get(report_data_general_ledger['form']['display_account'], '')
        sheet.write('B4', display_account, format_important)
        
        sheet.write('A5', 'Mouvements ciblés:', header_format)
        target_moves = {
            'all': 'Toutes les écritures', 
            'posted': 'Toutes les écritures publiées'
        }.get(report_data_general_ledger['form']['target_move'], '')
        sheet.write('B5', target_moves, format_important)
        
        sheet.write('A6', 'Trié par:', header_format)
        sort_by = {
            'sort_date': 'Date',
            'sort_journal_partner': 'Journal et Partenaire'
        }.get(report_data_general_ledger['form']['sortby'], '')
        sheet.write('B6', sort_by, format_important)
        
        if report_data_general_ledger['form'].get('date_from'):
            sheet.write('A7', 'Date de début:', header_format)
            sheet.write('B7', data['form']['date_from'], date_format)
        
        if report_data_general_ledger['form'].get('date_to'):
            sheet.write('A8', 'Date de fin:', header_format)
            sheet.write('B8', data['form']['date_to'], date_format)

        # Write table headers
        headers = ['Date', 'JRNL', 'Partenaire', 'Réf', 'Mouvement', 'Libellé de l’entrée', 'Débit', 'Crédit', 'Solde', 'Devise']
        for col_num, header in enumerate(headers):
            sheet.write(9, col_num, header, header_format)

        # Write table data
        row_num = 10
        for account in report_data_general_ledger['Accounts']:
            # Write account details
            sheet.merge_range(row_num, 0, row_num, 5, f"{account['code']} {account['name']}", format_important_name)
            sheet.write(row_num, 6, account['debit'], currency_format_total)
            sheet.write(row_num, 7, account['credit'], currency_format_total)
            sheet.write(row_num, 8, account['balance'], currency_format_total)
            row_num += 1

            for line in account['move_lines']:
                sheet.write(row_num, 0, line['ldate'], date_format)
                sheet.write(row_num, 1, line['lcode'])
                sheet.write(row_num, 2, line['partner_name'])
                sheet.write(row_num, 3, line.get('lref', ''))
                sheet.write(row_num, 4, line['move_name'])
                sheet.write(row_num, 5, line['lname'])
                sheet.write(row_num, 6, line['debit'], currency_format)
                sheet.write(row_num, 7, line['credit'], currency_format)
                sheet.write(row_num, 8, line['balance'], currency_format)
                if 'amount_currency' in line and line['amount_currency']:
                    sheet.write(row_num, 9, f"{line['amount_currency']} {line['currency_code']}", currency_format)
                row_num += 1