# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class Pricelist(models.Model):
    _inherit = "product.pricelist"

    for_insurance = fields.Boolean("Pour assurance", default=False)
    code_desc = fields.Char("Code")
class ProductCategory(models.Model):
    _inherit = 'product.category'

    is_nomenclature = fields.Boolean("Est nomenclature", default=False)
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hospital_product_type = fields.Selection(selection_add=[('hospitalisation', 'Hospitalisation'),('vad', 'Visite à domicile')])

class ACSPatient(models.Model):
    _inherit = 'hms.patient'

    chk_print_service_card = fields.Boolean("Imprimé depuis service santé", defaut=False)

class ResCompany(models.Model):
    _inherit = 'res.company'

    is_consultation = fields.Boolean("Centre de consultation", default=False)
    is_surgery = fields.Boolean("Centre de Chirurgie", default=False)
    is_hospitalization = fields.Boolean("Centre d'hospitalisation", default=False)
    is_imaging = fields.Boolean("Centre d'imagerie médical", default=False)
    is_laboratory = fields.Boolean("Centre d' analyse de laboratoire", default=False)

class HealthService(models.Model):
    _name = 'acs.health_service'
    _description = 'Service Sante'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'acs.hms.mixin']
    _order = 'id desc'

    STATES = {'invoiced': [('readonly', True)], 'cancel': [('readonly', True)], 'confirm': [('readonly', True)], 'requested': [('readonly', True)], 'done': [('readonly', True)]}

    @api.depends('service_line', 'service_line.amount_total')
    def _get_total_price(self):
        for rec in self:
            rec.total_price = sum(line.amount_total for line in rec.service_line)

    def _smart_rec_count(self):
        for rec in self:
            invoice_count = self.env['account.move'].search_count([('patient_id', '=', self.patient_id.id)])
            rec.invoice_count = invoice_count

    @api.depends('service_line')
    def _get_nb_line(self):
        nb = []
        for rec in self:
            for line in rec.service_line:
                if not line.display_type:
                    nb.append(line.product.id)
            rec.nb_service_line = len(nb)

    @api.onchange('patient_id')
    def onchange_dob(self):
        if self.patient_id:
            self.birthday = self.patient_id.birthday or False
            self.pricelist_id = self.patient_id.property_product_pricelist or False
            self.invoice_to = self.patient_id.partner_id.id or False
            self.mobile = self.patient_id.mobile or False
            self.smi = self.patient_id.smi

    @api.onchange('service_line','service_line.product_type')
    def onchange_show_rdv(self):
        if self.service_line:
             for line in self.service_line:
                if line.product_type in ['consultation']:
                    self.show_rdv = True
                elif line.product_type in ['surgery']:
                    self.show_ot = True
                elif line.product_type == 'radio_int':
                    self.show_rdv = True
                    self.show_ot = True
                else:
                    pass

    @api.onchange('service_line')
    def onchange_show_pricelist(self):
        if not self.service_line:
            self.show_update_pricelist = True

    name = fields.Char(string='ID', readonly=True)
    desc = fields.Char(string='Description', states=STATES)
    patient_id = fields.Many2one('hms.patient', string='Patient', required=True, states=STATES , tracking=True)
    birthday = fields.Date(string='Date of Birth', tracking=True, readonly=True)
    mobile = fields.Char(string='Mobile', copy=False, states=STATES, tracking=True)
    company_id = fields.Many2one('res.company', ondelete='restrict', 
        string='Company', default=lambda self: self.env.company.id, states=STATES, tracking=True)

    service_date = fields.Date(string='Date', default=fields.Date.context_today, states=STATES, tracking=True)
    service_line = fields.One2many('acs.health_service.line', 'service_id', string='Ligne', help="Ligne de service", states=STATES)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('proforma', 'Demande de Proforma'),
        ('confirm', 'Confirmé'),
        ('invoiced', 'Facture créée'),
        ('requested', 'Demande examens créé'),
        ('cancel', 'Annulé'),
        ('editable', 'Rendre editable'),
        ('done', 'Fait'),
        ], string='State', default='draft', readonly=True, tracking=True)
    invoice_to = fields.Many2one('res.partner', string='Facturer à', states=STATES)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', check_company=True, states=STATES, tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Si vous modifiez la liste de prix, la facture correspondante sera affectée.")
    show_update_pricelist = fields.Boolean(string='Has Pricelist Changed',
                                           default=True)
    currency_id = fields.Many2one(related='pricelist_id.currency_id', depends=["pricelist_id"], store=True)
    #physician_id = fields.Many2one('hms.physician', string='Médecin prescripteur', ondelete='restrict', states=STATES, tracking=True)
    physician_id = fields.Many2many('hms.physician', string='Rendez-vous avec', ondelete='restrict', states=STATES, tracking=True)
    prescripteur = fields.Many2one('res.partner', string='Médecin prescripteur', domain=[('is_referring_doctor', '=', True)],states=STATES)
    nurse_id = fields.Many2one('hr.employee', string='Nurse', default=lambda self: self.env.user.employee_id.id,
                               states=STATES, tracking=True)
    total_price = fields.Float(compute="_get_total_price", string='Total', store=True, tracking=True)
    notes = fields.Text(string='Notes', states=STATES)
    invoice_id = fields.Many2one('account.move', string='Invoice', copy=False, states=STATES)
    ref_acte = fields.Char(string='Référence acte', readonly=True)
    invoice_count = fields.Integer(compute='_smart_rec_count', string='Facture')
    # =======INFO SUR PAIEMENT======
    mode_payd = fields.Many2one('account.journal', string="Mode de paiement",
                                   domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")
    ref_payd = fields.Char(string="Numéro de paiement")
    department_id = fields.Many2one('hr.department', ondelete="restrict",
                                    string='Department', domain=[('patient_department', '=', True)],
                                    states=STATES)
    #=======GROUPE DE REQUETE======
    is_group_request = fields.Boolean(default=False, states=STATES)
    group_patient_ids = fields.Many2many("hms.patient", "hms_patient_service_req_rel", "request_id", "patient_id",
                                         string="Autres patients du groupe", states=STATES)
    #======BANNIERE SMI=====
    smi = fields.Boolean(string='Membre SMI')
    show_rdv = fields.Boolean(string='Est consultation', default=False)
    nb_service_line = fields.Integer("Nombre de ligne d'article", compute='_get_nb_line')
    type_paid = fields.Selection([
        ('ESPECE', 'ESPECE'),
        ('VIREMENT', 'VIREMENT'),
        ('CHEQUE', 'CHEQUE'),
        ('M-VOLA', 'M-VOLA'),
        ('ORANGE MONEY', 'ORANGE MONEY'),
      #  ('MOBILE MONEY', 'MOBILE MONEY'),
        ('TPE', 'TPE'),
    ], string='Mode de paiement')
    #==== RENSEIGNEMENT CLINIQUE ===
    clinic_info = fields.Char("RC", help="Renseignement clinique", states=STATES)
    #==== POUR IMPRIME LAB SAMPLE ===
    check_sample = fields.Boolean(string="Lab sample", store=True)
    show_ot = fields.Boolean(string='Est chirurgie', default=False)
    #==== POUR IMPRIME IMAGING SAMPLE ===
    check_img = fields.Boolean(string="Is imaging request", store=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "ID doit etre unique !"),
    ]

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('acs.health_service')
        return super(HealthService, self).create(vals)

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_("Record can be delete only in Draft state."))
        return super(HealthService, self).unlink()

    @api.onchange('invoice_to')
    def onchange_invoice_to(self):
        if self.invoice_to:
            self.type_paid = self.invoice_to.type_paid or False

    def action_open_sms(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Send SMS'),
            'res_model': 'sms.composer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_recipient_single_number_itf': self.patient_id.mobile,
                'default_recipient_single_description': self.patient_id.name,
                'default_composition_mode': 'comment',
                'binding_model_id': 'health_service.model_acs_health_service',
                'default_res_id': self.id
            }
        }

    def action_send_sms(self):
        res = self.env['sms.composer'].action_send_sms()
        return res

    def check_doulon(self):
        if self.service_line:
            product_name = []
            for rec in self.service_line:
                if rec.display_type not in ['line_section', 'line_note']:
                    product_name.append(rec.name)
            dup = {x for x in product_name if product_name.count(x) > 1}
            if dup:
                raise UserError(_('Présence de produit en double: \n %s', dup))
            else:
                pass

    def button_draft(self):
        self.state = 'draft'

    def button_proforma(self):
        self.state = 'proforma'

    def button_confirm(self):
        self.check_doulon()
        self.update_price()
        labo = 0
        imagerie = 0
        consultation = 0
        chir = 0
        hospi = 0
        soins_inf = 0
        medicament = 0
        transfert = 0
        vad = 0
        for rec in self.service_line:
            if rec.product_type == 'pathology':
                labo = labo + 1
            elif rec.product_type in ['CT', 'MR', 'exploration', 'CR', 'US', 'MG', 'AU', 'radio_int']:
                imagerie = imagerie + 1
            elif rec.product_type == 'consultation':
                consultation = consultation + 1
            elif rec.product_type in ['surgery', 'radio_int']:
                chir = chir + 1
            elif rec.product_type in ['hospitalisation', 'bed']:
                hospi = hospi + 1
            elif rec.product_type == 'soins_infirmier':
                soins_inf = soins_inf + 1
            elif rec.product_type == 'medicament':
                medicament = medicament + 1
            elif rec.product_type == 'ambulance':
                transfert = transfert + 1
            elif rec.product_type == 'vad':
                vad = vad + 1
        self.desc = self.pricelist_id.code_desc or ''
        if vad != 0:
            self.desc = self.desc + ' VAD'
        if transfert != 0:
            self.desc = self.desc + ' TRANSFERT'
        if labo != 0:
            self.desc = self.desc + ' LABO'
        if imagerie != 0:
            self.desc = self.desc + ' IMAGERIE'
        if chir != 0:
            self.desc = self.desc + ' CHIRURGIE'
        if hospi != 0:
            self.desc = self.desc + ' HOSPITALISATION'
        if consultation != 0:
            self.desc = self.desc + ' CONSULTATION'
        if soins_inf != 0:
            self.desc = self.desc + ' SOINS INFIRMIERS'
        if medicament != 0:
            self.desc = self.desc + ' MEDICAMENTS'
        self.state = 'confirm'
        if not self.patient_id.first_determination and not self.patient_id.second_determination:
            if self.patient_id.chk_print_service_card is False: 
                self.message_post(body=_("Carte patient imprimée" ))
                self.patient_id.sudo().write({'chk_print_service_card': True})
                return self.env.ref('acs_hms_base.patient_blood_card_report_action').report_action(self.patient_id)

    def button_cancel(self):
        self.state = 'cancel'

    def button_done(self):
        self.state = 'done'

    def set_editable(self):
        self.state = 'editable'

    def re_done(self):
        self.state = 'done'

    def print_sample(self):
        self.ensure_one()
        sample_ids = self.env['acs.patient.laboratory.sample'].search([('health_service_id','=',self.id)])
        return self.env.ref('acs_laboratory.acs_lab_sample_report').report_action(sample_ids)

    def print_img_etiquette(self):
        self.ensure_one()
        etiquette_ids = self.env['acs.imaging.request'].search([('health_service_id','=',self.id)])
        return self.env.ref('acs_imaging.img_request_label_report_id').report_action(etiquette_ids)

    # CREATION LAB TEST
    def generate_labrequest(self):
        self.ensure_one()
        labtest_line_vals = []
        for line in self.service_line:
            if line.product_type == "pathology":
                vals = {
                    'test_id': self.env['acs.lab.test'].search([('product_id', '=', line.product.id)]).id,
                    'sale_price': line.sale_price,
                }
                labtest_line_vals.append((0, 0, vals))
            else:
                pass
        vals_labrequest = []
        patients = self.mapped('patient_id') + self.mapped('group_patient_ids')
        for patient in patients:
            labrequest_vals = {
                #'patient_id': self.patient_id.id,
                'patient_id': patient.id,
                #'physician_id': self.physician_id.id,
                'prescripteur': self.prescripteur.id,
                'health_service_id': self.id,
                'line_ids': labtest_line_vals,
                # 'department_id': self.department_id.id,
                # 'file_patient': self.file_patient,
                'clinic_info' : self.clinic_info,
                'company_id': self.company_id.id,
            }
            if len(labtest_line_vals) > 0:
                lab_request = self.env['acs.laboratory.request'].sudo().create(labrequest_vals)
                vals_labrequest.append((4, lab_request.id))
                lab_request.button_requested()
                lab_request.button_accept()
                self.check_sample = True
            else:
                pass

    def generate_ctrequest(self):
        self.ensure_one()
        ct_line_vals = []
        for line in self.service_line:
            if line.product_type == "CT":
                vals = {
                    'test_id': self.env['acs.imaging.test'].search([('product_id', '=', line.product.id)]).id,
                    'sale_price': line.sale_price,
                    #'pdc': line.pdc,
                }
                ct_line_vals.append((0, 0, vals))
            else:
                pass
        vals_imgrequest = []
        patients = self.mapped('patient_id') + self.mapped('group_patient_ids')
        for patient in patients:
            ct_vals = {
                'patient_id': patient.id,
               # 'physician_id': self.physician_id.id,
                'health_service_id': self.id,
                'line_ids': ct_line_vals,
                #'department_id': self.department_id.id,
                'test_type': 'CT',
                #'file_patient': self.file_patient,
                'prescripteur': self.prescripteur.id,
                'clinic_info' : self.clinic_info,
                'company_id': self.company_id.id,
                
            }
            if len(ct_line_vals) > 0:
                img_request = self.env['acs.imaging.request'].sudo().create(ct_vals)
                vals_imgrequest.append((4, img_request.id))
                self.check_img = True
            else:
                pass

    def generate_mrrequest(self):
        self.ensure_one()
        mr_line_vals = []
        for line in self.service_line:
            if line.product_type == "MR":
                vals = {
                    'test_id': self.env['acs.imaging.test'].search([('product_id', '=', line.product.id)]).id,
                    'sale_price': line.sale_price,
                    #'pdc': line.pdc,
                }
                mr_line_vals.append((0, 0, vals))
            else:
                pass
        vals_imgrequest = []
        patients = self.mapped('patient_id') + self.mapped('group_patient_ids')
        for patient in patients:
            mr_vals = {
                'patient_id': patient.id,
               # 'physician_id': self.physician_id.id,
                'health_service_id': self.id,
                'line_ids': mr_line_vals,
                #'department_id': self.department_id.id,
                'test_type': 'MR',
                # 'file_patient': self.file_patient,
                'prescripteur': self.prescripteur.id,
                'clinic_info' : self.clinic_info,
                'company_id': self.company_id.id,
            }
            if len(mr_line_vals) > 0:
                img_request = self.env['acs.imaging.request'].sudo().create(mr_vals)
                vals_imgrequest.append((4, img_request.id))
                self.check_img = True
            else:
                pass

    def generate_explorationrequest(self):
        self.ensure_one()
        exploration_line_vals = []
        for line in self.service_line:
            if line.product_type == "exploration":
                vals = {
                    'test_id': self.env['acs.imaging.test'].search([('product_id', '=', line.product.id)]).id,
                    'sale_price': line.sale_price,
                    #'pdc': line.pdc,
                }
                exploration_line_vals.append((0, 0, vals))
            else:
                pass
        vals_imgrequest = []
        patients = self.mapped('patient_id') + self.mapped('group_patient_ids')
        for patient in patients:
            exploration_vals = {
                'patient_id': patient.id,
                #'physician_id': self.physician_id.id,
                'health_service_id': self.id,
                'line_ids': exploration_line_vals,
                #'department_id': self.department_id.id,
                'test_type': 'exploration',
                # 'file_patient': self.file_patient,
                'prescripteur': self.prescripteur.id,
                'clinic_info' : self.clinic_info,
                'company_id': self.company_id.id,
            }
            if len(exploration_line_vals) > 0:
                img_request = self.env['acs.imaging.request'].sudo().create(exploration_vals)
                vals_imgrequest.append((4, img_request.id))
                self.check_img = True
            else:
                pass

    def generate_crrequest(self):
        self.ensure_one()
        cr_line_vals = []
        for line in self.service_line:
            if line.product_type == "CR":
                vals = {
                    'test_id': self.env['acs.imaging.test'].search([('product_id', '=', line.product.id)]).id,
                    'sale_price': line.sale_price,
                    #'pdc': line.pdc,
                }
                cr_line_vals.append((0, 0, vals))
            else:
                pass
        vals_imgrequest = []
        patients = self.mapped('patient_id') + self.mapped('group_patient_ids')
        for patient in patients:
            cr_vals = {
                # 'patient_id': self.patient_id.id,
                'patient_id': patient.id,
                #'physician_id': self.physician_id.id,
                'health_service_id': self.id,
                'line_ids': cr_line_vals,
                #'department_id': self.department_id.id,
                'test_type': 'CR',
                # 'file_patient': self.file_patient,
                'prescripteur': self.prescripteur.id,
                'clinic_info' : self.clinic_info,
                'company_id': self.company_id.id,
            }
            if len(cr_line_vals) > 0:
                img_request = self.env['acs.imaging.request'].sudo().create(cr_vals)
                vals_imgrequest.append((4, img_request.id))
                self.check_img = True
            else:
                pass

    def generate_usrequest(self):
        self.ensure_one()
        us_line_vals = []
        for line in self.service_line:
            if line.product_type == "US":
                vals = {
                    'test_id': self.env['acs.imaging.test'].search([('product_id', '=', line.product.id)]).id,
                    'sale_price': line.sale_price,
                    #'pdc': line.pdc,
                }
                us_line_vals.append((0, 0, vals))
            else:
                pass
        vals_imgrequest = []
        patients = self.mapped('patient_id') + self.mapped('group_patient_ids')
        for patient in patients:
            us_vals = {
                # 'patient_id': self.patient_id.id,
                'patient_id': patient.id,
                #'physician_id': self.physician_id.id,
                'health_service_id': self.id,
                'line_ids': us_line_vals,
                #'department_id': self.department_id.id,
                'test_type': 'US',
                # 'file_patient': self.file_patient,
                'prescripteur': self.prescripteur.id,
                'clinic_info' : self.clinic_info,
                'company_id': self.company_id.id,
            }
            if len(us_line_vals) > 0:
                img_request = self.env['acs.imaging.request'].sudo().create(us_vals)
                vals_imgrequest.append((4, img_request.id))
                self.check_img = True
            else:
                pass

    def generate_mggrequest(self):
        self.ensure_one()
        mg_line_vals = []
        for line in self.service_line:
            if line.product_type == "MG":
                vals = {
                    'test_id': self.env['acs.imaging.test'].search([('product_id', '=', line.product.id)]).id,
                    'sale_price': line.sale_price,
                    #'pdc': line.pdc,
                }
                mg_line_vals.append((0, 0, vals))
            else:
                pass
        vals_imgrequest = []
        patients = self.mapped('patient_id') + self.mapped('group_patient_ids')
        for patient in patients:
            mg_vals = {
                # 'patient_id': self.patient_id.id,
                'patient_id': patient.id,
               # 'physician_id': self.physician_id.id,
                'health_service_id': self.id,
                'line_ids': mg_line_vals,
                #'department_id': self.department_id.id,
                'test_type': 'MG',
                # 'file_patient': self.file_patient,
                'prescripteur': self.prescripteur.id,
                'clinic_info' : self.clinic_info,
                'company_id': self.company_id.id,
            }
            if len(mg_line_vals) > 0:
                img_request = self.env['acs.imaging.request'].sudo().create(mg_vals)
                vals_imgrequest.append((4, img_request.id))
                self.check_img = True
            else:
                pass

    def generate_aurequest(self):
        self.ensure_one()
        au_line_vals = []
        for line in self.service_line:
            if line.product_type == "AU":
                vals = {
                    'test_id': self.env['acs.imaging.test'].search([('product_id', '=', line.product.id)]).id,
                    'sale_price': line.sale_price,
                    #'pdc': line.pdc,
                }
                au_line_vals.append((0, 0, vals))
            else:
                pass
        vals_imgrequest = []
        patients = self.mapped('patient_id') + self.mapped('group_patient_ids')
        for patient in patients:
            au_vals = {
                # 'patient_id': self.patient_id.id,
                'patient_id': patient.id,
               # 'physician_id': self.physician_id.id,
                'health_service_id': self.id,
                'line_ids': au_line_vals,
                #'department_id': self.department_id.id,
                'test_type': 'AU',
                # 'file_patient': self.file_patient,
                'prescripteur': self.prescripteur.id,
                'clinic_info' : self.clinic_info,
                'company_id': self.company_id.id,
            }
            if len(au_line_vals) > 0:
                img_request = self.env['acs.imaging.request'].sudo().create(au_vals)
                vals_imgrequest.append((4, img_request.id))
                self.check_img = True
            else:
                pass

    def generate_radio_int_request(self):
        self.ensure_one()
        au_line_vals = []
        for line in self.service_line:
            if line.product_type == "radio_int":
                vals = {
                    'test_id': self.env['acs.imaging.test'].search([('product_id', '=', line.product.id)]).id,
                    'sale_price': line.sale_price,
                    #'pdc': line.pdc,
                }
                au_line_vals.append((0, 0, vals))
            else:
                pass
        vals_imgrequest = []
        patients = self.mapped('patient_id') + self.mapped('group_patient_ids')
        for patient in patients:
            au_vals = {
                # 'patient_id': self.patient_id.id,
                'patient_id': patient.id,
               # 'physician_id': self.physician_id.id,
                'health_service_id': self.id,
                'line_ids': au_line_vals,
                #'department_id': self.department_id.id,
                'test_type': 'radio_int',
                # 'file_patient': self.file_patient,
                'prescripteur': self.prescripteur.id,
                'clinic_info' : self.clinic_info,
                'company_id': self.company_id.id,
            }
            if len(au_line_vals) > 0:
                img_request = self.env['acs.imaging.request'].sudo().create(au_vals)
                vals_imgrequest.append((4, img_request.id))
                self.check_img = True
            else:
                pass

    def generate_consultation(self):
        self.ensure_one()
        consultation_line_vals = []
        patients = self.mapped('patient_id') + self.mapped('group_patient_ids')
        medecin = []
        medecin = self.mapped('physician_id')
        for line in self.service_line:
            if line.product_type == "consultation":
                vals_consultation = []
                for patient in patients:
                    consultation_vals = {
                        #'patient_id': self.patient_id.id,
                        'patient_id': patient.id,
                        #'physician_id': self.physician_id.id,
                        'physician_id': medecin[0].id,
                        'health_service_id': self.id,
                        'product_id': line.product.id,
                        'company_id': self.company_id.id,
                    }
                    consultation_request = self.env['hms.appointment'].sudo().create(consultation_vals)
                    vals_consultation.append((4, consultation_request.id))
            else:
                pass

    def generate_surgery(self):
        self.ensure_one()
        patients = self.mapped('patient_id') + self.mapped('group_patient_ids')
        for patient in patients:
            for line in self.service_line:
                if line.product_type == "surgery" or line.product_type == "radio_int":
                    vals_surgery = []
                    surgery_vals = {
                        #'patient_id': self.patient_id.id,
                        'patient_id': patient.id,
                        'note': self.notes,
                        'ot_id': self.ot_id.id,
                        'health_service_id': self.id,
                    }
                    surgery_request = self.env['acs.ot.booking'].sudo().create(surgery_vals)
                    vals_surgery.append((4, surgery_request.id))
                else:
                    pass

    def generate_hospitalisation(self):
        self.ensure_one()
        patients = self.mapped('patient_id') + self.mapped('group_patient_ids')
        for patient in patients:
            for line in self.service_line:
                if line.product_type == "hospitalisation":
                    vals_hospi = []
                    hospi_vals = {
                        #'patient_id': self.patient_id.id,
                        'patient_id': patient.id,
                        #'physician_id': self.physician_id.id,
                        'health_service_id': self.id,
                        'company_id': self.company_id.id,
                    }
                    hospi_request = self.env['acs.hospitalization'].sudo().create(hospi_vals)
                    vals_hospi.append((4, hospi_request.id))
                else:
                    pass

    def generate_soins_infirmier(self):
        self.ensure_one()
        soins_line_vals = []
        patients = self.mapped('patient_id') + self.mapped('group_patient_ids')
        for patient in patients:
            for line in self.service_line:
                if line.product_type == "soins_infirmier":
                    vals_soins = []
                    soins_vals = {
                        #'patient_id': self.patient_id.id,
                        'patient_id': patient.id,
                        'birthday': patient.birthday,
                        'nurse_id': self.nurse_id.id,
                        'health_service_id': self.id,
                        'product_id': line.product.id,
                        'company_id': self.company_id.id,
                    }
                    soins_request = self.env['acs.soins.infirmier'].sudo().create(soins_vals)
                    vals_soins.append((4, soins_request.id))
                else:
                    pass

    def create_testrequest(self):
        if not self.invoice_id:
            raise UserError(_("La facture n'est pas encore créée."))
        elif self.invoice_id and self.invoice_id.payment_state not in ['in_payment','paid']:
            raise UserError(_("La facture n'est pas encore payée."))
        else:
            if self.company_id.is_laboratory is True:
                self.generate_labrequest()
            if self.company_id.is_imaging is True:
                self.generate_ctrequest()
                self.generate_mrrequest()
                self.generate_explorationrequest()
                self.generate_crrequest()
                self.generate_usrequest()
                self.generate_mggrequest()
                self.generate_aurequest()
                self.generate_radio_int_request()
            if self.company_id.is_consultation is True:
                self.generate_consultation()
                self.generate_soins_infirmier()
            if self.company_id.is_surgery is True:
                self.generate_surgery()
            if self.company_id.is_hospitalization is True:
                self.generate_hospitalisation()
            self.state = 'requested'

    def create_invoice(self):
        if not self.service_line:
            raise UserError(_("Remplir la ligne de service svp."))
        fact_exist = self.env['account.move'].search([('ref','=', self.name)])
        if fact_exist:
            raise UserError(_("Vous avez déjà créé une facture lié au service santé."))

        product_data = []
        for line in self.service_line:
            product_data.append({
                'display_type': line.display_type,
                'name': line.name,
                'product_id': line.product,
                'price_unit': line.sale_price,
                'quantity': line.quantity,
            })
        pricelist_context = {}
        if self.pricelist_id:
            pricelist_context = {'acs_pricelist_id': self.pricelist_id.id}

        # partner_commission = []
        # if self.prescripteur.provide_commission is True:
        #     partner_commission.append(self.env['res.partner'].search([('name', '=', self.prescripteur.name)], limit=1).id)

        prestataire_data = []
        list_prestataire = self.mapped('physician_id').filtered(lambda r: r.prest_commission == True)
        for prest in list_prestataire:
              prestataire_data.append(prest.partner_id.id)

        invoice = self.with_context(pricelist_context).acs_create_invoice(partner=self.invoice_to, patient=self.patient_id, product_data=product_data, inv_data={'ref': self.name})
        invoice.write({
            'mode_payment': self.mode_payd.id,
            'ref_payment': self.ref_payd,
            'description_fact': self.desc,
            'department_id': self.department_id,
            # 'commission_partner_ids': [(6, 0, partner_commission)],
            'coprest_partner_ids': [(6, 0, prestataire_data)],
            'physician_id': self.physician_id[0] or self.physician_id[0].id if self.physician_id else False,
            'ref_physician_id': self.prescripteur.id,
        })
        self.invoice_id = invoice.id
        self.invoice_id.update_coprest_values()
       # invoice.service_id = self.id
        self.state = 'invoiced'
        action = self.acs_action_view_invoice(self.invoice_id)
        return action

    def view_invoice(self):
        invoices = self.mapped('invoice_id')
        action = self.acs_action_view_invoice(invoices)
        return action

    def update_price(self):
        self.ensure_one()
        for line in self.service_line:
            line.maj_pricelist()
        self.show_update_pricelist = False

    def add_service_line(self):
        action = {
                'name': 'Ajouter ligne de service',
                'type': 'ir.actions.act_window',
                'res_model': 'service.line.category.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('health_service.view_service_line_category_wizard_form').id,
                'target': 'new',
                'context': {
                    'default_service_id': self.id,
                },
            }
        return action


class HealthServiceLine(models.Model):
    _name = 'acs.health_service.line'
    _description = 'Line Service Sante'

    @api.depends('quantity', 'sale_price')
    def _compute_amount(self):
        for line in self:
            line.amount_total = line.quantity * line.sale_price

    service_id = fields.Many2one('acs.health_service', string='Service', readonly=True)
    to_invoice = fields.Boolean(string='Invoice', default=True)
    product = fields.Many2one('product.product', string='Product')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product.uom_id.category_id', readonly=True)
    sale_price = fields.Float(string='Sale Price', readonly=True)
    quantity = fields.Integer(string='Quantity')
    product_type = fields.Char(string='Type')
    amount_total = fields.Float(compute="_compute_amount", string="Sub Total", store=True)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    currency_id = fields.Many2one(related='service_id.currency_id', depends=['service_id.currency_id'], store=True,
                                  string='Currency', readonly=True)

    @api.onchange('product')
    def onchange_test(self):
        if self.product:
            self.sale_price = self.product.lst_price
            self.product_type = self.product.hospital_product_type
            self.product_uom = self.product.uom_id.id
            self.name = self.product.name
            self.quantity = 1

    def maj_pricelist(self):
        if self.product:
            if self.service_id.pricelist_id:
                product_id = self.product.with_context(pricelist=self.service_id.pricelist_id.id)
                self.sale_price = product_id.price
    