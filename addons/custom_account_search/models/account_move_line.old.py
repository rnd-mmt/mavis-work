# -*- coding: utf-8 -*-
from odoo import api, models
import logging

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        
        new_args = []
        _logger.warning("////////////---///////////// [account.move.line] search appelé avec args=%s", args)

        for domain in args:
            # Domaine simple [champ, opérateur, valeur]
            # _logger.warning("///////////-------////////////// Traitement du domaine: %s", domain)
            if isinstance(domain, (list, tuple)) and len(domain) == 3:
                field, op, value = domain
                value_str = str(value).strip() if value else ""
                if field in ["account_id", "account_id.code", "code"] and value_str.isdigit():
                    new_args.append(['account_id.code', '=like', f"{value_str}%"])
                else:
                    new_args.append(domain)
            elif domain in ['&', '|', '!']:
                # Ajouter seulement si précédemment il y a deux conditions pour combiner
                # Sinon on ignore pour éviter la syntaxe invalide
                if len(new_args) >= 2:
                    new_args.append(domain)
            else:
                new_args.append(domain)
                # _logger.warning("///////////////////////// Domaine logique ajouté: %s", domain)

        # _logger.warning("///////////////////////// Appel final [account.move.line] avec new_args=%s", new_args)
        return super(AccountMoveLine, self).search(new_args, offset=offset, limit=limit, order=order, count=count)
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        _logger.warning("//////////// [****] ///////////// read_group appelé avec domain=%s, groupby=%s", domain, groupby)

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
            _logger.warning("[****] Comptes trouvés pour les codes %s : %s", code_values, account_ids)
            # Ajouter un filtre supplémentaire
            if not account_ids:
                original_domain.append(['account_id', 'in', [0]])
            else:
                original_domain.append(['account_id', 'in', account_ids])

        _logger.warning("[****] read_group final domain=%s", original_domain)

        return super(AccountMoveLine, self).read_group(
            original_domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )
