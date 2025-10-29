import logging
from odoo import models, api

_logger = logging.getLogger(__name__)

class AccountAccount(models.Model):
    _inherit = 'account.account'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
        Ajuste la recherche du plan comptable :
        - Si l'utilisateur tape un code numérique, on ne cherche que les comptes
          dont le code COMMENCE par ce nombre.
        - La recherche par type ou autres champs reste inchangée.
        """
        new_args = []
        is_code_search = False

        _logger.warning("------------ search appelé avec args=%s", args)

        # Détecter si c'est une recherche par code uniquement
        for domain in args:
            if isinstance(domain, list) and len(domain) == 3:
                field, op, value = domain
                value_str = str(value).strip() if value else ""
                value_num = value_str.rstrip('%')
                if field == "code" and value_num.isdigit():
                    is_code_search = True
                    break

        for domain in args:
            # Domaine simple [field, operator, value]
            if isinstance(domain, list) and len(domain) == 3:
                field, op, value = domain
                value_str = str(value).strip() if value else ""
                value_num = value_str.rstrip('%')
                    
                if is_code_search:
                    # On ne garde que le code, ignore name et autres
                    if field == "code" and value_num.isdigit():
                        new_domain = [field, "=like", f"{value_num}%"]
                        new_args.append(new_domain)
                        _logger.warning("------------ Recherche ajustée: %s", new_domain)
                    else:
                        _logger.warning("------------ Domaine ignoré pour recherche code: %s", domain)
                else:
                    # Recherche normale pour autres cas (type, name, etc.)
                    new_args.append(domain)
                    _logger.warning("------------ Domaine inchangé ajouté: %s", domain)
            else:
                # Ignorer les opérateurs logiques si recherche code
                if is_code_search:
                    _logger.warning("------------ Opérateur logique ignoré pour recherche code: %s", domain)
                else:
                    new_args.append(domain)
                    _logger.warning("------------ Domaine logique ajouté: %s", domain)

        _logger.warning("------------ Appel final search avec new_args=%s", new_args)
        return super(AccountAccount, self).search(new_args, offset=offset, limit=limit, order=order, count=count)
    
    def test_logging(self):
        _logger.warning("[OK] test_logging appelé !")
        return True
