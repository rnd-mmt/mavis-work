# -*- coding: utf-8 -*-
import io
import json
from datetime import date
from datetime import datetime

from dateutil.relativedelta import relativedelta

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo.tools import date_utils


class EvcpReportViewWizard(models.TransientModel):
    _name = 'evcp.view'
    _description = 'Wizard for generating EVCP report view'

    def _get_date(self):
        year = datetime.today().year
        years = list()
        for y in range(11):
            years.extend([[str(year - y), str(year - y)]])
        return tuple(years)

    start_date = fields.Date('Start date', default=date.today().replace(day=1) - relativedelta(months=3))
    end_date = fields.Date('End date', default=date.today())
    date_start = fields.Selection(string="Date", selection='_get_date')
    period = fields.Selection([
        ('3_1', 'This fiscal year'),
        ('3_2', 'Last fiscal year')
    ], default='3_1')
    is_custom = fields.Boolean(default=True)


    def confirm_evcp(self):
        if not self.date_start:
            raise UserError(_("Please select a date"))
        # Get parameter
        date_start = str(self.date_start)
        start_date = str(self.start_date)
        end_date = str(self.end_date)
        period = str(self.period)
        is_custom = str(self.is_custom)
        data = {
            'date_start': date_start,
            'start_date': start_date,
            'end_date': end_date,
            'period': period,
            'is_custom': is_custom,
        }
        return self.env.ref('l10n_mg_reports_c.action_report_financial_evcp').report_action(self, data=data,
                                                                                            config=False)

    def print_xlsx(self):
        if not self.date_start:
            raise UserError(_("Please select a date"))
            # Get parameter
        date_start = str(self.date_start)
        start_date = str(self.start_date)
        end_date = str(self.end_date)
        period = str(self.period)
        is_custom = str(self.is_custom)
        temp_data = {
            'date_start': date_start,
            'start_date': start_date,
            'end_date': end_date,
            'period': period,
            'is_custom': is_custom,
        }
        temp_data = self.env.ref('l10n_mg_reports_c.action_report_financial_evcp').report_action(self, data=temp_data,
                                                                                                 config=False)
        data = {
            'context': temp_data['context'],
            'date_start': date_start,
            'start_date': start_date,
            'end_date': end_date,
            'period': period,
            'is_custom': is_custom,
        }
        return {
            'data': {'model': 'evcp.view',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Evcp_excel',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        report = self.env['report.l10n_mg_reports_c.evcp_report_template']
        report_values = report._get_report_values(docids=None, data=data)
        results = report_values.get('results')
        years = report_values.get('years')
        year_1 = results.get(str(years[0]))
        year_2 = results.get(str(years[1]))
        # excel config
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        bold_bottom = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 1, 'font_size': 11})
        bold = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 11})
        bold_title_center = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'align': 'center', 'font_size': 13, 'bottom': 2})
        bold_center = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'align': 'center', 'font_size': 10, 'bottom': 1})
        cell_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12})
        cell_style_bottom = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'bottom': 1})
        sheet.merge_range('A1:F1',_('ETAT DE VARIATION DES CAPITAUX PROPRES'), bold_title_center)
        sheet.merge_range('A2:F2', _('Unité monétaire : Ariary'), bold)
        sheet.set_column('A:A', 35)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 30)
        sheet.set_column('F:F', 20)
        # data title
        sheet.write('A3', '', bold_center)
        sheet.write('B3', _('Capital social'), bold_center)
        sheet.write('C3', _('Primes et Réserves'), bold_center)
        sheet.write('D3', _('Ecart d''évaluation'), bold_center)
        sheet.write('E3', _('Résultat et Report à nouveau'), bold_center)
        sheet.write('F3', _('Total'), bold_center)
        # excel data line 1
        sheet.write('A4', _('Solde au 31 décembre') + str(int(years[0]) - 1), bold_bottom)
        sheet.write('B4', '{:10,.2f}'.format(float(year_1.get('result_prec_cap'))).replace(',', ' '), cell_style_bottom)
        sheet.write('C4', '{:10,.2f}'.format(float(year_1.get('result_prec_prime'))).replace(',', ' '),
                    cell_style_bottom)
        sheet.write('D4', '{:10,.2f}'.format(float(year_1.get('result_prec_ecart'))).replace(',', ' '),
                    cell_style_bottom)
        sheet.write('E4', '{:10,.2f}'.format(float(year_1.get('result_prec_result'))).replace(',', ' '),
                    cell_style_bottom)
        sheet.write('F4', '{:10,.2f}'.format(float(year_1.get('result_prec_t'))).replace(',', ' '), cell_style_bottom)
        # excel data line 2
        sheet.write('A5', _('Changement de méthode comptable'), bold)
        sheet.write('B5', '{:10,.2f}'.format(float(year_1.get('change_meth_cap'))).replace(',', ' '), cell_style)
        sheet.write('C5', '{:10,.2f}'.format(float(year_1.get('change_meth_prime'))).replace(',', ' '), cell_style)
        sheet.write('D5', '{:10,.2f}'.format(float(year_1.get('change_meth_ecart'))).replace(',', ' '), cell_style)
        sheet.write('E5', '{:10,.2f}'.format(float(year_1.get('change_meth_result'))).replace(',', ' '), cell_style)
        sheet.write('F5', '{:10,.2f}'.format(float(year_1.get('change_meth_t'))).replace(',', ' '), cell_style)
        # excel data line 3
        sheet.write('A6', _('Correction d''erreurs'), bold)
        sheet.write('B6', '{:10,.2f}'.format(float(year_1.get('correct_cap'))).replace(',', ' '), cell_style)
        sheet.write('C6', '{:10,.2f}'.format(float(year_1.get('correct_prime'))).replace(',', ' '), cell_style)
        sheet.write('D6', '{:10,.2f}'.format(float(year_1.get('correct_ecart'))).replace(',', ' '), cell_style)
        sheet.write('E6', '{:10,.2f}'.format(float(year_1.get('correct_result'))).replace(',', ' '), cell_style)
        sheet.write('F6', '{:10,.2f}'.format(float(year_1.get('correct_t'))).replace(',', ' '), cell_style)
        # excel data line 4
        sheet.write('A7', _('Autres produits et charges'), bold)
        sheet.write('B7', '{:10,.2f}'.format(float(year_1.get('prod_charge_cap'))).replace(',', ' '), cell_style)
        sheet.write('C7', '{:10,.2f}'.format(float(year_1.get('prod_charge_prime'))).replace(',', ' '), cell_style)
        sheet.write('D7', '{:10,.2f}'.format(float(year_1.get('prod_charge_ecart'))).replace(',', ' '), cell_style)
        sheet.write('E7', '{:10,.2f}'.format(float(year_1.get('prod_charge_result'))).replace(',', ' '), cell_style)
        sheet.write('F7', '{:10,.2f}'.format(float(year_1.get('prod_charge_t'))).replace(',', ' '), cell_style)
        # excel data line 5
        sheet.write('A8', _('Affectation du résultat précédent'), bold)
        sheet.write('B8', '{:10,.2f}'.format(float(year_1.get('affect_cap'))).replace(',', ' '), cell_style)
        sheet.write('C8', '{:10,.2f}'.format(float(year_1.get('affect_prime'))).replace(',', ' '), cell_style)
        sheet.write('D8', '{:10,.2f}'.format(float(year_1.get('affect_ecart'))).replace(',', ' '), cell_style)
        sheet.write('E8', '{:10,.2f}'.format(float(year_1.get('affect_result'))).replace(',', ' '), cell_style)
        sheet.write('F8', '{:10,.2f}'.format(float(year_1.get('affect_t'))).replace(',', ' '), cell_style)
        # excel data line 6
        sheet.write('A9', _('Opération en capital'), bold)
        sheet.write('B9', '{:10,.2f}'.format(float(year_1.get('operation_cap'))).replace(',', ' '), cell_style)
        sheet.write('C9', '{:10,.2f}'.format(float(year_1.get('operation_prime'))).replace(',', ' '), cell_style)
        sheet.write('D9', '{:10,.2f}'.format(float(year_1.get('operation_ecart'))).replace(',', ' '), cell_style)
        sheet.write('E9', '{:10,.2f}'.format(float(year_1.get('operation_result'))).replace(',', ' '), cell_style)
        sheet.write('F9', '{:10,.2f}'.format(float(year_1.get('operation_t'))).replace(',', ' '), cell_style)
        # excel data line 7
        sheet.write('A10', _('Résultat net au 31 déc') + str(years[0]), bold_bottom)
        sheet.write('B10', '{:10,.2f}'.format(float(year_1.get('resultat_cap'))).replace(',', ' '), cell_style_bottom)
        sheet.write('C10', '{:10,.2f}'.format(float(year_1.get('resultat_prime'))).replace(',', ' '), cell_style_bottom)
        sheet.write('D10', '{:10,.2f}'.format(float(year_1.get('resultat_ecart'))).replace(',', ' '), cell_style_bottom)
        sheet.write('E10', '{:10,.2f}'.format(float(year_1.get('resultat_result'))).replace(',', ' '),
                    cell_style_bottom)
        sheet.write('F10', '{:10,.2f}'.format(float(year_1.get('resultat_t'))).replace(',', ' '), cell_style_bottom)
        # excel data line 8
        sheet.write('A11', _('Solde au 31 décembre') + str(years[0]), bold_bottom)
        sheet.write('B11', '{:10,.2f}'.format(float(year_1.get('result_cap'))).replace(',', ' '), cell_style_bottom)
        sheet.write('C11', '{:10,.2f}'.format(float(year_1.get('result_prime'))).replace(',', ' '), cell_style_bottom)
        sheet.write('D11', '{:10,.2f}'.format(float(year_1.get('result_ecart'))).replace(',', ' '), cell_style_bottom)
        sheet.write('E11', '{:10,.2f}'.format(float(year_1.get('result_result'))).replace(',', ' '), cell_style_bottom)
        sheet.write('F11', '{:10,.2f}'.format(float(year_1.get('result_t'))).replace(',', ' '), cell_style_bottom)
        # excel data line 9
        sheet.write('A12', _('Changement de méthode comptable'), bold)
        sheet.write('B12', '{:10,.2f}'.format(float(year_2.get('change_meth_cap'))).replace(',', ' '), cell_style)
        sheet.write('C12', '{:10,.2f}'.format(float(year_2.get('change_meth_prime'))).replace(',', ' '), cell_style)
        sheet.write('D12', '{:10,.2f}'.format(float(year_2.get('change_meth_ecart'))).replace(',', ' '), cell_style)
        sheet.write('E12', '{:10,.2f}'.format(float(year_2.get('change_meth_result'))).replace(',', ' '), cell_style)
        sheet.write('F12', '{:10,.2f}'.format(float(year_2.get('change_meth_t'))).replace(',', ' '), cell_style)
        # excel data line 10
        sheet.write('A13', _('Correction d''erreurs'), bold)
        sheet.write('B13', '{:10,.2f}'.format(float(year_2.get('correct_cap'))).replace(',', ' '), cell_style)
        sheet.write('C13', '{:10,.2f}'.format(float(year_2.get('correct_prime'))).replace(',', ' '), cell_style)
        sheet.write('D13', '{:10,.2f}'.format(float(year_2.get('correct_ecart'))).replace(',', ' '), cell_style)
        sheet.write('E13', '{:10,.2f}'.format(float(year_2.get('correct_result'))).replace(',', ' '), cell_style)
        sheet.write('F13', '{:10,.2f}'.format(float(year_2.get('correct_t'))).replace(',', ' '), cell_style)
        # excel data line 11
        sheet.write('A14', _('Autres produits et charges'), bold)
        sheet.write('B14', '{:10,.2f}'.format(float(year_2.get('prod_charge_cap'))).replace(',', ' '), cell_style)
        sheet.write('C14', '{:10,.2f}'.format(float(year_2.get('prod_charge_prime'))).replace(',', ' '), cell_style)
        sheet.write('D14', '{:10,.2f}'.format(float(year_2.get('prod_charge_ecart'))).replace(',', ' '), cell_style)
        sheet.write('E14', '{:10,.2f}'.format(float(year_2.get('prod_charge_result'))).replace(',', ' '), cell_style)
        sheet.write('F14', '{:10,.2f}'.format(float(year_2.get('prod_charge_t'))).replace(',', ' '), cell_style)
        # excel data line 12
        sheet.write('A15', _('Affectation du résultat précédent'), bold)
        sheet.write('B15', '{:10,.2f}'.format(float(year_2.get('affect_cap'))).replace(',', ' '), cell_style)
        sheet.write('C15', '{:10,.2f}'.format(float(year_2.get('affect_prime'))).replace(',', ' '), cell_style)
        sheet.write('D15', '{:10,.2f}'.format(float(year_2.get('affect_ecart'))).replace(',', ' '), cell_style)
        sheet.write('E15', '{:10,.2f}'.format(float(year_2.get('affect_result'))).replace(',', ' '), cell_style)
        sheet.write('F15', '{:10,.2f}'.format(float(year_2.get('affect_t'))).replace(',', ' '), cell_style)
        # excel data line 13
        sheet.write('A16', _('Opération en capital'), bold)
        sheet.write('B16', '{:10,.2f}'.format(float(year_2.get('operation_cap'))).replace(',', ' '), cell_style)
        sheet.write('C16', '{:10,.2f}'.format(float(year_2.get('operation_prime'))).replace(',', ' '), cell_style)
        sheet.write('D16', '{:10,.2f}'.format(float(year_2.get('operation_ecart'))).replace(',', ' '), cell_style)
        sheet.write('E16', '{:10,.2f}'.format(float(year_2.get('operation_result'))).replace(',', ' '), cell_style)
        sheet.write('F16', '{:10,.2f}'.format(float(year_2.get('operation_t'))).replace(',', ' '), cell_style)
        # excel data line 14
        sheet.write('A17', _('Résultat net au 31 déc') + str(years[1]), bold_bottom)
        sheet.write('B17', '{:10,.2f}'.format(float(year_2.get('resultat_cap'))).replace(',', ' '), cell_style_bottom)
        sheet.write('C17', '{:10,.2f}'.format(float(year_2.get('resultat_prime'))).replace(',', ' '), cell_style_bottom)
        sheet.write('D17', '{:10,.2f}'.format(float(year_2.get('resultat_ecart'))).replace(',', ' '), cell_style_bottom)
        sheet.write('E17', '{:10,.2f}'.format(float(year_2.get('resultat_result'))).replace(',', ' '),
                    cell_style_bottom)
        sheet.write('F17', '{:10,.2f}'.format(float(year_2.get('resultat_t'))).replace(',', ' '), cell_style_bottom)
        # excel data line 15
        sheet.write('A18', _('Solde au 31 décembre') + str(years[1]), bold_bottom)
        sheet.write('B18', '{:10,.2f}'.format(float(year_2.get('result_cap'))).replace(',', ' '), cell_style_bottom)
        sheet.write('C18', '{:10,.2f}'.format(float(year_2.get('result_prime'))).replace(',', ' '), cell_style_bottom)
        sheet.write('D18', '{:10,.2f}'.format(float(year_2.get('result_ecart'))).replace(',', ' '), cell_style_bottom)
        sheet.write('E18', '{:10,.2f}'.format(float(year_2.get('result_result'))).replace(',', ' '),
                    cell_style_bottom)
        sheet.write('F18', '{:10,.2f}'.format(float(year_2.get('result_t'))).replace(',', ' '), cell_style_bottom)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
