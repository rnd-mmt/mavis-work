# -*- coding: utf-8 -*-
import calendar
from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo import models


class ParticularReport(models.AbstractModel):
    _name = 'report.l10n_mg_reports_c.flux_tresorerie_report_template'

    def _get_report_values(self, docids, data=None):

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        is_custom = data.get('is_custom', False)
        domain = []
        domain_prec = []
        start_date_ef = date.today()
        end_date_ef = date.today()
        if is_custom:
            custom_date = data.get('start_date', datetime.now()), data.get('end_date', datetime.now())
            start_date_prec = datetime.strptime(str(custom_date[0]), '%Y-%m-%d') - relativedelta(years=1)
            end_date_prec = datetime.strptime(str(custom_date[1]), '%Y-%m-%d') - relativedelta(years=1)
            custom_date_prec = start_date_prec, end_date_prec
            domain = [('date', '>=', custom_date[0]), ('date', '<=', custom_date[1])]
            domain_prec = [('date', '>=', custom_date_prec[0]), ('date', '<=', custom_date_prec[1])]
            start_date_ef = custom_date[0]
            end_date_ef = custom_date[1]
        else:
            period = str(data.get('period')).split('_')
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
            'encaiss_client': 0, 'somme_frns_pers': 0, 'interet_frais_fi': 0, 'impot_result': 0, 'flux_avant_extra': 0,
            'flux_extra': 0, 't_flux_operationnel': 0,
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
            current_code = account.account_id.code if account.account_id.code else ""

            # Encaiss client
            if current_code == '7520000' or current_code[:4] == '7571' or current_code[:4] == '7572' or current_code[
                                                                                                        :3] == '758':
                result['encaiss_client'] -= account.balance
            if current_code[:3] == '701' or current_code[:3] == '707' or current_code[:3] == '708':
                result['encaiss_client'] -= account.balance
            if current_code in ['4110000', '4111000', '4111100', '4111110', '4112000']:
                res += account.balance
                if res < 0:
                    res = 0
                result['encaiss_client'] -= account.balance
            if current_code in ['4211000', '4280000', '4251100', '4251500', '4251700', '4251800', '4251900', '4286000',
                                '4441000', '4454000', '4455000', '4456200', '4456100', '4456300', '4456580', '4458100',
                                '4459000', '4096000', '4091000', '4092000', '4572000', '4574003', '4620000', '4670000',
                                '4672000', '4673000', '4673100', '4673200', '4675000', '4676000', '4677000', '4678000',
                                '4678003', '4678004', '4678005', '4678008', '4678200', '4678300', '4678400', '4678500',
                                '4678600', '4678700', '4678800', '4678900', '4678901', '4678902', '4679000', '4679200',
                                '4679210', '4679300', '4679400', '4679500', '4679600', '4679700', '4679800', '4686000',
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

            if current_code in ['5110000', '5111000', '5121000', '5121100', '5121200', '5121300', '5122000', '5122100',
                                '5122200', '5122300', '5122400', '5123000', '5123100', '5123200', '5128000', '5198100',
                                '5300000', '5312000', '5811000']:
                result['tresorerie_clot'] += account.balance
            if current_code in ['5121000', '5121200', '5198100', '5198200', '5312000']:
                result['tresorerie_clot'] += account.balance

        for account_prec in account_moves_prec:
            current_code_prec = account_prec.account_id.code if account_prec.account_id.code else ""
            if current_code_prec[:2] == '40' or current_code_prec[:2] == '41' or current_code_prec[:2] == '42' or \
                    current_code_prec[:2] == '43' or current_code_prec[:2] == '44' or current_code_prec[:2] == '45' or \
                    current_code_prec[:2] == '46' or current_code_prec[:2] == '47':
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

            if current_code_prec == '1010000' or current_code_prec[:3] != '110' or current_code_prec[:3] == '106' or \
                    current_code_prec[:3] == '120' or current_code_prec[:3] == '129':
                result['dividende_distribution'] += account_prec.balance

            if current_code_prec[:2] == '60' or current_code_prec[:2] == '61' or current_code_prec[:2] == '62' or \
                    current_code_prec[:2] == '65' or current_code_prec[:2] == '64' or current_code_prec[:2] == '68' or \
                    current_code_prec[:2] == '66':
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

        docargs = {
            'doc_ids': docids,
            'doc_model': model,
            'docs': self,
            'account_moves': account_moves,
            'result': result,
            'start_date_ef': start_date_ef,
            'end_date_ef': end_date_ef
        }
        return docargs
