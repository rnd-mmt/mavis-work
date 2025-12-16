# -*- coding: utf-8 -*-
from odoo import api, models
import logging

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _rewrite_account_code_domain(self, domain):
        """
        Ne modifie le domaine QUE si :
        - Il y a une recherche globale avec un nombre
        - ET qu'il n'y a PAS déjà un filtre strict sur account_id (= un ID précis → drill-down)
        """
        if not domain:
            return domain

        # Détecter si on est en drill-down : présence de ('account_id', '=', integer)
        has_drilldown = any(
            isinstance(leaf, (list, tuple)) and len(leaf) == 3 and
            leaf[0] == 'account_id' and leaf[1] == '=' and isinstance(leaf[2], int)
            for leaf in domain
        )

        # Si on est en drill-down → on ne touche à rien
        if has_drilldown:
            return domain

        new_domain = []
        i = 0
        while i < len(domain):
            item = domain[i]

            if item in ('&', '|', '!'):
                new_domain.append(item)
                i += 1
            elif isinstance(item, (list, tuple)) and len(item) == 3:
                field, operator, value = item
                _logger.debug("Traitement du domaine item=%s", item)
                
                # 1. Recherche sur account_id avec valeur numérique
                if field in ('account_id', 'account_id.code') and isinstance(value, str):
                    _logger.debug("------------------**--------2----------------")
                    
                    val = value.strip()
                    if val.isdigit():
                        # Remplace par recherche "commence par" sur le code
                        new_domain.append(['account_id.code', '=ilike', val + '%'])
                        _logger.info("Recherche compte → modifié %s en ['account_id.code', '=ilike', '%s%%']", item, val)
                        i += 1
                        continue

                # 2. CORRECTION : Recherche spécifique pour compte racine
                # Le champ est 'account_root_id' selon les logs
                if field == 'account_root_id' and isinstance(value, str):
                    _logger.debug("------------------**--------3---------------- Recherche racine détectée")
                    
                    val = value.strip()
                    if val.isdigit():
                        # Option A: Si account_root_id est un Many2one vers account.account
                        # Recherche "commence par" sur les 2 premiers caractères du code
                        new_domain.append(['account_id.code', '=like', val[:2] + '%'])
                        
                        # OU Option B: Si account_root_id est un champ calculé avec le code racine
                        # new_domain.append(['account_root_id.code', '=like', val + '%'])
                        
                        _logger.info("Recherche racine → modifié %s en ['account_id.code', '=like', '%s%%']", item, val[:2])
                        i += 1
                        continue

                # 3. Si vous avez d'autres champs pour la recherche racine
                if field in ('root_account_id', 'account_root_code', 'root_code') and isinstance(value, str):
                    _logger.debug("------------------**--------4---------------- Autre recherche racine")
                    
                    val = value.strip()
                    if val.isdigit():
                        # Même logique
                        new_domain.append(['account_id.code', '=like', val[:2] + '%'])
                        _logger.info("Recherche racine (autre) → modifié %s en ['account_id.code', '=like', '%s%%']", item, val[:2])
                        i += 1
                        continue

                new_domain.append(item)
                i += 1
            else:
                new_domain.append(item)
                i += 1

        _logger.debug("Domaine final: %s", new_domain)
        return new_domain

    @api.model
    def search(self, domain, *args, **kwargs):
        domain = self._rewrite_account_code_domain(domain or [])
        return super().search(domain, *args, **kwargs)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain = self._rewrite_account_code_domain(domain or [])
        return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)
    