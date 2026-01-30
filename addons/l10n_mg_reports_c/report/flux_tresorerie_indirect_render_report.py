# -*- coding: utf-8 -*-
import calendar
from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo import models


class ParticularReport(models.AbstractModel):
    _name = 'report.l10n_mg_reports_c.indirect_flux_report_template'

    def _get_report_values(self, docids, data=None):

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        is_custom = data.get('is_custom', False)
        domain = []
        domain_prec = []
        start_date_ef = date.today()
        end_date_ef = date.today()
        if is_custom:
            custom_date = data.get('start_date', datetime.now()), data.get('end_date', datetime.now())
            start_date_prec = datetime.strptime(str(custom_date[0]), '%Y-%m-%d') - relativedelta(years=1)
            end_date_prec = datetime.strptime(str(custom_date[1]), '%Y-%m-%d') - relativedelta(years=1)
            custom_date_prec = start_date_prec, end_date_prec
            domain = [('date', '>=', custom_date[0]), ('date', '<=', custom_date[1])]
            domain_prec = [('date', '>=', custom_date_prec[0]), ('date', '<=', custom_date_prec[1])]
            start_date_ef = custom_date[0]
            end_date_ef = custom_date[1]
        else:
            period = str(data.get('period')).split('_')
            code, t_code = period[0], period[1]
            today = date.today()
            month_before = date.today() - relativedelta(months=1)
            if code == '1':
                first_month = today.replace(day=1) if t_code == '1' else month_before.replace(day=1)
                last_month = today.replace(
                    day=calendar.monthrange(today.year, today.month)[1]) if t_code == 1 else month_before.replace(
                    day=calendar.monthrange(month_before.year, month_before.month)[1])
                first_month_prec = first_month - relativedelta(months=1)
                last_month_prec = last_month - relativedelta(months=1)
                domain = [('date', '>=', first_month), ('date', '<=', last_month)]
                domain_prec = [('date', '>=', first_month_prec), ('date', '<=', last_month_prec)]
                start_date_ef = first_month
                end_date_ef = last_month

            elif code == '2':
                tab = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4]
                quarter = tab[today.month - 1]
                if t_code == '1':
                    if quarter == 1:
                        date_first = date(today.year, 1, 1)
                        date_end = date(today.year, 3, 31)
                    elif quarter == 2:
                        date_first = date(today.year, 4, 1)
                        date_end = date(today.year, 6, 30)
                    elif quarter == 3:
                        date_first = date(today.year, 7, 1)
                        date_end = date(today.year, 9, 30)
                    else:
                        date_first = date(today.year, 10, 1)
                        date_end = date(today.year, 12, 31)
                else:
                    if quarter == 1:
                        date_first = date(today.year - 1, 10, 1)
                        date_end = date(today.year - 1, 12, 31)
                    elif quarter == 2:
                        date_first = date(today.year, 1, 1)
                        date_end = date(today.year, 3, 31)
                    elif quarter == 3:
                        date_first = date(today.year, 4, 1)
                        date_end = date(today.year, 6, 30)
                    else:
                        date_first = date(today.year, 7, 1)
                        date_end = date(today.year, 9, 30)
                domain = [('date', '>=', date_first), ('date', '<=', date_end)]
                domain_prec = [('date', '>=', date_first - relativedelta(months=3)),
                               ('date', '<=', date_end - relativedelta(months=3))]
                start_date_ef = date_first
                end_date_ef = date_end

            elif code == '3':
                years = today.year if t_code == '1' else today.year - 1
                date_first = date(years, 1, 1)
                date_end = date(years, 12, 31)
                domain = [('date', '>=', date_first), ('date', '<=', date_end)]
                domain_prec = [('date', '>=', date_first - relativedelta(years=1)),
                               ('date', '<=', date_end - relativedelta(years=1))]
                start_date_ef = date_first
                end_date_ef = date_end
        start_date_ef = datetime.strptime(str(start_date_ef), '%Y-%m-%d').strftime('%d/%m/%Y')
        end_date_ef = datetime.strptime(str(end_date_ef), '%Y-%m-%d').strftime('%d/%m/%Y')
        account_moves = self.env['account.move.line'].search(domain)
        account_moves_prec = self.env['account.move.line'].search(domain_prec)
        result = {
            'resultat_net': 0, 'amort_provision': 0, 'variation_prov': 0, 'variation_impot': 0, 'variation_stock': 0,
            'variation_stock_n':0,'variation_stock_n_1':0,'variation_client_creance_n':0,'variation_client_creance_n_1':0,
            'variation_client_creance': 0, 'variation_frns_dette': 0, 'moins_plus_value': 0, 'flux_activite': 0,
            'decaiss_acqui_immo': 0, 'encaiss_cess_immo': 0, 'incidence_var': 0, 'flux_invest': 0,
            'dividende': 0, 'augment_num': 0, 'ecart_eval': 0, 'elimination': 0, 'emission_emprunt': 0,
            'remb_emprunt': 0, 'flux_finance': 0, 'variation_periode_abc': 0,'subv_invest':0,
            'tresorerie_ouv': 0, 'tresorerie_clot': 0, 'incidence_dev': 0, 'variation_periode': 0,
            'mat_four_brut': 0, 'mat_four_net': 0, 'mat_four_amort': 0, 'mat_four_brut_prec': 0, 'mat_four_net_prec': 0,
            'mat_four_amort_prec': 0, 'cours_prod_brut': 0, 'cours_prod_amort': 0, 'cours_prod_net': 0,
            'prod_fini_brut': 0, 'prod_fini_amort': 0, 'prod_fini_net': 0, 'creance_brut': 0, 'creance_amort': 0,
        }
        ibs, etat_tva, tva_achat_import, tva_achat_locaux, tva_charge_exploit, tva_intermit_ded, tva_ded_reg, iri, credit_tva = 0, 0, 0, 0, 0, 0, 0, 0, 0
        client_locaux, client_demarcheur, frns_debiteur, client_etranger = 0, 0, 0, 0
        remu_pers, avance_acompte, avance15, mois13, avance_spec, avance_sco, cession_couv, conge_ap = 0, 0, 0, 0, 0, 0, 0, 0
        EMBAR, FEAAS, FRNSETR, RAMAHOLIMIHASO, NIRINA_RAMANANDRAIBE, CSCIMMO, TRANSNS, SANTA, RAMAEXPORT_TANA, RAMAEXPORT_MANAKARA = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        RAMAEXPORT_BETAINOMBY, RAMAEXPORT_AMBANJA, RAMAEXPORT_TRANSIT_TVE, BESOA, DIVS, MADAME_ANNIE_RIANA, SME, DIVPC, RENE_JULIEN_CACAO, LOVASOA = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        MANOFI, ETS_JOSEPH_RAMANANDRAIBE, GHM, ZAFITSARA, SUCCESS_JEAN_RAMANANDRAIBE, MAKASSAR_TOURS, AMIGO_HOTEL, MIKEA_LODGE, REPORT_MAVA, GEDECO = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        ROSSET_DIVERS, SAGRIMAD, SOAMANANTOMBO, COMPTE_FAMILLE, RAINBOW_CENTER, SANEX, RBM, RABEARIVELO, CHARAP, CPTE_ATTENTE = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        CHARCAV, CH_EXPLOIT = 0, 0
        for account_prec in account_moves_prec.filtered(lambda a: a.parent_state=='posted'):
            current_code_prec = account_prec.account_id.code
            # Variation des provision
            if current_code_prec[:2] in ['48']:
                result['variation_prov'] -= account_prec.balance

            # Variation des impots différes
            if current_code_prec[:3] in ['133']:
                result['variation_impot'] -= account_prec.credit

            # Variation de stocks
            if current_code_prec[:2] in ['31', '32', '33', '34', '35', '37', '38']:
                result['variation_stock_n_1'] += account_prec.debit
            if current_code_prec[:3] in ['391', '392', '393', '394', '395', '397', '398']:
                result['variation_stock_n_1'] -= account_prec.credit

            #Variation des clients et autres creances
            if current_code_prec[:2] in ['40', '41', '42', '43', '44', '45', '46']:
                result['variation_client_creance_n_1'] += account_prec.debit
            if current_code_prec[:3] in ['491']:
                result['variation_client_creance_n_1'] -= account_prec.balance

            #Variation des fournisseurs et autres dettes
            if current_code_prec[:2] in ['40', '41', '42', '43', '44', '45', '46']:
                result['variation_frns_dette'] -= account_prec.credit

            # Decaissement sur acquisition d'immobilisations
            if current_code_prec[:2] in ['20', '21']:
                result['decaiss_acqui_immo'] -= account_prec.debit

            #Encaissement sur cession d'immobilisations
            if current_code_prec[:2] in ['20', '21']:
                result['encaiss_cess_immo'] -= account_prec.credit

            # Augmentation de capital en numeraire
            if current_code_prec[:4] in ['1013']:
                result['augment_num'] -= account_prec.balance

            #Emission d'emprunt
            if current_code_prec[:2] in ['16', '17']:
                result['emission_emprunt'] -= account_prec.credit

            #Remboursement d'emprunt
            if current_code_prec[:2] in ['16', '17']:
                result['remb_emprunt'] -= account_prec.debit

            #Subvention d'investissement
            if current_code_prec[:2] in ['15']:
                result['subv_invest'] -= account_prec.balance

            #Tresorerie d'ouverture
            if current_code_prec[:1] == '5':
                res = -account_prec.balance if account_prec.balance < 0 else 0
                result['tresorerie_ouv'] -= res
                rep = account_prec.balance if account_prec.balance > 0 else 0
                result['tresorerie_ouv'] += rep
            # if current_code_prec[:2] in ['31', '32']:
            #     result['mat_four_brut_prec'] += account_prec.balance
            #     result['mat_four_net_prec'] = result['mat_four_brut_prec'] + result['mat_four_amort_prec']
        for account in account_moves.filtered(lambda a: a.parent_state =='posted'):
            current_code = account.account_id.code
            # RESULTAT
            if current_code[:1] in ['6']:
                result['resultat_net'] -= account.balance
            if current_code[:1] in ['7']:
                result['resultat_net'] -= account.balance

            # Amortissement et provision
            if current_code[:2] == '68':
                result['amort_provision'] -= account.balance

            # Variation des provision
            if current_code[:2] in ['48']:
                result['variation_prov'] += account.balance

            # Variation des impots différes
            if current_code[:3] in['133']:
                result['variation_impot']+=account.credit

            # Variation de stocks
            if current_code[:2] in ['31','32','33','34','35','37','38']:
                result['variation_stock_n'] += account.debit
            if current_code[:3] in ['391','392','393','394','395','397','398']:
                result['variation_stock_n'] -= account.credit

            # Variation des clients et autres creances
            if current_code[:2] in ['40', '41', '42', '43', '44', '45', '46']:
                result['variation_client_creance_n'] += account.debit
            if current_code[:3] in ['491']:
                result['variation_client_creance_n'] -= account.balance

            # Variation des fournisseurs et autres dettes
            if current_code[:2] in ['40', '41', '42', '43', '44', '45', '46']:
                result['variation_frns_dette'] += account.credit

            #Moins ou Plus values de cession nettes d'impots
            if current_code[:3] in ['752']:
                result['moins_plus_value'] += account.balance
            if current_code[:3] in ['652']:
                result['moins_plus_value'] -= account.balance

            # Decaissement sur acquisition d'immobilisations
            if current_code[:2] in ['20', '21']:
                result['decaiss_acqui_immo'] += account.debit

            #Encaissement sur cession d'immobilisations
            if current_code[:2] in ['20', '21']:
                result['encaiss_cess_immo'] += account.credit

            # Dividende versee aux actionnaires
            if current_code[:3] in ['457']:
                result['dividende'] += account.balance

            #Augmentation de capital en numeraire
            if current_code[:4] in ['1013']:
                result['augment_num'] +=account.balance

            # Emission d'emprunt
            if current_code[:2] in ['16', '17']:
                result['emission_emprunt'] += account.credit

            #Remboursement d'emprunt
            if current_code[:2] in ['16','17']:
                result['remb_emprunt'] += account.debit

            # Subvention d'investissement
            if current_code[:2] in ['15']:
                result['subv_invest'] += account.balance

            # Tresorerie de cloture
            if current_code[:1] == '5':
                res = -account.balance if account.balance < 0 else 0
                result['tresorerie_clot'] -= res
                rep = account.balance if account.balance > 0 else 0
                result['tresorerie_clot'] += rep


        result['variation_client_creance'] = result['variation_client_creance_n_1'] - result['variation_client_creance_n']

        result['cours_prod_net'] = result['cours_prod_brut'] + result['cours_prod_amort']
        result['variation_stock'] = result['variation_stock_n_1'] - result['variation_stock_n']
        result['flux_activite'] = result['resultat_net'] + result['amort_provision'] + result['variation_prov'] + \
                                  result['variation_impot'] + result['variation_stock'] + result[
                                      'variation_client_creance'] + result['variation_frns_dette'] + result[
                                      'moins_plus_value']
        result['flux_invest'] = -result['decaiss_acqui_immo'] + result['encaiss_cess_immo'] + result['incidence_var']
        result['flux_finance'] = result['dividende'] + result['augment_num'] + result['ecart_eval'] + result[
            'elimination'] + result['emission_emprunt'] + result['remb_emprunt']
        result['variation_periode_abc'] = result['flux_activite'] + result['flux_finance'] + result['flux_invest']
        result['variation_periode'] = result['tresorerie_clot'] - result['tresorerie_ouv'] + result['incidence_dev']

        docargs = {
            'doc_ids': docids,
            'doc_model': model,
            'docs': self,
            'account_moves': account_moves,
            'result': result,
            'start_date_ef': start_date_ef,
            'end_date_ef': end_date_ef
        }
        return docargs
