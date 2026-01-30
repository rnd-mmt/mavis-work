# -*- coding: utf-8 -*-
import calendar
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models, _
from odoo.exceptions import UserError


class ParticularReport(models.AbstractModel):
    _name = 'report.l10n_mg_reports_c.evcp_report_template'

    def group(self, number):
        number = round(number, 2)
        s = '%s' % number
        groups = []
        while s and s[-1].isdigit():
            groups.append(s[-3:])
            s = s[:-3]
        result = s + ' '.join(reversed(groups))
        return result.replace(' .', '.')

    def compute_years(self, date):
        nbr = []
        for year in range(2):
            new = int(date) - year if isinstance(date, str) else date - year
            nbr.append(new)
        return sorted(nbr)

    @api.model
    def _get_report_values(self, docids, data=None):
        # if not data or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
        #     raise UserError(_("Form content is missing, this report cannot be printed."))
        if not data:
            raise UserError(_("Form content is missing, this report cannot be printed."))

        is_custom = data.get('is_custom', False)
        domain = []
        res = dict()
        start_date_ef = date.today()
        end_date_ef = date.today()
        if is_custom:
            list_years = self.compute_years(data.get('date_start', datetime.today().year))
            custom_date = data.get('start_date', datetime.now()), data.get('end_date', datetime.now())
            start_date_prec = datetime.strptime(str(custom_date[0]), '%Y-%m-%d') - relativedelta(years=1)
            end_date_prec = datetime.strptime(str(custom_date[1]), '%Y-%m-%d') - relativedelta(years=1)
            custom_date_prec = start_date_prec, end_date_prec
            domain = [('date_maturity', '>=', custom_date[0]), ('date_maturity', '<=', custom_date[1])]
            domain_prec = [('date_maturity', '>=', custom_date_prec[0]), ('date_maturity', '<=', custom_date_prec[1])]
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
                    day=calendar.monthrange(today.year, today.month)[1]) if t_code == '1' else month_before.replace(
                    day=calendar.monthrange(month_before.year, month_before.month)[1])
                first_month_prec = first_month - relativedelta(months=1)
                last_month_prec = last_month - relativedelta(months=1)
                domain = [('date_maturity', '>=', first_month), ('date_maturity', '<=', last_month)]
                domain_prec = [('date_maturity', '>=', first_month_prec), ('date_maturity', '<=', last_month_prec)]
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
                domain = [('date_maturity', '>=', date_first), ('date_maturity', '<=', date_end)]
                domain_prec = [('date_maturity', '>=', date_first - relativedelta(months=3)),
                               ('date_maturity', '<=', date_end - relativedelta(months=3))]
                start_date_ef = date_first
                end_date_ef = date_end

            elif code == '3':
                years = today.year if t_code == '1' else today.year - 1
                list_years = self.compute_years(years)
                date_first = date(years, 1, 1)
                date_end = date(years, 12, 31)
                domain = [('date_maturity', '>=', date_first), ('date_maturity', '<=', date_end)]
                domain_prec = [('date_maturity', '>=', date_first - relativedelta(years=1)),
                               ('date_maturity', '<=', date_end - relativedelta(years=1))]
                start_date_ef = date_first
                end_date_ef = date_end

        for year in list_years:

            date_first = date(year, 1, 1)
            date_end = date(year, 12, 31)
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
                'result_prec_cap': 0, 'result_prec_prime': 0, 'result_prec_ecart': 0, 'result_prec_result': 0,
                'result_prec_t': 0,
                'change_meth_cap': 0, 'change_meth_prime': 0, 'change_meth_ecart': 0, 'change_meth_result': 0,
                'change_meth_t': 0,
                'correct_cap': 0, 'correct_prime': 0, 'correct_ecart': 0, 'correct_result': 0, 'correct_t': 0,
                'prod_charge_cap': 0, 'prod_charge_prime': 0, 'prod_charge_ecart': 0, 'prod_charge_result': 0,
                'prod_charge_t': 0,
                'affect_cap': 0, 'affect_prime': 0, 'affect_ecart': 0, 'affect_result': 0, 'affect_t': 0,
                'operation_cap': 0, 'operation_prime': 0, 'operation_ecart': 0, 'operation_result': 0, 'operation_t': 0,
                'resultat_cap': 0, 'resultat_prime': 0, 'resultat_ecart': 0, 'resultat_result': 0, 'resultat_t': 0,
                'result_cap': 0, 'result_prime': 0, 'result_ecart': 0, 'result_result': 0, 'result_t': 0,
            }
            for account_prec in account_moves_prec:
                current_code_prec = account_prec.account_id.code
                if current_code_prec == '1010000':
                    result['result_prec_cap'] -= account_prec.balance if account_prec.balance < 0 else 0
                if current_code_prec[:3] == '106':
                    result['result_prec_prime'] -= account_prec.balance if account_prec.balance < 0 else 0
                if current_code_prec[:3] == '110' or current_code_prec[:3] == '120':
                    result['result_prec_result'] -= account_prec.balance if account_prec.balance < 0 else 0
                if current_code_prec[:3] == '129':
                    result['result_prec_result'] -= account_prec.balance if account_prec.balance > 0 else 0

            for account in account_moves:
                current_code = account.account_id.code
                # RESULTAT
                if current_code[:2] in ['60', '61', '62', '63', '64', '65', '66', '68', '69']:
                    result['resultat_result'] -= account.balance
                if current_code[:2] in ['70', '71', '72', '75', '76', '78']:
                    result['resultat_result'] -= account.balance
                # RESULTAT

                result['result_prec_t'] = result['result_prec_cap'] + result['result_prec_prime'] + result[
                    'result_prec_ecart'] + result['result_prec_result']
                result['change_meth_t'] = result['change_meth_cap'] + result['change_meth_prime'] + result[
                    'change_meth_ecart'] + result['change_meth_result']
                result['correct_t'] = result['correct_cap'] + result['correct_prime'] + result['correct_ecart'] + \
                                      result['correct_result']
                result['prod_charge_t'] = result['prod_charge_cap'] + result['prod_charge_prime'] + result[
                    'prod_charge_ecart'] + result['prod_charge_result']
                result['affect_t'] = result['affect_cap'] + result['affect_prime'] + result['affect_ecart'] + result[
                    'affect_result']
                result['operation_t'] = result['operation_cap'] + result['operation_prime'] + result[
                    'operation_ecart'] + result['operation_result']
                result['resultat_t'] = result['resultat_cap'] + result['resultat_prime'] + result['resultat_ecart'] + \
                                       result['resultat_result']
                result['result_cap'] = result['result_prec_cap'] + result['change_meth_cap'] + result['correct_cap'] + \
                                       result['prod_charge_cap'] + result['affect_cap'] + result['operation_cap'] + \
                                       result['resultat_cap']
                result['result_prime'] = result['result_prec_prime'] + result['change_meth_prime'] + result[
                    'correct_prime'] + result['prod_charge_prime'] + result['affect_prime'] + result[
                                             'operation_prime'] + result['resultat_prime']
                result['result_ecart'] = result['result_prec_ecart'] + result['change_meth_ecart'] + result[
                    'correct_ecart'] + result['prod_charge_ecart'] + result['affect_ecart'] + result[
                                             'operation_ecart'] + result['resultat_ecart']
                result['result_result'] = result['result_prec_result'] + result['change_meth_result'] + result[
                    'correct_result'] + result['prod_charge_result'] + result['affect_result'] + result[
                                              'operation_result'] + result['resultat_result']
                result['result_t'] = result['result_cap'] + result['result_prime'] + result['result_ecart'] + result[
                    'result_result']
            res.update({str(year): result})

        if not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            return {
                'results': res,
                'years': sorted(list_years),
                'start_date_ef': start_date_ef,
                'end_date_ef': end_date_ef
            }
        else:
            model = self.env.context.get('active_model')
            docs = self.env[model].browse(self.env.context.get('active_id'))
            return {
                'doc_ids': docids,
                'doc_model': model,
                'docs': self,
                'account_moves': account_moves,
                'results': res,
                'years': sorted(list_years),
                'start_date_ef': start_date_ef,
                'end_date_ef': end_date_ef
            }
