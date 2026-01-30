# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from datetime import datetime

from odoo import models, fields, api


class InterCompanyTransferLogBookEpt(models.Model):
    """
    For managing the Logs of Inter Company and Internal Warehouse Transfers.
    @author: Maulik Barad.
    """
    _name = "inter.company.transfer.log.book.ept"
    _description = "Inter Company Transfer Log Book"

    name = fields.Char(copy=False)
    ict_log_date = fields.Datetime(string="Log Date", copy=False)
    ict_process = fields.Selection([("inter.company.transfer.ept", "Inter Company Transfer")], string="Application")
    operation = fields.Selection([("import", "Import"), ("ict", "ICT"), ("reverse", "Reverse Transfer"),
                                  ("invoice", "Invoice"), ("auto", "Auto Generate ICT/IWT")])
    inter_company_transfer_id = fields.Many2one("inter.company.transfer.ept")
    ict_log_line_ids = fields.One2many("inter.company.transfer.log.line.ept", "ict_log_id")

    @api.model
    def create_ict_log_book(self, record, operation_type):
        """
        Creates a new log book.
        @author: Maulik Barad.
        """
        log_book = self.search([("inter_company_transfer_id", "=", record.id)], limit=1)
        if not log_book:
            record_name = 'LOG/' + record._name + '/' + str(record.id)
            sequence_id = self.env.ref('intercompany_transaction_ept.inter_company_process_log_seq').ids
            if sequence_id:
                record_name = self.env['ir.sequence'].browse(sequence_id).next_by_id()
            log_vals = {
                'name': record_name,
                'ict_log_date': datetime.now(),
                'ict_process': record._name,
                'operation': operation_type,
                'inter_company_transfer_id': record.id
            }
            log_book = self.create(log_vals)
        return log_book

    def post_log_line(self, message, log_type='error'):
        """
        Creates log line for log book.
        @author: Maulik Barad.
        @param message: Reason of the log.
        @param log_type: Type of the log.
        """
        log_line_vals = {
            'ict_message': message,
            'ict_log_type': log_type,
            'ict_log_id': self.id,
        }
        self.env['inter.company.transfer.log.line.ept'].create(log_line_vals)
        return True
