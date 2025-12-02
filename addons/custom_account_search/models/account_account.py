import logging
from odoo import models, api

_logger = logging.getLogger(__name__)

class AccountAccount(models.Model):
    _inherit = 'account.account'
    
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        _logger.warning("-----1------- search appelé avec args=%s", args)

        # Collecter tous les codes présents dans les triplets (field, op, value)
        code_values = []
        for domain in args:
            if isinstance(domain, (list, tuple)) and len(domain) == 3:
                field, op, value = domain
                if field == 'code' and value:
                # if field == 'code' and op in ('like') and isinstance(value, str):
                    value_str = str(value).strip().rstrip('%')
                    # Extraire tous les codes séparés par espaces (ex: "10 25")
                    codes = [v.strip() for v in value_str.split() if v.strip().isdigit()]
                    code_values.extend(codes)

        # Si on a des codes → construire un domaine OR correctement
        if code_values:
            code_domains = [['code', '=like', f"{code}%"] for code in code_values]

            if len(code_domains) == 1:
                # Un seul triplet → search attend une liste d'éléments (donc une liste contenant le triplet)
                new_args = [code_domains[0]]     # -> [['code','...']]
            else:
                # Plusieurs codes → construire une liste commençant par les '|' successifs
                # Exemple pour 3 codes: ['|', '|', ['code','10%'], ['code','25%'], ['code','12%']]
                or_tokens = []
                for _ in range(len(code_domains) - 1):
                    or_tokens.append('|')
                or_tokens.extend(code_domains)
                new_args = or_tokens            # <-- NE PAS envelopper dans une autre liste
            _logger.warning("-----2------ Domaine reconstruit pour codes: %s", new_args)
        else:
            # Aucun code détecté → on laisse args tels quels (mais on normalise tuples -> lists)
            new_args = [list(d) if isinstance(d, tuple) else d for d in args]
            _logger.warning("-----3------- Pas de code détecté, new_args = %s", new_args)

        _logger.warning("------4------ Appel final search avec new_args=%s", new_args)
        return super(AccountAccount, self).search(new_args, offset=offset, limit=limit, order=order, count=count)
