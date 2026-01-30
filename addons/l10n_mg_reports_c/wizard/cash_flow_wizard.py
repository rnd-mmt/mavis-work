# -*- coding: utf-8 -*-

import calendar
import io
import json

from odoo.exceptions import ValidationError
from odoo.tools import date_utils

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields,_


class CashFLowWizard(models.TransientModel):
    _name = 'cash.flow.wizard'
    _description = 'Wizard for generating cash flow report view'

    start_date = fields.Date('Start date', default=date.today().replace(day=1) - relativedelta(months=3))
    end_date = fields.Date('End date', default=date.today())
    period = fields.Selection([('1_1', 'This month'), ('2_1', 'This quarter'), ('3_1', 'This fiscal year'),
                               ('1_2', 'The last month'), ('2_2', 'Last quarter'),
                               ('3_2', 'Last fiscal year')], default='3_1')
    is_custom = fields.Boolean(default=False)

    type = fields.Selection([('direct', 'Direct'), ('indirect', 'Indirect')], string="Type", default='direct')

    def print_pdf(self):
        self.ensure_one()
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'period': self.period,
            'is_custom': self.is_custom,
            'type': self.type
        }
        if self.type == 'direct':
            return self.env.ref('l10n_mg_reports_c.flux_tresorerie_report').report_action(self, data=data)
        else:
            return self.env.ref('l10n_mg_reports_c.indirect_flux_tresorerie_report').report_action(self, data=data)

    def export_excel(self):
        if self.start_date > self.end_date:
            raise ValidationError(_('Start Date must be less than End Date'))
        data = {
            'p_start_date': str(self.start_date).replace('-', '__'),
            'p_end_date': str(self.end_date).replace('-', '__'),
            'p_period': str(self.period),
            'p_is_custom': self.is_custom,
            'type': self.type
        }
        return {
            # 'type': 'ir_actions_xlsx_download',
            'data': {'model': 'cash.flow.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': _("Flux tresorerie direct") if self.type == 'direct' else _("Flux tresorerie indirect"),
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        if data['type'] == 'direct':
            xls_file = io.BytesIO()
            workbook = xlsxwriter.Workbook(xls_file, {'in_memory': True})
            p_start_date = data['p_start_date'].split('__')
            p_end_date = data['p_end_date'].split('__')
            p_start_date = date(int(p_start_date[0]), int(p_start_date[1]), int(p_start_date[2]))
            p_end_date = date(int(p_end_date[0]), int(p_end_date[1]), int(p_end_date[2]))

            # Text formating
            date_format = workbook.add_format({
                'num_format': 'dd/mm/yyyy',
                'border': 1,
                'bold': 1,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': 'white'
            })
            title_format = workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': 'white'
            })
            text_format = workbook.add_format({
                'border': 1,
                'align': 'right',
                'valign': 'vcenter',
                'fg_color': 'white'
            })
            bolding = workbook.add_format()
            bolding.set_bold(True)

            # Create sheet
            worksheet = workbook.add_worksheet('Tresorerie')

            # Adjust column
            worksheet.set_column('A:A', 65)
            worksheet.set_column('B:B', 20)

            # Get search domain
            is_custom = data.get('p_is_custom')
            domain = []
            domain_prec = []
            start_date_ef = date.today()
            end_date_ef = date.today()
            if is_custom :
                custom_date = p_start_date, p_end_date
                custom_date_prec = p_start_date - relativedelta(years=1), p_end_date - relativedelta(years=1)
                domain = [('date', '>=', custom_date[0]), ('date', '<=', custom_date[1])]
                domain_prec = [('date', '>=', custom_date_prec[0]), ('date', '<=', custom_date_prec[1])]
                start_date_ef = custom_date[0]
                end_date_ef = custom_date[1]
            else:
                period = data['p_period'].split('_')
                code, t_code = period[0], period[1]
                today = date.today()
                month_before = date.today() - relativedelta(months=1)
                if code == '1':
                    first_month = today.replace(day=1) if t_code == '1' else month_before.replace(day=1)
                    last_month = today.replace(
                        day=calendar.monthrange(today.year, today.month)[1]) if t_code == 1 else month_before.replace(
                        day=calendar.monthrange(month_before.year, month_before.month)[1])
                    first_month_prec = first_month - relativedelta(months=1)
                    last_month_prec = last_month - relativedelta(months=1)
                    domain = [('date', '>=', first_month), ('date', '<=', last_month)]
                    domain_prec = [('date', '>=', first_month_prec), ('date', '<=', last_month_prec)]
                    start_date_ef = first_month
                    end_date_ef = last_month

                elif code == '2':
                    tab = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4]
                    quarter = tab[today.month - 1]
                    if t_code == '1':
                        if quarter == 1:
                            date_first = date(today.year, 1, 1)
                            date_end = date(today.year, 3, 31)
                        elif quarter == 2:
                            date_first = date(today.year, 4, 1)
                            date_end = date(today.year, 6, 30)
                        elif quarter == 3:
                            date_first = date(today.year, 7, 1)
                            date_end = date(today.year, 9, 30)
                        else:
                            date_first = date(today.year, 10, 1)
                            date_end = date(today.year, 12, 31)
                    else:
                        if quarter == 1:
                            date_first = date(today.year - 1, 10, 1)
                            date_end = date(today.year - 1, 12, 31)
                        elif quarter == 2:
                            date_first = date(today.year, 1, 1)
                            date_end = date(today.year, 3, 31)
                        elif quarter == 3:
                            date_first = date(today.year, 4, 1)
                            date_end = date(today.year, 6, 30)
                        else:
                            date_first = date(today.year, 7, 1)
                            date_end = date(today.year, 9, 30)
                    domain = [('date', '>=', date_first), ('date', '<=', date_end)]
                    domain_prec = [('date', '>=', date_first - relativedelta(months=3)),
                                   ('date', '<=', date_end - relativedelta(months=3))]
                    start_date_ef = date_first
                    end_date_ef = date_end

                elif code == '3':
                    years = today.year if t_code == '1' else today.year - 1
                    date_first = date(years, 1, 1)
                    date_end = date(years, 12, 31)
                    domain = [('date', '>=', date_first), ('date', '<=', date_end)]
                    domain_prec = [('date', '>=', date_first - relativedelta(years=1)),
                                   ('date', '<=', date_end - relativedelta(years=1))]
                    start_date_ef = date_first
                    end_date_ef = date_end

            start_date_ef = datetime.strptime(str(start_date_ef), '%Y-%m-%d').strftime('%d/%m/%Y')
            end_date_ef = datetime.strptime(str(end_date_ef), '%Y-%m-%d').strftime('%d/%m/%Y')
            account_moves = self.env['account.move.line'].search(domain)
            account_moves_prec = self.env['account.move.line'].search(domain_prec)
            result = {
                'encaiss_client': 0, 'somme_frns_pers': 0, 'interet_frais_fi': 0, 'impot_result': 0,
                'flux_avant_extra': 0, 'flux_extra': 0, 't_flux_operationnel': 0,
                'decaiss_acquis_immo': 0, 'encaiss_cession_immo': 0, 'decaiss_acquis_immo_fi': 0,
                'encaiss_cession_immo_fi': 0, 'interet_placement': 0, 'dividende_quote': 0, 't_flux_invest': 0,
                'encaiss_action': 0, 'dividende_distribution': 0, 'augmentation_num': 0, 'encaiss_emprunt': 0,
                'remb_emprunt': 0, 't_flux_finance': 0,
                'profit_change': 0, 'perte_change': 0,
                'variation_periode': 0,
                'tresorerie_ouv': 0, 'tresorerie_clot': 0,
                'variation_tresorerie_periode': 0,
            }

            rep = 0
            res = 0

            for account in account_moves:
                current_code = account.account_id.code

                # Encaiss client
                if current_code == '7520000' or current_code[:4] == '7571' or current_code[
                                                                              :4] == '7572' or current_code[
                                                                                               :3] == '758':
                    result['encaiss_client'] -= account.balance
                if current_code[:3] == '701' or current_code[:3] == '707' or current_code[:3] == '708':
                    result['encaiss_client'] -= account.balance
                if current_code in ['4110000', '4111000', '4111100', '4111110', '4112000']:
                    res += account.balance
                    if res < 0:
                        res = 0
                    result['encaiss_client'] -= account.balance
                if current_code in ['4211000', '4280000', '4251100', '4251500', '4251700', '4251800', '4251900',
                                    '4286000', '4441000', '4454000', '4455000', '4456200', '4456100', '4456300',
                                    '4456580', '4458100', '4459000', '4096000', '4091000', '4092000', '4572000',
                                    '4574003', '4620000', '4670000', '4672000', '4673000', '4673100', '4673200',
                                    '4675000', '4676000', '4677000', '4678000', '4678003', '4678004', '4678005',
                                    '4678008', '4678200', '4678300', '4678400', '4678500', '4678600', '4678700',
                                    '4678800', '4678900', '4678901', '4678902', '4679000', '4679200', '4679210',
                                    '4679300', '4679400', '4679500', '4679600', '4679700', '4679800', '4686000',
                                    '4710000', '4860000', '4861000']:
                    result['encaiss_client'] -= account.balance

                # Encaiss client

                # Somme frns pers
                if current_code[:2] == '40' or current_code[:2] == '41' or current_code[:2] == '42' or \
                        current_code[:2] == '43' or current_code[:2] == '44' or current_code[:2] == '45' or \
                        current_code[:2] == '46' or current_code[:2] == '47':
                    result['somme_frns_pers'] -= account.balance

                if current_code[:2] == '60' or current_code[:2] == '61' or current_code[:2] == '62' or \
                        current_code[:2] == '63' or current_code[:2] == '64' or current_code[:2] == '65':
                    result['somme_frns_pers'] -= account.balance

                # impot sur les résultats payés

                if current_code[:4] == '6950':
                    result['impot_result'] -= account.balance

                # interet frais financier
                if current_code[:2] == '76' or current_code[:4] == '7573':
                    result['interet_frais_fi'] -= account.balance
                if current_code[:2] == '66':
                    result['interet_frais_fi'] -= account.balance

                # Encaiss cession immo
                if current_code[:2] == '26':
                    result['encaiss_cession_immo_fi'] -= account.balance
                if current_code[:2] == '29':
                    result['encaiss_cession_immo_fi'] += account.balance
                if current_code[:4] == '6852':
                    result['encaiss_cession_immo_fi'] -= account.balance

                # Encaiss cession immo

                # Decaiss acquis immo
                if current_code[:2] == '21':
                    result['decaiss_acquis_immo'] -= account.balance
                if current_code[:2] == '28':
                    result['decaiss_acquis_immo'] += account.balance
                if current_code[:3] == '681':
                    result['decaiss_acquis_immo'] += account.balance

                # Dividende et autres distributions effectuées
                if current_code == '1010000' or current_code[:3] != '110' or current_code[:3] == '106' or \
                        current_code[:3] == '120' or current_code[:3] == '129':
                    result['dividende_distribution'] += account.balance
                    # RESULTAT

                if current_code in ['5110000', '5111000', '5121000', '5121100', '5121200', '5121300', '5122000',
                                    '5122100', '5122200', '5122300', '5122400', '5123000', '5123100', '5123200',
                                    '5128000', '5198100', '5300000', '5312000', '5811000']:
                    result['tresorerie_clot'] += account.balance
                if current_code in ['5121000', '5121200', '5198100', '5198200', '5312000']:
                    result['tresorerie_clot'] += account.balance

            for account_prec in account_moves_prec:
                current_code_prec = account_prec.account_id.code

                if current_code_prec[:2] == '40' or current_code_prec[:2] == '41' or current_code_prec[:2] == '42' or \
                        current_code_prec[:2] == '43' or current_code_prec[:2] == '44' or \
                        current_code_prec[:2] == '45' or current_code_prec[:2] == '46' or current_code_prec[:2] == '47':
                    result['somme_frns_pers'] += account_prec.balance

                if current_code_prec in ['5110000', '5111000', '5121000', '5121100', '5121200', '5121300', '5122000',
                                         '5122100', '5122200', '5122300', '5122400', '5123000', '5123100', '5123200',
                                         '5128000', '5198100', '5300000', '5312000', '5811000']:
                    result['tresorerie_ouv'] += account_prec.balance
                if current_code_prec in ['5121000', '5121200', '5198100', '5198200', '5312000']:
                    result['tresorerie_ouv'] += account_prec.balance

                if current_code_prec in ['4110000', '4111000', '4111100', '4111110', '4112000']:
                    rep += account_prec.balance
                    if rep < 0:
                        rep = 0
                    result['encaiss_client'] += account_prec.balance
                if current_code_prec in ['4211000', '4280000', '4251100', '4251500', '4251700', '4251800', '4251900',
                                         '4286000', '4441000', '4454000', '4455000', '4456200', '4456100', '4456300',
                                         '4456580', '4458100', '4459000', '4096000', '4091000', '4092000', '4572000',
                                         '4574003', '4620000', '4670000', '4672000', '4673000', '4673100', '4673200',
                                         '4675000', '4676000', '4677000', '4678000', '4678003', '4678004', '4678005',
                                         '4678008', '4678200', '4678300', '4678400', '4678500', '4678600', '4678700',
                                         '4678800', '4678900', '4678901', '4678902', '4679000', '4679200', '4679210',
                                         '4679300', '4679400', '4679500', '4679600', '4679700', '4679800', '4686000',
                                         '4710000', '4860000', '4861000']:
                    result['encaiss_client'] -= account_prec.balance

                if current_code_prec[:2] == '26':
                    result['encaiss_cession_immo_fi'] += account_prec.balance
                if current_code_prec[:2] == '29':
                    result['encaiss_cession_immo_fi'] -= account_prec.balance

                if current_code_prec[:2] == '21':
                    result['decaiss_acquis_immo'] += account_prec.balance
                if current_code_prec[:2] == '28':
                    result['decaiss_acquis_immo'] -= account_prec.balance

                if current_code_prec == '1010000' or current_code_prec[:3] != '110' or \
                        current_code_prec[:3] == '106' or current_code_prec[:3] == '120' or \
                        current_code_prec[:3] == '129':
                    result['dividende_distribution'] += account_prec.balance

                if current_code_prec[:2] == '60' or current_code_prec[:2] == '61' or current_code_prec[:2] == '62' or \
                        current_code_prec[:2] == '65' or current_code_prec[:2] == '64' or \
                        current_code_prec[:2] == '68' or current_code_prec[:2] == '66':
                    result['dividende_distribution'] += account_prec.balance
                if current_code_prec[:2] == '70' or current_code_prec[:2] == '71' or current_code_prec[:2] == '72' or \
                        current_code_prec[:2] == '75' or current_code_prec[:2] == '78' or current_code_prec[:2] == '76':
                    result['dividende_distribution'] += account_prec.balance

            result['flux_avant_extra'] = result['encaiss_client'] + result['somme_frns_pers'] + result[
                'interet_frais_fi'] + result['impot_result']
            result['t_flux_operationnel'] = result['flux_avant_extra'] + result['flux_extra']

            result['t_flux_invest'] = result['decaiss_acquis_immo'] + result['encaiss_cession_immo'] + result[
                'decaiss_acquis_immo_fi'] + result['encaiss_cession_immo_fi'] + result['interet_placement'] + result[
                                          'dividende_quote']
            result['t_flux_finance'] = result['encaiss_action'] + result['dividende_distribution'] + result[
                'augmentation_num'] + result['encaiss_emprunt'] + result['remb_emprunt']

            result['variation_periode'] = result['t_flux_operationnel'] + result['t_flux_invest'] + result[
                't_flux_finance'] + result['profit_change'] + result['perte_change']

            result['variation_tresorerie_periode'] = result['tresorerie_clot'] - result['tresorerie_ouv']

            # Complete file
            worksheet.merge_range('A1:B1', _('FLUX DE TRESORERIE DIRECT du %s au %s') % (start_date_ef, end_date_ef),
                                  title_format)
            worksheet.merge_range('A2:B2', _('FLUX DE TRESORERIE LIES AUX ACTIVITES OPERATIONNELLES'), title_format)
            worksheet.write(2, 0, _('Encaissement recu des clients'), text_format)
            worksheet.write(2, 1,
                            '{:10,.2f}'.format(float(result['encaiss_client'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(3, 0, _('Sommes versees aux fournisseurs et au personnel'), text_format)
            worksheet.write(3, 1,
                            '{:10,.2f}'.format(float(result['somme_frns_pers'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(4, 0, _('Interets et autres frais financiers payes'), text_format)
            worksheet.write(4, 1,
                            '{:10,.2f}'.format(float(result['interet_frais_fi'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(5, 0, _('Impots sur les resultats payes'), text_format)
            worksheet.write(5, 1, '{:10,.2f}'.format(float(result['impot_result'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(6, 0, _('Flux de tresorerie avant elements extraordinaires'), bolding)
            worksheet.write(6, 1,
                            '{:10,.2f}'.format(float(result['flux_avant_extra'])).replace(',', ' ').replace('.', ','),
                            bolding)
            worksheet.write(7, 0, _('Flux de tresorerie lie a des evenements extraordinaires (a preciser)'), text_format)
            worksheet.write(7, 1, '{:10,.2f}'.format(float(result['flux_extra'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(8, 0, _('A - FLUX DE TRESORERIE NET PROVENANT DES ACTIVITES OPERATIONNELLES'), bolding)
            worksheet.write(8, 1,
                            '{:10,.2f}'.format(float(result['t_flux_operationnel'])).replace(',', ' ').replace('.',
                                                                                                               ','),
                            bolding)
            worksheet.merge_range('A10:B10', _('FLUX DE TRESORERIE LIEES AUX ACTIVITES D\'INVESTISSEMENT'), title_format)
            worksheet.write(10, 0, _('Decaissement sur acquisition d\'immobilisations corporelles ou incorporelles'),
                            text_format)
            worksheet.write(10, 1,
                            '{:10,.2f}'.format(float(result['decaiss_acquis_immo'])).replace(',', ' ').replace('.',
                                                                                                               ','),
                            text_format)
            worksheet.write(11, 0, _('Encaissement sur cession d\'immobilisations corporelles ou incorporelles'),
                            text_format)
            worksheet.write(11, 1,
                            '{:10,.2f}'.format(float(result['encaiss_cession_immo'])).replace(',', ' ').replace('.',
                                                                                                                ','),
                            text_format)
            worksheet.write(12, 0, _('Decaissement sur acquisition d\'immobilisations financieres'), text_format)
            worksheet.write(12, 1,
                            '{:10,.2f}'.format(float(result['decaiss_acquis_immo_fi'])).replace(',', ' ').replace('.',
                                                                                                                  ','),
                            text_format)
            worksheet.write(13, 0, _('Encaissement sur cessions d\'immobilisations financieres'), text_format)
            worksheet.write(13, 1,
                            '{:10,.2f}'.format(float(result['encaiss_cession_immo_fi'])).replace(',', ' ').replace('.',
                                                                                                                   ','),
                            text_format)
            worksheet.write(14, 0, _('Interets encaisses sur placements financiers'), text_format)
            worksheet.write(14, 1,
                            '{:10,.2f}'.format(float(result['interet_placement'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(15, 0, _('Dividendes et quote part de resultats recus'), text_format)
            worksheet.write(15, 1,
                            '{:10,.2f}'.format(float(result['dividende_quote'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(16, 0, _('B - FLUX DE TRESORERIE NET PROVENANT DES ACTIVITES D\'INVESTISSEMENT'), bolding)
            worksheet.write(16, 1,
                            '{:10,.2f}'.format(float(result['t_flux_invest'])).replace(',', ' ').replace('.', ','),
                            bolding)
            worksheet.merge_range('A18:B18', _('FLUX DE TRESORERIE LIES AUX ACTIVITES DE FINANCEMENT'), title_format)
            worksheet.write(18, 0, _('Encaissements suite a l\'emissions d\'actions'), text_format)
            worksheet.write(18, 1,
                            '{:10,.2f}'.format(float(result['encaiss_action'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(19, 0, _('Dividendes at autres distributions effectues'), text_format)
            worksheet.write(19, 1,
                            '{:10,.2f}'.format(float(result['dividende_distribution'])).replace(',', ' ').replace('.',
                                                                                                                  ','),
                            text_format)
            worksheet.write(20, 0, _('Augmentation de capital en numeraire'), text_format)
            worksheet.write(20, 1,
                            '{:10,.2f}'.format(float(result['augmentation_num'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(21, 0, _('Encaissements provenant d\'emprunts'), text_format)
            worksheet.write(21, 1,
                            '{:10,.2f}'.format(float(result['encaiss_emprunt'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(22, 0, _('Remboursement d\'emprunts ou d\'autres dettes assimiles'), text_format)
            worksheet.write(22, 1,
                            '{:10,.2f}'.format(float(result['remb_emprunt'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(23, 0, _('C - FLUX DE TRESORERIE NET PROVENANT DES ACTIVITES DE FINANCEMENT'), bolding)
            worksheet.write(23, 1,
                            '{:10,.2f}'.format(float(result['t_flux_finance'])).replace(',', ' ').replace('.', ','),
                            bolding)
            worksheet.merge_range('A25:B25',
                                  _('Incidences des variations des taux de change sur liquidites et quasi-liquidites'),
                                  text_format)
            worksheet.write(25, 0, _('Profit de change'), text_format)
            worksheet.write(25, 1,
                            '{:10,.2f}'.format(float(result['profit_change'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(26, 0, _('Perte de change'), text_format)
            worksheet.write(26, 1,
                            '{:10,.2f}'.format(float(result['perte_change'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(27, 0, _('VARIATION DE TRESORERIE DE LA PERIODE (A+B+C)'), bolding)
            worksheet.write(27, 1,
                            '{:10,.2f}'.format(float(result['variation_periode'])).replace(',', ' ').replace('.', ','),
                            bolding)
            worksheet.write(28, 0, _('Tresorerie d\'ouverture'), text_format)
            worksheet.write(28, 1,
                            '{:10,.2f}'.format(float(result['tresorerie_ouv'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(29, 0, _('Tresorerie de cloture'), text_format)
            worksheet.write(29, 1,
                            '{:10,.2f}'.format(float(result['tresorerie_clot'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(30, 0, _('VARIATION DE TRESORERIE DE LA PERIODE'), bolding)
            worksheet.write(30, 1,
                            '{:10,.2f}'.format(float(result['variation_tresorerie_periode'])).replace(',', ' ').replace(
                                '.', ','), bolding)

            # Return XLS files
            workbook.close()
            xls_file.seek(0)
            response.stream.write(xls_file.read())
            xls_file.close()
        else:
            xls_file = io.BytesIO()
            workbook = xlsxwriter.Workbook(xls_file)
            p_start_date = data['p_start_date'].split('__')
            p_end_date = data['p_end_date'].split('__')
            p_start_date = date(int(p_start_date[0]), int(p_start_date[1]), int(p_start_date[2]))
            p_end_date = date(int(p_end_date[0]), int(p_end_date[1]), int(p_end_date[2]))

            # Text formating
            date_format = workbook.add_format({
                'num_format': 'dd/mm/yyyy',
                'border': 1,
                'bold': 1,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': 'white'
            })
            title_format = workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': 'white'
            })
            text_format = workbook.add_format({
                'border': 1,
                'align': 'right',
                'valign': 'vcenter',
                'fg_color': 'white'
            })
            bolding = workbook.add_format({
                'border': 1,
                'bold': 1,
                'align': 'right',
            })

            # Create sheet
            worksheet = workbook.add_worksheet('Tresorerie')

            # Adjust column
            worksheet.set_column('A:A', 65)
            worksheet.set_column('B:B', 20)

            # Get search domain

            is_custom = data.get('p_is_custom')
            domain = []
            domain_prec = []
            start_date_ef = date.today()
            end_date_ef = date.today()
            if is_custom:
                custom_date = p_start_date, p_end_date
                custom_date_prec = p_start_date - relativedelta(years=1), p_end_date - relativedelta(years=1)
                domain = [('date', '>=', custom_date[0]), ('date', '<=', custom_date[1])]
                domain_prec = [('date', '>=', custom_date_prec[0]), ('date', '<=', custom_date_prec[1])]
                start_date_ef = custom_date[0]
                end_date_ef = custom_date[1]
            else:
                period = str(data.get('p_period')).split('_')
                code, t_code = period[0], period[1]
                today = date.today()
                month_before = date.today() - relativedelta(months=1)
                if code == '1':
                    first_month = today.replace(day=1) if t_code == '1' else month_before.replace(day=1)
                    last_month = today.replace(
                        day=calendar.monthrange(today.year, today.month)[1]) if t_code == 1 else month_before.replace(
                        day=calendar.monthrange(month_before.year, month_before.month)[1])
                    first_month_prec = first_month - relativedelta(months=1)
                    last_month_prec = last_month - relativedelta(months=1)
                    domain = [('date', '>=', first_month), ('date', '<=', last_month)]
                    domain_prec = [('date', '>=', first_month_prec), ('date', '<=', last_month_prec)]
                    start_date_ef = first_month
                    end_date_ef = last_month

                elif code == '2':
                    tab = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4]
                    quarter = tab[today.month - 1]
                    if t_code == '1':
                        if quarter == 1:
                            date_first = date(today.year, 1, 1)
                            date_end = date(today.year, 3, 31)
                        elif quarter == 2:
                            date_first = date(today.year, 4, 1)
                            date_end = date(today.year, 6, 30)
                        elif quarter == 3:
                            date_first = date(today.year, 7, 1)
                            date_end = date(today.year, 9, 30)
                        else:
                            date_first = date(today.year, 10, 1)
                            date_end = date(today.year, 12, 31)
                    else:
                        if quarter == 1:
                            date_first = date(today.year - 1, 10, 1)
                            date_end = date(today.year - 1, 12, 31)
                        elif quarter == 2:
                            date_first = date(today.year, 1, 1)
                            date_end = date(today.year, 3, 31)
                        elif quarter == 3:
                            date_first = date(today.year, 4, 1)
                            date_end = date(today.year, 6, 30)
                        else:
                            date_first = date(today.year, 7, 1)
                            date_end = date(today.year, 9, 30)
                    domain = [('date', '>=', date_first), ('date', '<=', date_end)]
                    domain_prec = [('date', '>=', date_first - relativedelta(months=3)),
                                   ('date', '<=', date_end - relativedelta(months=3))]
                    start_date_ef = date_first
                    end_date_ef = date_end

                elif code == '3':
                    years = today.year if t_code == '1' else today.year - 1
                    date_first = date(years, 1, 1)
                    date_end = date(years, 12, 31)
                    domain = [('date', '>=', date_first), ('date', '<=', date_end)]
                    domain_prec = [('date', '>=', date_first - relativedelta(years=1)),
                                   ('date', '<=', date_end - relativedelta(years=1))]
                    start_date_ef = date_first
                    end_date_ef = date_end

            start_date_ef = datetime.strptime(str(start_date_ef), '%Y-%m-%d').strftime('%d/%m/%Y')
            end_date_ef = datetime.strptime(str(end_date_ef), '%Y-%m-%d').strftime('%d/%m/%Y')
            account_moves = self.env['account.move.line'].search(domain)
            account_moves_prec = self.env['account.move.line'].search(domain_prec)
            result = {
                'resultat_net': 0, 'amort_provision': 0, 'variation_prov': 0, 'variation_impot': 0,
                'variation_stock': 0,
                'variation_stock_n': 0, 'variation_stock_n_1': 0, 'variation_client_creance_n': 0,
                'variation_client_creance_n_1': 0,
                'variation_client_creance': 0, 'variation_frns_dette': 0, 'moins_plus_value': 0, 'flux_activite': 0,
                'decaiss_acqui_immo': 0, 'encaiss_cess_immo': 0, 'incidence_var': 0, 'flux_invest': 0,
                'dividende': 0, 'augment_num': 0, 'ecart_eval': 0, 'elimination': 0, 'emission_emprunt': 0,
                'remb_emprunt': 0, 'flux_finance': 0, 'variation_periode_abc': 0, 'subv_invest': 0,
                'tresorerie_ouv': 0, 'tresorerie_clot': 0, 'incidence_dev': 0, 'variation_periode': 0,
                'mat_four_brut': 0, 'mat_four_net': 0, 'mat_four_amort': 0, 'mat_four_brut_prec': 0,
                'mat_four_net_prec': 0,
                'mat_four_amort_prec': 0, 'cours_prod_brut': 0, 'cours_prod_amort': 0, 'cours_prod_net': 0,
                'prod_fini_brut': 0, 'prod_fini_amort': 0, 'prod_fini_net': 0, 'creance_brut': 0, 'creance_amort': 0,
            }
            ibs, etat_tva, tva_achat_import, tva_achat_locaux, tva_charge_exploit, tva_intermit_ded, tva_ded_reg, iri, credit_tva = 0, 0, 0, 0, 0, 0, 0, 0, 0
            client_locaux, client_demarcheur, frns_debiteur, client_etranger = 0, 0, 0, 0
            remu_pers, avance_acompte, avance15, mois13, avance_spec, avance_sco, cession_couv, conge_ap = 0, 0, 0, 0, 0, 0, 0, 0
            EMBAR, FEAAS, FRNSETR, RAMAHOLIMIHASO, NIRINA_RAMANANDRAIBE, CSCIMMO, TRANSNS, SANTA, RAMAEXPORT_TANA, RAMAEXPORT_MANAKARA = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
            RAMAEXPORT_BETAINOMBY, RAMAEXPORT_AMBANJA, RAMAEXPORT_TRANSIT_TVE, BESOA, DIVS, MADAME_ANNIE_RIANA, SME, DIVPC, RENE_JULIEN_CACAO, LOVASOA = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
            MANOFI, ETS_JOSEPH_RAMANANDRAIBE, GHM, ZAFITSARA, SUCCESS_JEAN_RAMANANDRAIBE, MAKASSAR_TOURS, AMIGO_HOTEL, MIKEA_LODGE, REPORT_MAVA, GEDECO = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
            ROSSET_DIVERS, SAGRIMAD, SOAMANANTOMBO, COMPTE_FAMILLE, RAINBOW_CENTER, SANEX, RBM, RABEARIVELO, CHARAP, CPTE_ATTENTE = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
            CHARCAV, CH_EXPLOIT = 0, 0
            for account_prec in account_moves_prec.filtered(lambda a: a.parent_state == 'posted'):
                current_code_prec = account_prec.account_id.code
                # Variation des provision
                if current_code_prec[:2] in ['48']:
                    result['variation_prov'] -= account_prec.balance

                # Variation des impots différes
                if current_code_prec[:3] in ['133']:
                    result['variation_impot'] -= account_prec.credit

                # Variation de stocks
                if current_code_prec[:2] in ['31', '32', '33', '34', '35', '37', '38']:
                    result['variation_stock_n_1'] += account_prec.debit
                if current_code_prec[:3] in ['391', '392', '393', '394', '395', '397', '398']:
                    result['variation_stock_n_1'] -= account_prec.credit

                # Variation des clients et autres creances
                if current_code_prec[:2] in ['40', '41', '42', '43', '44', '45', '46']:
                    result['variation_client_creance_n_1'] += account_prec.debit
                if current_code_prec[:3] in ['491']:
                    result['variation_client_creance_n_1'] -= account_prec.balance

                # Variation des fournisseurs et autres dettes
                if current_code_prec[:2] in ['40', '41', '42', '43', '44', '45', '46']:
                    result['variation_frns_dette'] -= account_prec.credit

                # Decaissement sur acquisition d'immobilisations
                if current_code_prec[:2] in ['20', '21']:
                    result['decaiss_acqui_immo'] -= account_prec.debit

                # Encaissement sur cession d'immobilisations
                if current_code_prec[:2] in ['20', '21']:
                    result['encaiss_cess_immo'] -= account_prec.credit

                # Augmentation de capital en numeraire
                if current_code_prec[:4] in ['1013']:
                    result['augment_num'] -= account_prec.balance

                # Emission d'emprunt
                if current_code_prec[:2] in ['16', '17']:
                    result['emission_emprunt'] -= account_prec.credit

                # Remboursement d'emprunt
                if current_code_prec[:2] in ['16', '17']:
                    result['remb_emprunt'] -= account_prec.debit

                # Subvention d'investissement
                if current_code_prec[:2] in ['15']:
                    result['subv_invest'] -= account_prec.balance

                # Tresorerie d'ouverture
                if current_code_prec[:1] == '5':
                    res = -account_prec.balance if account_prec.balance < 0 else 0
                    result['tresorerie_ouv'] -= res
                    rep = account_prec.balance if account_prec.balance > 0 else 0
                    result['tresorerie_ouv'] += rep
                # if current_code_prec[:2] in ['31', '32']:
                #     result['mat_four_brut_prec'] += account_prec.balance
                #     result['mat_four_net_prec'] = result['mat_four_brut_prec'] + result['mat_four_amort_prec']
            for account in account_moves.filtered(lambda a: a.parent_state == 'posted'):
                current_code = account.account_id.code
                # RESULTAT
                if current_code[:1] in ['6']:
                    result['resultat_net'] -= account.balance
                if current_code[:1] in ['7']:
                    result['resultat_net'] -= account.balance

                # Amortissement et provision
                if current_code[:2] == '68':
                    result['amort_provision'] -= account.balance

                # Variation des provision
                if current_code[:2] in ['48']:
                    result['variation_prov'] += account.balance

                # Variation des impots différes
                if current_code[:3] in ['133']:
                    result['variation_impot'] += account.credit

                # Variation de stocks
                if current_code[:2] in ['31', '32', '33', '34', '35', '37', '38']:
                    result['variation_stock_n'] += account.debit
                if current_code[:3] in ['391', '392', '393', '394', '395', '397', '398']:
                    result['variation_stock_n'] -= account.credit

                # Variation des clients et autres creances
                if current_code[:2] in ['40', '41', '42', '43', '44', '45', '46']:
                    result['variation_client_creance_n'] += account.debit
                if current_code[:3] in ['491']:
                    result['variation_client_creance_n'] -= account.balance

                # Variation des fournisseurs et autres dettes
                if current_code[:2] in ['40', '41', '42', '43', '44', '45', '46']:
                    result['variation_frns_dette'] += account.credit

                # Moins ou Plus values de cession nettes d'impots
                if current_code[:3] in ['752']:
                    result['moins_plus_value'] += account.balance
                if current_code[:3] in ['652']:
                    result['moins_plus_value'] -= account.balance

                # Decaissement sur acquisition d'immobilisations
                if current_code[:2] in ['20', '21']:
                    result['decaiss_acqui_immo'] += account.debit

                # Encaissement sur cession d'immobilisations
                if current_code[:2] in ['20', '21']:
                    result['encaiss_cess_immo'] += account.credit

                # Dividende versee aux actionnaires
                if current_code[:3] in ['457']:
                    result['dividende'] += account.balance

                # Augmentation de capital en numeraire
                if current_code[:4] in ['1013']:
                    result['augment_num'] += account.balance

                # Emission d'emprunt
                if current_code[:2] in ['16', '17']:
                    result['emission_emprunt'] += account.credit

                # Remboursement d'emprunt
                if current_code[:2] in ['16', '17']:
                    result['remb_emprunt'] += account.debit

                # Subvention d'investissement
                if current_code[:2] in ['15']:
                    result['subv_invest'] += account.balance

                # Tresorerie de cloture
                if current_code[:1] == '5':
                    res = -account.balance if account.balance < 0 else 0
                    result['tresorerie_clot'] -= res
                    rep = account.balance if account.balance > 0 else 0
                    result['tresorerie_clot'] += rep

            result['variation_client_creance'] = result['variation_client_creance_n_1'] - result[
                'variation_client_creance_n']

            result['cours_prod_net'] = result['cours_prod_brut'] + result['cours_prod_amort']
            result['variation_stock'] = result['variation_stock_n_1'] - result['variation_stock_n']
            result['flux_activite'] = result['resultat_net'] + result['amort_provision'] + result['variation_prov'] + \
                                      result['variation_impot'] + result['variation_stock'] + result[
                                          'variation_client_creance'] + result['variation_frns_dette'] + result[
                                          'moins_plus_value']
            result['flux_invest'] = -result['decaiss_acqui_immo'] + result['encaiss_cess_immo'] + result[
                'incidence_var']
            result['flux_finance'] = result['dividende'] + result['augment_num'] + result['ecart_eval'] + result[
                'elimination'] + result['emission_emprunt'] + result['remb_emprunt']
            result['variation_periode_abc'] = result['flux_activite'] + result['flux_finance'] + result['flux_invest']
            result['variation_periode'] = result['tresorerie_clot'] - result['tresorerie_ouv'] + result['incidence_dev']

            # Complete file
            worksheet.merge_range('A1:B1', _('FLUX DE TRESORERIE INDIRECT du %s au %s') % (start_date_ef, end_date_ef),
                                  title_format)
            worksheet.write(1, 0, _('FLUX DE TRESORERIE LIES A L\'ACTIVITE'), bolding)
            worksheet.write(1, 1, '', text_format)
            worksheet.write(2, 0, _('RESULTAT NET DE L\'EXERCICE'), text_format)
            worksheet.write(2, 1, '{:10,.2f}'.format(float(result['resultat_net'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(3, 0, _('Ajustements pour:'), bolding)
            worksheet.write(3, 1, '', text_format)
            worksheet.write(4, 0, _('Amortissement et provisions'), text_format)
            worksheet.write(4, 1,
                            '{:10,.2f}'.format(float(result['amort_provision'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(5, 0, _('Variation des  provisions et produits constates d\'avance'), text_format)
            worksheet.write(5, 1,
                            '{:10,.2f}'.format(float(result['variation_prov'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(6, 0, _('Variation des impots differes'), text_format)
            worksheet.write(6, 1,
                            '{:10,.2f}'.format(float(result['variation_impot'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(7, 0, _('Variation des stocks'), text_format)
            worksheet.write(7, 1,
                            '{:10,.2f}'.format(float(result['variation_stock'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(8, 0, _('Variation des clients et autres creances'), text_format)
            worksheet.write(8, 1, '{:10,.2f}'.format(float(result['variation_client_creance'])).replace(',', ' ').
                            replace('.', ','), text_format)
            worksheet.write(9, 0, _('Variation des fournisseurs et autres dettes'), text_format)
            worksheet.write(9, 1,
                            '{:10,.2f}'.format(float(result['variation_frns_dette'])).replace(',', ' ').replace('.',
                                                                                                                ','),
                            text_format)
            worksheet.write(10, 0, _('Moins ou Plus values de cession, nettes d\'impots'), text_format)
            worksheet.write(10, 1,
                            '{:10,.2f}'.format(float(result['moins_plus_value'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(11, 0, _('A - FLUX DE TRESORERIE GENERES PAR L\'ACTIVITE'), text_format)
            worksheet.write(11, 1,
                            '{:10,.2f}'.format(float(result['flux_activite'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(12, 0, _('FLUX DE TRESORERIE LIES AUX OPERATIONS D\'INVESTISSEMENT'), bolding)
            worksheet.write(12, 1, '', text_format)
            worksheet.write(13, 0, _('Decaissement sur acquisition d\'immobilisations'), text_format)
            worksheet.write(13, 1,
                            '{:10,.2f}'.format(float(result['decaiss_acqui_immo'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(14, 0, _('Encaissement sur cession d\'immobilisations'), text_format)
            worksheet.write(14, 1,
                            '{:10,.2f}'.format(float(result['encaiss_cess_immo'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(15, 0, _('Incidence de variation sur perimetre de consolidation'), text_format)
            worksheet.write(15, 1,
                            '{:10,.2f}'.format(float(result['incidence_var'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(16, 0, _('B - FLUX DE TRESORERIE LIES AUX OPERATIONS D\'INVESTISSEMENT'), bolding)
            worksheet.write(16, 1, '{:10,.2f}'.format(float(result['flux_invest'])).replace(',', ' ').replace('.', ','),
                            bolding)
            worksheet.write(17, 0, _('FLUX DE TRESORERIE LIES AUX ACTIVITES DE FINANCEMENT'), bolding)
            worksheet.write(17, 1, '', bolding)
            worksheet.write(18, 0, _('Dividende versee aux actionnaires'), text_format)
            worksheet.write(18, 1, '{:10,.2f}'.format(float(result['dividende'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(19, 0, _('Augmentataion de capital en numeraire'), text_format)
            worksheet.write(19, 1, '{:10,.2f}'.format(float(result['augment_num'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(20, 0, 'Ecart d\'evaluation', text_format)
            worksheet.write(20, 1, '{:10,.2f}'.format(float(result['ecart_eval'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(21, 0, _('Eliminations des elements de passifs/actifs'), text_format)
            worksheet.write(21, 1, '{:10,.2f}'.format(float(result['elimination'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(22, 0, _('Emission d\'emprunts'), text_format)
            worksheet.write(22, 1,
                            '{:10,.2f}'.format(float(result['emission_emprunt'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(23, 0, _('Remboursement d\'emprunt'), text_format)
            worksheet.write(23, 1,
                            '{:10,.2f}'.format(float(result['remb_emprunt'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(24, 0, _('Subvention d\'investissement'), text_format)
            worksheet.write(24, 1,
                            '{:10,.2f}'.format(float(result['subv_invest'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(25, 0, _('C - FLUX DE TRESORERIE LIES AUX ACTIVITES DE FINANCEMENT'), bolding)
            worksheet.write(25, 1,
                            '{:10,.2f}'.format(float(result['flux_finance'])).replace(',', ' ').replace('.', ','),
                            bolding)
            worksheet.write(26, 0, _('VARIATION DE TRESORERIE DE LA PERIODE (A+B+C)'), bolding)
            worksheet.write(26, 1,
                            '{:10,.2f}'.format(float(result['variation_periode_abc'])).replace(',', ' ').replace('.',
                                                                                                                 ','),
                            text_format)
            worksheet.write(27, 0, _('Tresorerie d\'ouverture'), text_format)
            worksheet.write(27, 1,
                            '{:10,.2f}'.format(float(result['tresorerie_ouv'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(28, 0, _('Tresorerie de cloture'), text_format)
            worksheet.write(28, 1,
                            '{:10,.2f}'.format(float(result['tresorerie_clot'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(29, 0, _('Incidence des variations de cours de devises'), text_format)
            worksheet.write(29, 1,
                            '{:10,.2f}'.format(float(result['incidence_dev'])).replace(',', ' ').replace('.', ','),
                            text_format)
            worksheet.write(30, 0, _('VARIATION DE TRESORERIE DE LA PERIODE'), bolding)
            worksheet.write(30, 1,
                            '{:10,.2f}'.format(float(result['variation_periode'])).replace(',', ' ').replace('.', ','),
                            bolding)

            # Return XLS files
            workbook.close()
            xls_file.seek(0)
            response.stream.write(xls_file.read())
            xls_file.close()
