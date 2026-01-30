# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _check_balanced(self):
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        '''
        moves = self.filtered(lambda move: move.line_ids)
        if not moves:
            return

        for move in self:
            if move.state == 'posted':
                self.env['account.move.line'].flush(self.env['account.move.line']._fields)
                self.env['account.move'].flush(['journal_id'])
                self._cr.execute('''
                    SELECT line.move_id, ROUND(SUM(line.debit - line.credit), currency.decimal_places)
                    FROM account_move_line line
                    JOIN account_move move ON move.id = line.move_id
                    JOIN account_journal journal ON journal.id = move.journal_id
                    JOIN res_company company ON company.id = journal.company_id
                    JOIN res_currency currency ON currency.id = company.currency_id
                    WHERE line.move_id IN %s
                    GROUP BY line.move_id, currency.decimal_places
                    HAVING ROUND(SUM(line.debit - line.credit), currency.decimal_places) != 0.0;
                ''', [tuple(move.ids)])

                query_res = self._cr.fetchall()
                if query_res:
                    ids = [res[0] for res in query_res]
                    sums = [res[1] for res in query_res]
                    raise UserError(
                        _("Cannot create unbalanced journal entry. Ids: %s\nDifferences debit - credit: %s") % (
                            ids, sums))


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    move_id = fields.Many2one('account.move', string='Journal Entry',
                              index=True, required=True, readonly=False, auto_join=True, ondelete="cascade",
                              check_company=True,
                              help="The move of this entry line.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref') and not vals.get('move_id'):
                move = self.env['account.move'].search([('ref', '=', vals.get('ref'))], limit=1)
                if move:
                    vals.update({'move_id': move.id})
                    return super(AccountMoveLine, self).with_context(check_move_validity=False).create(vals_list)
                else:
                    _logger.debug('Journal entry reference not found, create journal entry first.')
        return super(AccountMoveLine, self).create(vals_list)

    @api.onchange('currency_id')
    def _onchange_currency(self):
        for line in self:
            if line.move_id:
                company = line.move_id.company_id

                if line.move_id.is_invoice(include_receipts=True):
                    line._onchange_price_subtotal()
                elif not line.move_id.reversed_entry_id:
                    balance = line.currency_id._convert(line.amount_currency, company.currency_id, company,
                                                        line.move_id.date or fields.Date.context_today(line))
                    line.debit = balance if balance > 0.0 else 0.0
                    line.credit = -balance if balance < 0.0 else 0.0

    @api.onchange('amount_currency')
    def _onchange_amount_currency(self):
        for line in self:
            if line.move_id:
                company = line.move_id.company_id
                balance = line.currency_id._convert(line.amount_currency, company.currency_id, company,
                                                    line.move_id.date)
                line.debit = balance if balance > 0.0 else 0.0
                line.credit = -balance if balance < 0.0 else 0.0

                if not line.move_id.is_invoice(include_receipts=True):
                    continue

                line.update(line._get_fields_onchange_balance())
                line.update(line._get_price_total_and_subtotal())
