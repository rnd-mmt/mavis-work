# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class ReportPartnerLedger(models.AbstractModel):
    _name = 'report.accounting_pdf_reports.report_partnerledger'
    _description = 'Partner Ledger Report'

    def _lines(self, data, partner):
        full_account = []
        currency = self.env['res.currency']
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        params = [partner.id, tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]
        query = """
            SELECT "account_move_line".id, "account_move_line".date, j.code, acc.code as a_code, acc.name as a_name, "account_move_line".ref, m.name as move_name, "account_move_line".name, "account_move_line".debit, "account_move_line".credit, "account_move_line".amount_currency,"account_move_line".currency_id, c.symbol AS currency_code
            FROM """ + query_get_data[0] + """
            LEFT JOIN account_journal j ON ("account_move_line".journal_id = j.id)
            LEFT JOIN account_account acc ON ("account_move_line".account_id = acc.id)
            LEFT JOIN res_currency c ON ("account_move_line".currency_id=c.id)
            LEFT JOIN account_move m ON (m.id="account_move_line".move_id)
            WHERE "account_move_line".partner_id = %s
                AND m.state IN %s
                AND "account_move_line".account_id IN %s AND """ + query_get_data[1] + reconcile_clause + """
                ORDER BY "account_move_line".date"""
        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()
        sum = 0.0
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        for r in res:
            r['date'] = r['date']
            r['displayed_name'] = '-'.join(
                r[field_name] for field_name in ('move_name', 'ref', 'name')
                if r[field_name] not in (None, '', '/')
            )
            sum += r['debit'] - r['credit']
            r['progress'] = sum
            r['currency_id'] = currency.browse(r.get('currency_id'))
            full_account.append(r)
        return full_account

    def _sum_partner(self, data, partner, field):
        if field not in ['debit', 'credit', 'debit - credit']:
            return
        result = 0.0
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '

        params = [partner.id, tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]
        query = """SELECT sum(""" + field + """)
                FROM """ + query_get_data[0] + """, account_move AS m
                WHERE "account_move_line".partner_id = %s
                    AND m.id = "account_move_line".move_id
                    AND m.state IN %s
                    AND account_id IN %s
                    AND """ + query_get_data[1] + reconcile_clause
        self.env.cr.execute(query, tuple(params))

        contemp = self.env.cr.fetchone()
        if contemp is not None:
            result = contemp[0] or 0.0
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        data['computed'] = {}

        obj_partner = self.env['res.partner']
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            data['computed']['move_state'] = ['posted']
        result_selection = data['form'].get('result_selection', 'customer')
        if result_selection == 'supplier':
            data['computed']['ACCOUNT_TYPE'] = ['payable']
        elif result_selection == 'customer':
            data['computed']['ACCOUNT_TYPE'] = ['receivable']
        else:
            data['computed']['ACCOUNT_TYPE'] = ['payable', 'receivable']

        self.env.cr.execute("""
            SELECT a.id
            FROM account_account a
            WHERE a.internal_type IN %s
            AND NOT a.deprecated""", (tuple(data['computed']['ACCOUNT_TYPE']),))
        data['computed']['account_ids'] = [a for (a,) in self.env.cr.fetchall()]
        params = [tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        query = """
            SELECT DISTINCT "account_move_line".partner_id
            FROM """ + query_get_data[0] + """, account_account AS account, account_move AS am
            WHERE "account_move_line".partner_id IS NOT NULL
                AND "account_move_line".account_id = account.id
                AND am.id = "account_move_line".move_id
                AND am.state IN %s
                AND "account_move_line".account_id IN %s
                AND NOT account.deprecated
                AND """ + query_get_data[1] + reconcile_clause
        self.env.cr.execute(query, tuple(params))
        partner_ids = [res['partner_id'] for res in self.env.cr.dictfetchall()]
        partners = obj_partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.ref or '', x.name or ''))

        return {
            'doc_ids': partner_ids,
            'doc_model': self.env['res.partner'],
            'data': data,
            'docs': partners,
            'time': time,
            'lines': self._lines,
            'sum_partner': self._sum_partner,
            # == POUR EXPORT EXCEL ==
            'form' : data['form'],
        }

    # == TEMPLATE POUR EXPORT EXCEL ==
    # == A APPELER DANS l10n_mg_reports_c
    @api.model
    def generate_xlsx(self, data ,workbook,company_and_currency):
        report_partner = self
        report_data_partner = report_partner._get_report_values(None, data)
        company = company_and_currency['company']
        currency_format_str = company_and_currency['currency']

        # Define formats
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
                'bold': True, 
                'font_size': 12
            })
        
        # Create a worksheet
        sheet = workbook.add_worksheet('Grand livres des partenaires')
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'}) 
        # Set column widths
        sheet.set_column('A:A', 52)
        sheet.set_column('B:B', 32)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 80)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 15)
        sheet.set_column('H:H', 15)
        
        # Write the report title
        sheet.write('A1', 'Grand livre des Tiers', header_format_h1)
        
        # Write the report header details
        sheet.write('A3', 'Entreprise:', header_format)
        sheet.write('B3', report_data_partner['form']['company_id'][1] , format_important)
            
        if data['form'].get('date_from'):
            sheet.write('A4', 'Date  debut :', header_format)
            sheet.write('B4', report_data_partner['form']['date_from'] , date_format)
            
        if data['form'].get('date_to'):
            sheet.write('A5', 'Date fin:', header_format)
            sheet.write('B5', report_data_partner['form']['date_to'] , date_format)

        sheet.write('A6', 'Déplacements cibles:', header_format)
        target_moves = {
                'all': 'Toutes les écritures', 
                'posted': 'Toutes les écritures publiées'
            }.get(report_data_partner['form']['target_move'], '')
        sheet.write('B6', target_moves ,  format_important)
        
            # Write table headers
        headers = ['Date', 'JRNL', 'Compte', 'Ref', 'Débit', 'Crédit', 'Équilibre']
        for col_num, header in enumerate(headers):
            sheet.write(7, col_num, header, header_format)

            # Write table data
        row_num = 8
        for partner in report_data_partner['docs']:
                # Write partner details
            sheet.merge_range(row_num, 0, row_num, 3, partner.name or '' , format_important_name)
            partner_debit = report_data_partner['sum_partner'](report_data_partner['data'], partner, 'debit')
            partner_credit = report_data_partner['sum_partner'](report_data_partner['data'], partner, 'credit')
            partner_balance = partner_debit - partner_credit
            sheet.write(row_num, 4, partner_debit, currency_format_total)
            sheet.write(row_num, 5, partner_credit, currency_format_total)
            sheet.write(row_num, 6, partner_balance, currency_format_total)
            row_num += 1

            for line in report_data_partner['lines'](report_data_partner['data'], partner):
                sheet.write(row_num, 0, line.get('date', '') , date_format)
                sheet.write(row_num, 1, line.get('code', ''))
                sheet.write(row_num, 2, line.get('a_code', ''))
                sheet.write(row_num, 3, line.get('displayed_name', ''))
                sheet.write(row_num, 4, line.get('debit', 0.0), currency_format)
                sheet.write(row_num, 5, line.get('credit', 0.0), currency_format)
                sheet.write(row_num, 6, line.get('progress', 0.0), currency_format)
                if data['form'].get('amount_currency') and line.get('currency_id'):
                    sheet.write(row_num, 7, line.get('amount_currency', 0.0), currency_format)
                row_num += 1