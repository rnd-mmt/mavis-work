# -*- coding: utf-8 -*-
from odoo import api, models
import logging

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        
        new_args = []
        _logger.warning("///////////////////////// [account.move.line] search appelé avec args=%s", args)

        for domain in args:
            # Domaine simple [champ, opérateur, valeur]
            _logger.warning("///////////-------////////////// Traitement du domaine: %s", domain)
            if isinstance(domain, (list, tuple)) and len(domain) == 3:
                field, op, value = domain
                value_str = str(value).strip() if value else ""

                # 🎯 Si la recherche vient du champ "Compte" (relié à account_id)
                # et que l'utilisateur tape un code numérique
                if field in ["account_id", "account_id.code", "code"] and value_str.isdigit():
                    new_domain = ['account_id.code', '=like', f"{value_str}%"]
                    new_args.append(new_domain)
                    _logger.warning("///////////////////////// Domaine ajusté sur code du compte: %s", new_domain)
                else:
                    new_args.append(domain)
                    _logger.warning("///////////////////////// Domaine inchangé ajouté: %s", domain)
            else:
                # Les domaines logiques ('|', '&', '!') restent tels quels
                new_args.append(domain)
                _logger.warning("///////////////////////// Domaine logique ajouté: %s", domain)

        _logger.warning("///////////////////////// Appel final [account.move.line] avec new_args=%s", new_args)
        return super(AccountMoveLine, self).search(new_args, offset=offset, limit=limit, order=order, count=count)

    def test_logging(self):
        _logger.warning("[OK] ///////////////////////// test_logging appelé !")
        return True
