# -*- coding: utf-8 -*-
from odoo import api, models
import logging

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
 
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        _logger.warning("[****] read_group appelé avec domain=%s, groupby=%s", domain, groupby)

        # ON NE TOUCHE PAS AU DOMAIN D'ORIGINE
        original_domain = list(domain or [])

        code_values = []
        # Seulement détecter les codes, sans retirer les tokens
        for d in original_domain:
            if isinstance(d, (list, tuple)) and len(d) == 3:
                field, op, value = d
                if field in ("account_id", "account_id.code") and isinstance(value, str):
                    codes = [v.strip() for v in value.strip().split() if v.strip().isdigit()]
                    if codes:
                        code_values.extend(codes)

        # Si on a trouvé des codes
        if code_values:
            account_ids = []
            account_model = self.env['account.account']
            for code in code_values:
                accounts = account_model.search([('code', '=like', f"{code}%")])
                account_ids.extend(accounts.ids)

            account_ids = list(set(account_ids))

            # Ajouter un filtre supplémentaire
            if not account_ids:
                original_domain.append(['account_id', 'in', [0]])
            else:
                original_domain.append(['account_id', 'in', account_ids])

        _logger.warning("[****] read_group final domain=%s", original_domain)

        return super(AccountMoveLine, self).read_group(
            original_domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )
