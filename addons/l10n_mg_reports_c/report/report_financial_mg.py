# -*- coding: utf-8 -*-
import ast

from odoo import models, _, exceptions
from odoo.exceptions import ValidationError
from odoo.tools import ustr


class ReportFinancial(models.AbstractModel):
    _inherit = 'report.accounting_pdf_reports.report_financial'

    def compute_child_mg(self, report, children, total):
        fields = ['credit', 'debit', 'balance']
        for child in children:
            if child.children_ids:
                total = self.compute_child_mg(report, child.children_ids, total)
            else:
                res = self._compute_report_balance(child)
                for field in fields:
                    total[report.id][field] += res[child.id][field]
        return total

    def compute_vals(self, report):
        res = {}
        fields = ['credit', 'debit', 'balance', 'amort', 'brut', 'net']
        res[report.id] = dict((fn, 0.0) for fn in fields)
        if report.formulas:
            formulas = report.formulas.replace(" ", "")
            [column, formulas] = formulas.split("=")
            if column == 'balance':
                if formulas.find("-(") != -1:
                    formulas = formulas.strip("-(")
                    formulas = formulas.strip(")")
                    formulas = formulas.replace("+", "tmp_val")
                    formulas = formulas.replace("-", "+")
                    formulas = formulas.replace("tmp_val", "-")
                    formulas = "-" + formulas
                for formula in formulas.split('.balance'):
                    if formula and formula in ('sum', '-sum') != -1:
                        if not report.domain:
                            raise ValidationError(_("The report '%s' should have domain." % report.name))
                        domain = report.domain and ast.literal_eval(ustr(report.domain))
                        accounts = self.env['account.account'].search(domain)
                        report_account = self._compute_account_balance(accounts)
                        for value in report_account.values():
                            for field in fields:
                                if field not in ['amort', 'brut', 'net']:
                                    if formula[0] == "-" and field == 'balance':
                                        res[report.id][field] -= value.get(field)
                                    else:
                                        res[report.id][field] += value.get(field)
                    elif formula:
                        code = formula.replace("-", "").replace("+", "")
                        child = self.env["account.financial.report"].search([('code', '=', code)])
                        if len(child) > 1:
                            raise ValidationError(_('There is 2 reports line having the same code, please fix it.'))
                        res2 = self.compute_vals(child)
                        for key, value in res2.items():
                            for field in fields:
                                if field not in ['amort', 'brut', 'net']:
                                    if formula[0] == "-" and field == 'balance':
                                        res[report.id][field] -= value.get(field)
                                    else:
                                        res[report.id][field] += value[field]
                for formula in formulas.split('.credit'):
                    if formula and formula in ('sum', '-sum') != -1:
                        if not report.domain:
                            raise ValidationError(_("The report '%s' should have domain." % report.name))
                        domain = report.domain and ast.literal_eval(ustr(report.domain))
                        accounts = self.env['account.account'].search(domain)
                        report_account = self._compute_account_balance(accounts)
                        for value in report_account.values():
                            for field in fields:
                                if field not in ['amort', 'brut', 'net']:
                                    if formula[0] == "-" and field == 'credit':
                                        if value.get(field) < 0:
                                            res[report.id][field] -= value.get(field)
                                    else:
                                        if value.get(field) < 0:
                                            res[report.id][field] += value.get(field)
        return res

    # override _eval_formulas
    def _eval_formulas(self, reports, res={}, level=5):
        # calcul with domain
        for report in reports:
            if report.level == level:
                if report.formulas and report.domain:
                    domains = self._get_domains_expressions(report.domain)
                    formulas = self._get_formulas_expressions(report.formulas)
                    for formula, domain in zip(formulas, domains):
                        # ['brut = sum.debit']
                        f = formula.split('=')
                        f = [item.strip() for item in f]
                        field = f[0]
                        sum_field = f[-1].split('.')
                        sum_field = [item.strip() for item in sum_field]
                        accounts = self.env['account.account'].search(ast.literal_eval(ustr(domain)))
                        res[report.id]['account'] = self._compute_account_balance(accounts)
                        for value in res[report.id]['account'].values():
                            if (sum_field[-1] == 'debit'):
                                val = value.get('balance')
                                if val > 0:
                                    res[report.id][field] += val
                            else:
                                res[report.id][field] += value.get(sum_field[-1])
                # calcul without domain
                elif report.formulas and not report.domain:
                    formulas = self._get_formulas_expressions(report.formulas)
                    for formula in formulas:
                        f = formula.split('=')
                        f = [item.strip() for item in f]
                        field = f[0]
                        sum_fields = f[-1].split('+')
                        sum_fields = [item.strip() for item in sum_fields]
                        for sum_field in sum_fields:
                            sum_field = sum_field.split('.')
                            sum_field = [item.strip() for item in sum_field]
                            temp_report = next(x for x in reports if (x.code and x.code == sum_field[0]))
                            res[report.id][field] += res[temp_report.id][sum_field[-1]]
        return res

    def _compute_report_balance(self, reports):
        '''returns a dictionary with key=the ID of a record and value=the credit, debit and balance amount
           computed for this record. If the record is of type :
               'accounts' : it's the sum of the linked accounts
               'account_type' : it's the sum of leaf accoutns with such an account_type
               'account_report' : it's the amount of the related report
               'sum' : it's the sum of the children of this record (aka a 'view' record)'''
        res = {}
        fields = ['credit', 'debit', 'balance', 'amort', 'brut', 'net']
        for report in reports:
            if report.type not in ['report_mg_pl', 'report_mg_cf', 'report_mg_cp_p', 'product_details',
                                   'charge_details']:
                if report.id in res:
                    continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                res[report.id]['account'] = self._compute_account_balance(report.account_ids)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field, 0.0)
            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                accounts = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
                res[report.id]['account'] = self._compute_account_balance(accounts)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field, 0.0)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                res2 = self._compute_report_balance(report.account_report_id)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value.get(field, 0.0)
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value.get(field, 0.0)
            elif report.type in ['report_mg_pl', 'report_mg_cf', 'report_mg_cp_p', 'product_details', 'charge_details']:
                res2 = self.compute_vals(report)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value.get(field, 0.0)
        return res

    def get_account_lines(self, data):
        lines = []
        account_report = self.env['account.financial.report'].search([('id', '=', data['account_report_id'][0])])
        child_reports = account_report._get_children_by_order()
        res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports)
        # ADD HRN remove first parent report
        if res.get(data['account_report_id'][0], False):
            del res[data['account_report_id'][0]]
        # END
        if data['type_financial_report_mg'] == 'balance_sheet':
            res = self.with_context(data.get('used_context'))._eval_formulas(child_reports, res, 5)
            res = self.with_context(data.get('used_context'))._eval_formulas(child_reports, res, 4)
            res = self.with_context(data.get('used_context'))._eval_formulas(child_reports, res, 3)
            res = self.with_context(data.get('used_context'))._eval_formulas(child_reports, res, 2)
            res = self.with_context(data.get('used_context'))._eval_formulas(child_reports, res, 1)
        if data['enable_filter']:
            comparison_res = self.with_context(data.get('comparison_context'))._compute_report_balance(child_reports)
            # ADD HRN remove first parent report
            if comparison_res.get(data['account_report_id'][0], False):
                del comparison_res[data['account_report_id'][0]]
            # END
            if data['type_financial_report_mg'] == 'balance_sheet':
                comparison_res = self.with_context(data.get('comparison_context'))._eval_formulas(
                    child_reports, comparison_res, 5)
                comparison_res = self.with_context(data.get('comparison_context'))._eval_formulas(
                    child_reports, comparison_res, 4)
                comparison_res = self.with_context(data.get('comparison_context'))._eval_formulas(
                    child_reports, comparison_res, 3)
                comparison_res = self.with_context(data.get('comparison_context'))._eval_formulas(
                    child_reports, comparison_res, 2)
                comparison_res = self.with_context(data.get('comparison_context'))._eval_formulas(
                    child_reports, comparison_res, 1)
                for report_id, value in comparison_res.items():
                    res[report_id]['comp_bal'] = (value['brut'] * float(1)) - abs(value['amort'] * float(1))
                    report_acc = res[report_id].get('account')
                    if report_acc:
                        for account_id, val in comparison_res[report_id].get('account').items():
                            report_acc[account_id]['comp_bal'] = val['balance']
            else:
                for report_id, value in comparison_res.items():
                    res[report_id]['comp_bal'] = value['balance']
                    report_acc = res[report_id].get('account')
                    if report_acc:
                        for account_id, val in comparison_res[report_id].get('account').items():
                            report_acc[account_id]['comp_bal'] = val['balance']
        for report in child_reports:
            # ADD HRN remove first parent report
            if report.id == data['account_report_id'][0]:
                continue
            # END
            # Customize code for active balance sheet ['brut','amorti']
            vals = {
                'name': report.name,
                'balance': res[report.id]['balance'] * float(report.sign),
                'net': res[report.id]['brut'] * float(1) - abs(res[report.id]['amort'] * float(1)) or 0,
                'brut': res[report.id]['brut'] * float(1) or 0,
                'amorti': res[report.id]['amort'] * float(1) or 0,
                'type': 'report',
                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                'account_type': report.type or False,  # used to underline the financial report balances
                'hidden': report.is_hidden,
            }
            if data['debit_credit']:
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']
            if data['enable_filter'] and data['type_financial_report_mg'] == 'balance_sheet':
                vals['balance_cmp'] = res[report.id]['comp_bal']
            if data['enable_filter'] and data['type_financial_report_mg'] != 'balance_sheet':
                vals['balance_cmp'] = res[report.id]['comp_bal'] * float(report.sign)

            lines.append(vals)
            if report.display_detail == 'no_detail':
                # the rest of the loop is used to display the details of the financial report, so it's not needed here.
                continue
            if res[report.id].get('account'):
                sub_lines = []
                for account_id, value in res[report.id]['account'].items():
                    # if there are accounts to display, we add them to the lines with a level equals to their level in
                    # the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                    # financial reports for Assets, liabilities...)
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    vals = {
                        'name': account.code + ' ' + account.name,
                        'balance': value['balance'] * float(report.sign) or 0.0,
                        'type': 'account',
                        'level': report.display_detail == 'detail_with_hierarchy' and 4,
                        'account_type': account.internal_type,
                    }
                    if data['debit_credit']:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not account.company_id.currency_id.is_zero(
                                vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
                            flag = True
                    if not account.company_id.currency_id.is_zero(vals['balance']):
                        flag = True
                    if data['enable_filter'] and data['type_financial_report_mg'] != 'balance_sheet':
                        vals['balance_cmp'] = value['comp_bal'] * float(report.sign)
                        if not account.company_id.currency_id.is_zero(vals['balance_cmp']):
                            flag = True
                    if data['enable_filter'] and data['type_financial_report_mg'] == 'balance_sheet':
                        vals['balance_cmp'] = value['comp_bal']
                        if not account.company_id.currency_id.is_zero(vals['balance_cmp']):
                            flag = True
                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
        return lines

    def _get_formulas_expressions(self, global_expression):
        expressions = []
        if global_expression.split(';'):
            expressions = global_expression.split(';')
        else:
            expressions.append(global_expression)
        expressions = [item.strip() for item in expressions]
        return expressions

    def _get_domains_expressions(self, global_expression):
        dict = {
            'brut': 0,
            'amort': 1,
        }
        expressions = []
        try:
            for expression in global_expression.split(";"):
                expressions.insert(dict[expression.split("=")[0].strip()], expression.split("=", 1)[1].strip())
        except KeyError:
            keys = [key for key in dict.keys()]
            exceptions.ValidationError(_("Please, check your domains. Make sure that your keys are in: %s") % keys)
        return expressions
