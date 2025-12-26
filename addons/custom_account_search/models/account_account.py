import logging
from odoo import models, api

_logger = logging.getLogger(__name__)

class AccountAccount(models.Model):
    _inherit = 'account.account'

    def _fix_code_domain(self, domain):
        _logger.debug("Fixing code domain: %s", domain)

        new_domain = []
        code_domain = []
        structural_domain = []
        has_precise_code_domain = False

        for d in domain:
            if not isinstance(d, (list, tuple)) or len(d) != 3:
                # opérateurs &, |
                new_domain.append(d)
                continue

            field, op, value = d
            _logger.debug("Processing domain element: %s", d)

            # Drill-down sur code
            if field == 'code' and op == '=like' and isinstance(value, str) and value.endswith('%'):
                _logger.debug("Drill-down on code detected → forcing ilike")
                code_domain.append(('code', '=ilike', value))
                has_precise_code_domain = True
                continue

            # 🔁 Filtre personnalisé : Code "contient"
            if field == 'code' and op in ('ilike', 'like') and isinstance(value, str):
                clean = value.strip()

                # supprimer les % éventuels
                clean = clean.strip('%')
                code_domain.append(('code', '=ilike', f'{clean}%'))
                has_precise_code_domain = True
                continue

            # Si drill-down → on IGNORE name
            if has_precise_code_domain and field == 'name':
                _logger.debug("Ignoring name condition due to drill-down")
                continue

            # Si drill-down → on IGNORE les recherches utilisateur
            if has_precise_code_domain and field in ('code', 'name') and op in ('ilike', '=ilike'):
                _logger.debug("Ignoring user search condition: %s", d)
                continue

            # Contraintes HAFA
            if field in ('root_id', 'company_id'):
                structural_domain.append(d)
                continue

            new_domain.append(d)

        # Drill-down prioritaire
        if has_precise_code_domain:
            # AJOUTER-na an'ilay operateur OR iny fotsiny sisa
            if len(code_domain) == 1:
                code_or_domain = code_domain
            else:
                code_or_domain = []
                for _ in range(len(code_domain) - 1):
                    code_or_domain.append('|')
                code_or_domain.extend(code_domain)

            # AND avec les contraintes structurelles
            if structural_domain:
                final_domain = ['&'] + code_or_domain + structural_domain
            else:
                final_domain = code_or_domain

            _logger.debug("Final drill-down domain: %s", final_domain)
            return final_domain

        return domain

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        _logger.warning("search args=%s", args)
        args = self._fix_code_domain(args)
        return super().search(args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def read_group(self, domain, fields, groupby,
                offset=0, limit=None, orderby=False, lazy=True):

        _logger.warning("read_group domain=%s", domain)
        domain = self._fix_code_domain(domain)

        return super().read_group(
            domain, fields, groupby,
            offset=offset, limit=limit,
            orderby=orderby, lazy=lazy
        )
