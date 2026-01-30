# -*- coding: utf-8 -*-

import io
import json

from odoo.exceptions import ValidationError
from odoo.tools import date_utils

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

from odoo import fields, models, api, _
import time


class AccountingReport(models.TransientModel):
    _inherit = "accounting.report"

    type_financial_report_mg = fields.Selection(string="Type of financial report",
                                                selection=[('balance_sheet', "Active balance sheet"),
                                                           ('balance_cp_p', "Balance Sheet Equity And Liabilities"),
                                                           ('income_statement', "Profit and loss account"),
                                                           ('cash_flow', "Cash flow"),
                                                           ('product_details', "Product details"),
                                                           ('charge_details', 'Details of charges')])

    @api.onchange('account_report_id')
    def change_account_report(self):
        if self.account_report_id:
            self.type_financial_report_mg = self.account_report_id.type_financial_report_mg

    @api.onchange('enable_filter')
    def change_debit_credit(self):
        if self.enable_filter:
            self.debit_credit = False

    def check_report(self):
        res = super(AccountingReport, self).check_report()
        data = {}
        data['form'] = self.read(
            ['account_report_id', 'date_from_cmp', 'date_to_cmp', 'journal_ids', 'filter_cmp', 'target_move',
             'type_financial_report_mg'])[0]
        for field in ['account_report_id']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        comparison_context = self._build_comparison_context(data)
        res['data']['form']['comparison_context'] = comparison_context
        return res

    def _print_report(self, data):
        data['form'].update(self.read(
            ['date_from_cmp', 'debit_credit', 'date_to_cmp', 'filter_cmp', 'account_report_id', 'enable_filter',
             'label_filter', 'target_move', 'type_financial_report_mg'])[0])
        report_financial_type = data['form']['type_financial_report_mg']
        print(report_financial_type)
        if report_financial_type == 'balance_sheet':
            self.env.ref('accounting_pdf_reports.action_report_financial').name = "Bilan actif"
        elif report_financial_type == 'balance_cp_p':
            self.env.ref('accounting_pdf_reports.action_report_financial').name = "Bilan capitaux propres et passif"
        elif report_financial_type=='income_statement':
            self.env.ref('accounting_pdf_reports.action_report_financial').name = "Compte de résultat"
        return self.env.ref('accounting_pdf_reports.action_report_financial').report_action(self, data=data,
                                                                                                config=False)


    def _create_comparison_context(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data and data['journal_ids'] or False
        result['state'] = 'target_move' in data and data['target_move'] or ''
        if data['filter_cmp'] == 'filter_date':
            result['date_from'] = data['date_from_cmp']
            result['date_to'] = data['date_to_cmp']
            result['strict_range'] = True
        return result

    def print_xlsx(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('Start Date must be less than End Date'))
        data = self.check_report()['data']['form']
        data.update(self.read(
            ['date_from_cmp', 'debit_credit', 'date_to_cmp', 'filter_cmp', 'account_report_id', 'enable_filter',
             'label_filter', 'target_move', 'type_financial_report_mg'])[0])
        return {
            'data': {'model': 'accounting.report',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': self.account_report_id.name,
                     },
            'report_type': 'xlsx',
        }

    def get_currency_and_company(self, data):
        company = self.env['res.company'].search([('id', '=', data['form']['company_id'][0])], limit=1)
        currency = company.currency_id
        currency_symbol = currency.symbol or ''
        currency_format = currency.position or 'before'
        currency_format_str = '#,##0.00'
        if currency_format == 'after':
            currency_format_str += f' "{currency_symbol}"'
        else:
            currency_format_str = f'"{currency_symbol}" ' + currency_format_str
        return {'company':company, 'currency' : currency_format_str}

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        #sheet = workbook.add_worksheet()
        ##################################
        bold = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'bold': True, 'bottom': 1, 'font_color': '#212529'})
        bold_title_center = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'align': 'center', 'font_size': 12, 'bottom': 2})
        cell_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12})
        cell_style_bottom = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'bottom': 2})
        title_style_level1 = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#212529', 'indent': 1, 'bold': True})
        cell_style_level1 = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#212529', 'bold': True})
        title_style_level2 = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'font_color': '#343A40', 'indent': 2, 'bold': True})
        cell_style_level2 = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 11, 'font_color': '#343A40', 'bold': True})
        title_style_level3 = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'font_color': '#495057', 'indent': 3, 'bold': True})
        cell_style_level3 = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'font_color': '#495057', 'bold': True})
        
        #== EXPORT DGI RAPORT FISCAL ==
        if data.get('form', {}).get('report_tax'):
            tax_report = self.env['report.accounting_pdf_reports.report_tax']
            company_and_currency =self.get_currency_and_company(data)
            tax_report.generate_xlsx( data , workbook , company_and_currency )
        #== EXPORT SOLDE DE BALANCE AGEE ==
        if data.get('form', {}).get('report_aged_partner'):
            ager_partner_report = self.env['report.accounting_pdf_reports.report_agedpartnerbalance']
            company_and_currency =self.get_currency_and_company(data)
            ager_partner_report.generate_xlsx( data , workbook , company_and_currency )
        #== EXPORT POUR GRAND LIVRE GENERAL ===
        if data.get('form', {}).get('report_general_ledger_name'):
            company_and_currency =self.get_currency_and_company(data)
            general_ledger_report = self.env['report.accounting_pdf_reports.report_general_ledger']
            general_ledger_report.generate_xlsx( data ,workbook , company_and_currency)
        #== EXPORT POUR BALANCE DE VERIFICATION======
        if data.get('form', {}).get('report_trial_balance_name'):
            trial_balance_report = self.env['report.accounting_pdf_reports.report_trialbalance']
            company_and_currency =self.get_currency_and_company(data)
            trial_balance_report.generate_xlsx( data ,workbook , company_and_currency )
        # == EXPORT POUR GRAND LIVRE DES TIERS ==
        if data.get('form', {}).get('report_partner_ledger_name'):
            report_partner = self.env['report.accounting_pdf_reports.report_partnerledger']
            company_and_currency =self.get_currency_and_company(data)
            report_partner.generate_xlsx( data ,workbook, company_and_currency)
        #=====AUDIT DES JOURNAUX POUR EXPORT EXCEL=========
        if data.get('form', {}).get('report_journal_name'):
            report_journal = self.env['report.accounting_pdf_reports.report_journal']
            report_data = report_journal._get_report_values(None,data)
            print("audiiiiiiiiiiiiiiiiiiiiiiiiiiiiii",report_data , "repoterd" , data.get('form', {}).get('report_journal_name') ,data.get('report_journal_name') , data , response)
            print('Excel printed')

            # Create an Excel file in memory
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
           
            journal_records = self.env['account.journal'].browse(data['form']['journal_ids'])
            for journal_id, journal in enumerate(journal_records):
                # Define formats
                sheet = workbook.add_worksheet(journal.name)
                header_format = workbook.add_format({
                        'bold': True, 
                        'bg_color': '#87CEEB', 
                        'border': 1,
                        'align': 'center',  
                        'valign': 'vcenter' 
                    })
                currency_format = workbook.add_format({'num_format': '#,##0.00'})
                date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'}) #date format

                # Set column widths
                sheet.set_column('A:A', 22)
                sheet.set_column('B:B', 22)
                sheet.set_column('C:C', 15)
                sheet.set_column('D:D', 15)
                sheet.set_column('E:E', 20)
                sheet.set_column('F:F', 15)
                sheet.set_column('G:G', 15)
                if report_data['form']['amount_currency']:
                    sheet.set_column('H:H', 15)

                # Write the report title
                sheet.write('A1', ' Journal ' +  journal['name'], header_format)

                # Write the report header details
                sheet.write('A3', 'Company:', header_format)
                sheet.write('B3', journal.company_id.name)
                sheet.write('A4', 'Journal:', header_format)
                sheet.write('B4', journal['name'])
                sheet.write('A5', 'Entrées triées par:', header_format)
                sheet.write('B5', 'Numéro de l\'écriture' if report_data['form'].get('sort_selection') != 'date' else 'Date')
                sheet.write('A6', 'Mouvements cibles:', header_format)
                sheet.write('B6', 'Toutes les écritures' if report_data['form'].get('target_move') == 'all' else 'Toutes les écritures publiées')  

                # Write table headers
                headers = ['Mouvement', 'Date', 'Compte', 'Partenaire', 'Libellé', 'Débit', 'Crédit']
                if report_data['form']['amount_currency']:
                    headers.append('Currency')

                for col_num, header in enumerate(headers):
                    sheet.write(8, col_num, header, header_format)

                # Write table data
                row_num = 9
                
                journal_lines = report_data['lines'].get(journal.id, [])
                print(f"Writing data for journal: {journal.name}")
                print("Journal Lines:", journal_lines)
                for aml in journal_lines:
                    sheet.write(row_num, 0, aml.move_id.name if aml.move_id.name != '/' else '*' + str(aml.move_id.id))
                    sheet.write(row_num, 1, aml.date, date_format)
                    sheet.write(row_num, 2, aml.account_id.code)
                    sheet.write(row_num, 3, aml.partner_id.name[:23] if aml.partner_id else '')
                    sheet.write(row_num, 4, aml.name[:35] if aml.name else '')
                    sheet.write(row_num, 5, aml.debit, currency_format)
                    sheet.write(row_num, 6, aml.credit, currency_format)
                    if report_data['form']['amount_currency'] and aml.amount_currency:
                        sheet.write(row_num, 7, aml.amount_currency, currency_format)
                    row_num += 1

                # Write totals
                sheet.write(row_num + 2, 4, 'Total', header_format)
                sheet.write(row_num + 2, 5, report_journal._sum_debit(report_data, journal), currency_format)
                sheet.write(row_num + 2, 6, report_journal._sum_credit(report_data, journal), currency_format)

                # Write tax declarations
                row_num += 5
                sheet.write(row_num, 0, 'Déclaration de taxes', header_format)
                tax_headers = ['Nom', 'Montant de base', 'Montant de la taxe']
                for col_num, header in enumerate(tax_headers):
                    sheet.write(row_num + 1, col_num, header, header_format)

                row_num += 2
                taxes = report_journal._get_taxes(data, journal)
                print("taxesssssssssssssss" , taxes)
                for tax_record, tax_data in taxes.items():
                    tax_name = tax_record.name  # Access the name directly from the tax record
                    sheet.write(row_num, 0, tax_name if tax_name else 'No Name')
                    sheet.write(row_num, 1, tax_data['base_amount'], currency_format)
                    sheet.write(row_num, 2, tax_data['tax_amount'], currency_format)
                    row_num += 1

        # Bilan passif
        
        if data.get('account_report_id'):
            report = self.env['report.accounting_pdf_reports.report_financial']
            results = report.get_account_lines(data)
            report = self.env['account.financial.report'].browse(data.get('account_report_id')[0])
            if report.type in ['sum_mg', 'cash_flow']:
                sheet = workbook.add_worksheet("Bilan passif")
                sheet.set_column('A:A', 70)
                sheet.set_column('B:B', 15)
                sheet.set_column('C:C', 15)
                sheet.set_column('D:D', 15)
                if data.get('enable_filter', False):
                    sheet.write('B1', '%s Net' % time.strftime('%Y'), bold_title_center)
                    sheet.write('C1', data.get('label_filter'), bold_title_center)
                elif data.get('debit_credit', False):
                    sheet.write('B1', 'Debit', bold_title_center)
                    sheet.write('C1', 'Credit', bold_title_center)
                    sheet.write('D1', '%s Net' % time.strftime('%Y'), bold_title_center)
                else:
                    sheet.write('B1', '%s Net' % time.strftime('%Y'), bold_title_center)
                i = 2
                for vals in results:
                    level = int(vals.get('level', 0))
                    if level == 0:
                        style = bold
                        col_style = bold
                    elif level == 2:
                        style = title_style_level2
                        col_style = cell_style_level2
                    elif level == 3:
                        style = title_style_level3
                        col_style = cell_style_level3
                    else:
                        style = bold
                        col_style = bold
                    sheet.write('A' + str(i), vals['name'],style)
                    if data.get('enable_filter', False):
                        if not vals.get('hidden', False) :
                            sheet.write('B' + str(i), vals['balance'],col_style)
                            sheet.write('C' + str(i), vals['balance_cmp'], col_style)
                        elif vals.get('hidden', False) and level== 0 :
                            sheet.write('B' + str(i), "", col_style)
                            sheet.write('C' + str(i), "", col_style)
                    elif data.get('debit_credit', False):
                        if not vals.get('hidden', False) :
                            sheet.write('B' + str(i), vals['debit'], col_style)
                            sheet.write('C' + str(i), vals['credit'], col_style)
                            sheet.write('D' + str(i), vals['balance'], col_style)
                        elif vals.get('hidden', False) and level== 0:
                            sheet.write('B' + str(i), "", col_style)
                            sheet.write('C' + str(i), "", col_style)
                            sheet.write('D' + str(i), "", col_style)

                    else:
                        if not vals.get('hidden', False):
                            sheet.write('B' + str(i), vals['balance'], col_style)
                        elif vals.get('hidden', False) and level == 0:
                            sheet.write('B' + str(i), "", col_style)
                    i += 1

            # Bilan actif
            row = 2
            if data.get('type_financial_report_mg') == 'balance_sheet':
                sheet = workbook.add_worksheet("Bilan actif")
                sheet.write('A1', "Name", bold_title_center)
                sheet.write('B1', 'Brut', bold_title_center)
                sheet.write('C1', 'Amorti', bold_title_center)
                sheet.write('D1', 'Net', bold_title_center)
                if data.get('enable_filter'):
                    sheet.write('E1', data.get('label_filter'), bold_title_center)
                    sheet.set_column('E:E', 15)
                sheet.set_column('A:A', 70)
                sheet.set_column('B:B', 15)
                sheet.set_column('C:C', 15)
                sheet.set_column('D:D', 15)
                for line in results:
                    if not line.get('type') == 'account':
                        if line.get('hidden'):
                            sheet.write('A' + str(row), line['name'], bold)
                            sheet.write('B' + str(row), "", bold)
                            sheet.write('C' + str(row), "", bold)
                            sheet.write('D' + str(row), "", bold)
                            if data.get('enable_filter'):
                                sheet.write('E' + str(row), "", bold)
                        elif row in [4, 5, 9, 14, 15, 16, 24, 30, 34]:
                            sheet.write('A' + str(row), line['name'], title_style_level1)
                            sheet.write('B' + str(row), line.get('brut'), cell_style_level1)
                            sheet.write('C' + str(row), line.get('amorti'), cell_style_level1)
                            sheet.write('D' + str(row), line.get('net'), cell_style_level1)
                            if data.get('enable_filter'):
                                sheet.write('E' + str(row), line.get('balance_cmp'), cell_style_level1)
                        elif row in [6, 7, 8, 10, 11, 12, 13, 17, 18, 19, 20, 21, 25, 26, 27, 28, 29, 31, 32,33,35, 36]:
                            sheet.write('A' + str(row), line['name'], title_style_level2)
                            sheet.write('B' + str(row), line.get('brut'), cell_style_level2)
                            sheet.write('C' + str(row), line.get('amorti'), cell_style_level2)
                            sheet.write('D' + str(row), line.get('net'), cell_style_level2)
                            if data.get('enable_filter'):
                                sheet.write('E' + str(row), line.get('balance_cmp'), cell_style_level2)
                        # elif row in [33, 34]:
                        #     sheet.write('A' + str(row), line['name'], title_style_level3)
                        #     sheet.write('B' + str(row), line.get('brut'), cell_style_level3)
                        #     sheet.write('C' + str(row), line.get('amorti'), cell_style_level3)
                        #     sheet.write('D' + str(row), line.get('net'), cell_style_level3)
                        #     if data.get('enable_filter'):
                        #         sheet.write('E' + str(row), line.get('balance_cmp'), cell_style_level3)
                        elif row in [22, 37,38, 39, 40]:
                            sheet.write('A' + str(row), line['name'], bold)
                            sheet.write('B' + str(row), line.get('brut'), bold)
                            sheet.write('C' + str(row), line.get('amorti'), bold)
                            sheet.write('D' + str(row), line.get('net'), bold)
                            if data.get('enable_filter'):
                                sheet.write('E' + str(row), line.get('balance_cmp'), bold)
                        else:
                            sheet.write('A' + str(row), line['name'], cell_style)
                            sheet.write('B' + str(row), line.get('brut'), cell_style)
                            sheet.write('C' + str(row), line.get('amorti'), cell_style)
                            sheet.write('D' + str(row), line.get('net'), cell_style)
                            if data.get('enable_filter'):
                                sheet.write('E' + str(row), line.get('balance_cmp'), cell_style)
                    else:
                        continue
                    row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        # workbook.close()

