# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.addons.orange_sms.models.orange_sms import SMS
import uuid


class RequestLabTestLine(models.Model):
    _name = "laboratory.result.line"
    _description = "Test Lines results"

    test_id = fields.Many2one('acs.lab.test',string='Test', ondelete='cascade', required=True)
    acs_tat = fields.Char(related='test_id.acs_tat', string='Turnaround Time', readonly=True)
    instruction = fields.Char(string='Special Instructions')
    result_id = fields.Many2one('patient.laboratory.test',string='Lines', ondelete='cascade')
    company_id = fields.Many2one('res.company', ondelete='restrict',
        string='Company',related='result_id.company_id')
    sample_type_id = fields.Many2one(related='test_id.sample_type_id', string='Type échantillon', readonly=True)


class PatientLabTest(models.Model):
    _name = "patient.laboratory.test"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'acs.hms.mixin', 'portal.mixin', 'acs.documnt.mixin', 'acs.qrcode.mixin']
    _description = "Patient Laboratory Test"
    _order = 'date_analysis desc, id desc'

    @api.model
    def _get_disclaimer(self):
        return self.env.user.sudo().company_id.acs_laboratory_disclaimer or ''
    
    @api.depends('critearea_ids.result_type')
    def _get_nb_line(self):
        #nb = []
        i=0
        for line in self.critearea_ids:
            if not line.display_type and line.result_type == 'warning':
                #nb.append(line.result_type)
                i=i+1
            else:
                i=i
        self.nb_analyte_warning = i #len(nb)

    # @api.depends('critearea_ids')
    # def _check_nb_line(self):
    #     for line in self.critearea_ids:
    #         if not line.display_type and line.result_type == 'warning':
    #             self.check_analyte_warning = True

    STATES = {'cancel': [('readonly', True)], 'done': [('readonly', True)], 'deliver': [('readonly', True)]}

    name = fields.Char(string='Test ID', help="Lab result ID", readonly="1",copy=False, index=True, tracking=True)
    mobile = fields.Char(string='Mobile', copy=False, states=STATES, tracking=True)
    test_id = fields.Many2one('acs.lab.test', string='Test', required=False, ondelete='restrict', states=STATES, tracking=True)
    patient_id = fields.Many2one('hms.patient', string='Patient', required=True, ondelete='restrict', states=STATES, tracking=True)
    age = fields.Char(string='Age', related='patient_id.partner_id.age')
    birthday = fields.Date(string='Date of Birth', related='patient_id.birthday')
    user_id = fields.Many2one('res.users',string='Lab User', default=lambda self: self.env.user, states=STATES)
    physician_id = fields.Many2one('hms.physician',string='Prescribing Doctor', help="Doctor who requested the test", ondelete='restrict', states=STATES)
    diagnosis = fields.Text(string='Diagnosis', states=STATES)
    critearea_ids = fields.One2many('lab.test.critearea', 'patient_lab_id', string='Test Cases', copy=True, states=STATES)
    date_requested = fields.Datetime(string='Request Date', states=STATES)
    date_analysis = fields.Date(string='Test Date', default=fields.Date.context_today, states=STATES)
    request_id = fields.Many2one('acs.laboratory.request', string='Lab Request', ondelete='restrict', states=STATES)
    laboratory_id = fields.Many2one('acs.laboratory', related="request_id.laboratory_id", string='Laboratory', readonly=True, store=True)
    report = fields.Text(string='Test Report', states=STATES)
    note = fields.Text(string='Extra Info', states=STATES)
    sample_ids = fields.Many2many('acs.patient.laboratory.sample', 'test_lab_sample_rel', 'test_id', 'sample_id', string='Test Samples', states=STATES)
    company_id = fields.Many2one('res.company', ondelete='restrict', 
        string='Company',default=lambda self: self.env.user.company_id.id, states=STATES)
    state = fields.Selection([
        ('draft','Draft'),
        ('pret','Confirmer'),
        ('sent', 'Envoie dans automate'),
        ('result_saved', 'Résultat inséré'),
        ('verified', 'Validation biologiste'),
        ('half_done','Résultat partielle'),
        ('done','Résultat disponible'),
        ('deliver', 'Résultat livré'),
        ('cancel','Cancel'),
    ], string='State',readonly=True, default='draft', tracking=True)
    consumable_line_ids = fields.One2many('hms.consumable.line', 'patient_lab_test_id',
        string='Consumable Line', states=STATES)
    disclaimer = fields.Text("Dislaimer", states=STATES, default=_get_disclaimer)
    collection_center_id = fields.Many2one('acs.laboratory', string='Collection Center', related="request_id.collection_center_id", states=STATES)
    # Harnetprod
    health_service_id = fields.Many2one('acs.health_service', string='Service santé', readonly=True)

    group_techlab = fields.Many2many(comodel_name='res.partner', string="Technicien de laboratoire",
                                     domain=[('type_prof', '=', 'is_techlab')], states=STATES)
    group_medlab = fields.Many2many('hms.physician', string="Médecin imagerie", states=STATES)

    #Just to make object selectable in selction field this is required: Waiting Screen
    acs_show_in_wc = fields.Boolean(default=True)

    #===MODIF POUR AUTOMATE====
    list_test = fields.One2many('laboratory.result.line', 'result_id', string='Listes tests', states=STATES, copy=True)
    cat_analyse = fields.Selection([
        ('hematologie', 'HEMATOLOGIE'),
        ('bacteriologie', 'BACTERIOLOGIE'),
        ('parasitologie', 'PARASITOLOGIE'),
        ('biochimie', 'BIOCHIMIE'),
        ('hormonologie', 'HORMONOLOGIE'),
        ('immunologie', 'IMMUNOLOGIE'),
        ('anatomopathologie', 'ANATOMOPATHOLOGIE'),
        ('serologie', 'SEROLOGIE'),
        ('marqueurs_tumoraux', 'MARQUEURS TUMORAUX'),
        ('biochimie_utinaire', 'BIOCHIMIE UTINAIRE'),
    ], string='catégorie analyse')
    department_id = fields.Many2one('hr.department', ondelete='restrict', string='Department', tracking=True)
    clinic_info = fields.Char("Renseignement clinique", states=STATES)
    prescripteur = fields.Many2one('res.partner', string='Médecin prescripteur',
                                   domain=[('is_referring_doctor', '=', True)], states=STATES)
    aspect_sang = fields.Char("Aspect macroscopique sang", states=STATES)
    aspect_urine = fields.Char("Aspect macroscopique urine", states=STATES)
    
    editable_reason = fields.Text(string="Motif de revérification", states=STATES)
    tech_user_id = fields.Many2one('res.users', string='Confirmé par', readonly=True)
    check_user_id = fields.Many2one('res.users', string='Valeur vérifiée par', readonly=True)
    med_user_id = fields.Many2one('res.users', string='Validé par', readonly=True)
    reverifed_user_id = fields.Many2one('res.users', string='Re-vérifié par', readonly=True)
    deliverd_user_id = fields.Many2one('res.users', string='Livré par', readonly=True)
    nb_analyte_warning = fields.Integer("Nombre résultat anormaux")
    check_analyte_warning = fields.Boolean("Si résultat anormaux")
    check_print_card = fields.Boolean("Carte sanguin à imprimer")
    show_button = fields.Boolean(compute="_compute_show_button", string="Show Button", store=False)
    #===Antibiogramme===
    antibiogramme = fields.Html('Interpretation', states=STATES)
    antibiogramme_fcv = fields.Html('BACTERIO - FCV', states=STATES)
    antibiogramme_ecbu = fields.Html('BACTERIO - ECBU', states=STATES)
    antibiogramme_hemoculture = fields.Html('BACTERIO - HEMOCULTURE', states=STATES)
    #===LIVRAISON PARTIELLE===
    is_ready_for_partial_delivery = fields.Boolean(string="Pour livraison partielle", default=False, store=True, tracking=True)
    is_partial_delivery = fields.Boolean(string="Livré partiellement", default=False, store=True, tracking=True)
    #==ANTIBIOGRAMME===
    antibiogramme_1 = fields.Html('Antibiogramme 1', states=STATES)
    antibiogramme_2 = fields.Html('Antibiogramme 2', states=STATES)
    antibiogramme_3 = fields.Html('Antibiogramme 3', states=STATES)
    antibiogramme_4 = fields.Html('Antibiogramme 4', states=STATES)


    


    _sql_constraints = [
        ('name_company_uniq', 'unique (name,company_id)', 'Test Name must be unique per company !')
    ]

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('patient.laboratory.test')
        res = super(PatientLabTest, self).create(vals)
        res.unique_code = uuid.uuid4()
        return res

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_("Lab Test can be delete only in Draft state."))
        return super(PatientLabTest, self).unlink()
    
    def set_ready_for_partial_delivery(self):
        self.is_ready_for_partial_delivery = True
        
    def unset_ready_for_partial_delivery(self):
        self.is_ready_for_partial_delivery = False

    

    def set_ready_for_partial_delivery_tree(self):
        active_ids = self.env.context.get("active_ids", [])
        lab_results = self.env['patient.laboratory.test'].browse(active_ids)
        for lab_result in lab_results:
            lab_result.is_ready_for_partial_delivery = True

    def unset_ready_for_partial_delivery_tree(self):
        active_ids = self.env.context.get("active_ids", [])
        lab_results = self.env['patient.laboratory.test'].browse(active_ids)
        for lab_result in lab_results:
            lab_result.is_ready_for_partial_delivery = False

    def set_partial_delivery(self):
        self.is_partial_delivery = True

    def set_partial_delivery_tree(self):
        active_ids = self.env.context.get("active_ids", [])
        lab_results = self.env['patient.laboratory.test'].browse(active_ids)
        for lab_result in lab_results:
            lab_result.is_partial_delivery = True
    
    
    @api.depends('health_service_id')
    def _compute_show_button(self):
        for rec in self:
            rec.show_button = bool(rec.health_service_id and rec.health_service_id.ref_hs_canceled.id)

    def recover_lab_data(self):
        Critearea = self.env['lab.test.critearea']
        
        old_lab_result = self.env['patient.laboratory.test'].sudo().search([
            ('health_service_id', '=', self.health_service_id.ref_hs_canceled.id),
            ('state', '=', 'cancel')
        ], limit=1)  
        
        if not old_lab_result:
            raise UserError(_('Aucun donnée Trouveée pour la récuperation'))

        old_criteareas = old_lab_result.critearea_ids 
        current_criteareas = self.critearea_ids 

        for old_critearea in old_criteareas:
            current_critearea = current_criteareas.filtered(lambda c: c.name == old_critearea.name and c.code == old_critearea.code)
            
            if current_critearea:
                current_critearea.write({
                    'normal_range': old_critearea.normal_range,
                    'remark': old_critearea.remark,
                    'result': old_critearea.result,
                    'lab_uom_id': old_critearea.lab_uom_id.id if old_critearea.lab_uom_id else False,
                    'display_type': old_critearea.display_type,
                    'sequence': old_critearea.sequence,
                    'ref_sample': old_critearea.ref_sample,
                })

        self.message_post(body=f"Lab data recovered from the old canceled lab request: {old_lab_result.name}")

    

    def get_resultat_anterieur(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.action_get_resultat_anterieur_wizard")
        action['context'] = {
            'active_model':'patient.laboratory.test',
        }
        return action

    def action_open_sms(self):
        # res = self.env['ir.actions.act_window'].for_xml_id('sms.composer','sms_composer_view_form')
        # return res
        return {
            'type': 'ir.actions.act_window',
            'name': _('Send SMS'),
            'res_model': 'sms.composer',
            'view_mode': 'form',
            # 'view_type': 'form',
            'target': 'new',
            'context': {
                'default_recipient_single_number_itf': self.patient_id.mobile,
                'default_recipient_single_description': self.patient_id.name,
                'default_composition_mode': 'comment',
                'binding_model_id': 'acs_laboratory.model_patient_laboratory_test',
                'default_res_id': self.id
            }
        }
        # return self.env('sms.composer').action_send_sms()
        # self.sms = True

    def action_send_sms(self):
        res = self.env['sms.composer'].action_send_sms()
        return res, self.env.ref('acs_laboratory.action_report_basic_lab_combine_imm').report_action(self)
    
    def print_send_sms(self):
        active_ids = self.env.context.get("active_ids") or [self.id]
        lab_results = self.env['patient.laboratory.test'].browse(active_ids)
        # criteria_ids = lab_results.mapped("critearea_ids").filtered(lambda c: c.display_type not in ["line_section", "line_note"])
        # is_all_result_available = all(criteria_ids.mapped("result"))
        ng_partiel_result = lab_results.search_count([('state', '=','half_done')])

        company = self.env.company
        auth_token = company.auth_token
        senderName = company.senderName
        dev_phone_number = company.dev_phone_number
        clientID = company.client_id
        clientSecret = company.client_secret

        sms_service = SMS(auth_token=auth_token, senderName=senderName, clientID=clientID, clientSecret=clientSecret)

        recipient_phone_number = self.patient_id.phone or self.patient_id.mobile

        if ng_partiel_result != 0:
            _message = self.env['sms.template'].sudo().search([('name', '=', 'resultat labo partiellement disponible')])
            if _message:
                response = sms_service.send_sms(
                    dev_phone_number=dev_phone_number,
                    recipient_phone_number=recipient_phone_number,
                    message=_message.body
                )
                if response.status_code != 201:
                    raise UserWarning(f"Message non envoyé pour: {self.name}")
        else:
            _message = self.env['sms.template'].sudo().search([('name', '=', 'resultat labo disponible'),('company_id','=',self.company_id.id)])
            if _message:
                sms_service.send_sms(
                    dev_phone_number=dev_phone_number,
                    recipient_phone_number=recipient_phone_number,
                    message=_message.body
                )

        return self.env.ref('acs_laboratory.action_report_acs_lab_test_imm').report_action(lab_results)
    
    def action_open_tree_sms(self):
        active_ids = self.env.context.get("active_ids", [])
        lab_results = self.env['patient.laboratory.test'].browse(active_ids)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Send SMS'),
            'res_model': 'sms.composer',
            'view_mode': 'form',
            'target': 'new',
            # 'context': {
            #     'default_recipient_single_number_itf': lab_results[0].patient_id.mobile,
            #     'default_recipient_single_description': lab_results[0].patient_id.name,
            #     'default_composition_mode': 'comment',
            #     'binding_model_id': 'acs_laboratory.model_patient_laboratory_test',
            #     'default_res_id': lab_results[0].id,
            # }
        }
    
    def action_print(self):
        return self.env.ref('acs_laboratory.action_report_basic_lab_combine_imm').report_action(self)
    
    def action_print_tree(self):
        
        self.action_print()
        # return self.env.ref('acs_laboratory.action_report_basic_lab_combine_imm').report_action(self)
        active_ids = self.env.context.get("active_ids", [])
        lab_results = self.env['patient.laboratory.test'].browse(active_ids)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Send SMS'),
            'res_model': 'sms.composer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_recipient_single_number_itf': lab_results[0].patient_id.mobile,
                'default_recipient_single_description': lab_results[0].patient_id.name,
                'default_composition_mode': 'comment',
                'binding_model_id': 'acs_laboratory.model_patient_laboratory_test',
                'default_res_id': lab_results[0].id,
            }
        }

        

    @api.onchange('request_id')
    def onchange_request_id(self):
        if self.request_id and self.request_id.date:
            self.date_requested = self.request_id.date

    @api.onchange('test_id')
    def onchange_test_id(self):
        if self.test_id:
            result = self.search(['&','&',('patient_id', '=', self.patient_id.id), ('test_id', '=', self.test_id.id), ('state', '=', 'done')], order='id desc', limit=1)
            self.old_resultlab_id = result.id if result else False

    # @api.onchange('test_id')
    # def on_change_test(self):
    #     test_lines = []
    #     if self.test_id:
    #         gender = self.patient_id.gender
    #         for line in self.test_id.critearea_ids:
    #             test_lines.append((0,0,{
    #                 'sequence': line.sequence,
    #                 'name': line.name,
    #                 'normal_range': line.normal_range_female if gender=='F' else line.normal_range_male,
    #                 'lab_uom_id': line.lab_uom_id and line.lab_uom_id.id or False,
    #                 'remark': line.remark,
    #                 'display_type': line.display_type,
    #             }))
    #         self.critearea_ids = test_lines

    @api.onchange('test_id')
    def on_change_test(self):
        test_lines = []
        if self.test_id:
            gender = self.patient_id.gender
            age = ''
            end_data = self.patient_id.date_of_death or fields.Datetime.now()
            delta = relativedelta(end_data, self.birthday)
            if delta.years <= 1:
                age = str(delta.months) + _(" Month ")
            else:
                age = str(delta.years) + _(" Year")
            for line in self.test_id.critearea_ids:
                if line.reference_per_age is True:
                    list_tranche_age = []

                    test_lines.append((0, 0, {
                        'sequence': line.sequence,
                        'name': line.name,
                        'normal_range': line.normal_range_female if gender == 'F' else line.normal_range_male,
                        'lab_uom_id': line.lab_uom_id and line.lab_uom_id.id or False,
                        'remark': line.remark,
                        'display_type': line.display_type,
                    }))
                else:
                    test_lines.append((0, 0, {
                        'sequence': line.sequence,
                        'name': line.name,
                        'normal_range': line.normal_range_female if gender == 'F' else line.normal_range_male,
                        'lab_uom_id': line.lab_uom_id and line.lab_uom_id.id or False,
                        'remark': line.remark,
                        'display_type': line.display_type,
                    }))
            self.critearea_ids = test_lines

    def action_done(self):
        self.consume_lab_material()
        if not self.med_user_id:
            self.med_user_id = self.env.uid
        # result_empty = self.critearea_ids.search_count([('result', '=', '')])
        criteria_ids = self.mapped("critearea_ids").filtered(lambda c: c.display_type not in ["line_section", "line_note"])
        is_all_result_available = all(criteria_ids.mapped("result"))

        if is_all_result_available:
            self.state = 'done'
        else:
            self.state = 'half_done'

    def action_deliver(self):
        if not self.deliverd_user_id:
            self.deliverd_user_id = self.env.uid
        total_result = self.request_id.result_count
        labresult_deliver = self.env['patient.laboratory.test'].sudo().search_count([('request_id', '=', self.request_id.id), ('state', '=', 'deliver')])
        if labresult_deliver == (total_result - 1):
            request = self.env['acs.laboratory.request'].sudo().search([('id', '=', self.request_id.id)])
            request.state = 'done'
            self.state = 'deliver'
        else:
            self.state = 'deliver'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'

    def reverified_record(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.action_labo_reverificaiton_reason")
        action['context'] = {
            'active_model':'patient.laboratory.test',
        }
        return action

    def action_verified(self):
        if not self.reverifed_user_id:
            self.reverifed_user_id = self.env.uid
        self.state = 'verified'

    @api.model
    def _prepare_critearea(self, seq=False, group_sequence=False,line=False, res_line=False, ref_per_age=False):
        gender = self.patient_id.gender
        critearea_vals = {
            'patient_lab_id': self.id,
            'name': res_line.name,
            'code': res_line.code,
            'result_value_type': res_line.result_value_type,
            'normal_range': ref_per_age.normal_range_female if gender == 'F' else ref_per_age.normal_range_male,
            'lab_uom_id': res_line.lab_uom_id and res_line.lab_uom_id.id or False,
            'sequence': seq if res_line.sequence == 0 else res_line.sequence,
            'group_sequence': group_sequence,
            'remark': res_line.remark,
            'display_type': res_line.display_type,
            'request_id': self.request_id.id,
            'ref_sample': self.env['acs.patient.laboratory.sample'].search(
                ['&', ('request_id', '=', self.request_id.id),
                 ('sample_type_id', '=', line.test_id.sample_type_id.id)]).name,
            'patient_id': self.patient_id.id,
            'reference_spec': ref_per_age.reference_spec_female if gender == 'F' else ref_per_age.reference_spec_male,
            'interp_si_low': res_line.interp_si_low,
            'interp_si_normal': res_line.interp_si_normal,
            'interp_not_normal': res_line.interp_not_normal,
            'interp_si_high': res_line.interp_si_high,
            'interp_range_1': res_line.interp_range_1,
            'interp_range_2': res_line.interp_range_2,
            'advice_low': res_line.advice_low,
            'advice_high': res_line.advice_high,
        }
        return critearea_vals

    def get_analyte(self):
        if self.state != 'draft':
            raise UserError(_("L'enregistrement doit être en état brouillon."))

        Critearea = self.env['lab.test.critearea']
        gender = self.patient_id.gender

        group_sequence = 0
        seq = 0
        for line in self.list_test:
            group_sequence += 1
            for res_line in line.test_id.critearea_ids:
                seq += 1
                if res_line.reference_per_age is False:
                    Critearea.create({
                        'patient_lab_id': self.id,
                        'name': res_line.name,
                        'code': res_line.code,
                        'result_value_type': res_line.result_value_type,
                        'normal_range': res_line.normal_range_female if gender=='F' else res_line.normal_range_male,
                        'lab_uom_id': res_line.lab_uom_id and res_line.lab_uom_id.id or False,
                        'sequence': seq if res_line.sequence == 0 else res_line.sequence,
                        'group_sequence': group_sequence,
                        'remark': res_line.remark,
                        'display_type': res_line.display_type,
                        'request_id': self.request_id.id,
                        'ref_sample': self.env['acs.patient.laboratory.sample'].search(['&',('request_id', '=',self.request_id.id),('sample_type_id', '=', line.test_id.sample_type_id.id)]).name,
                        'patient_id': self.patient_id.id,
                        'usual_reference_line':  res_line.usual_reference_line,
                        'reference_spec': res_line.reference_spec_female if gender=='F' else res_line.reference_spec_male,
                        'interp_si_low': res_line.interp_si_low,
                        'interp_si_normal': res_line.interp_si_normal,
                        'interp_not_normal': res_line.interp_not_normal,
                        'interp_si_high': res_line.interp_si_high,
                        'interp_range_1': res_line.interp_range_1,
                        'interp_range_2': res_line.interp_range_2,
                        'advice_low': res_line.advice_low,
                        'advice_high': res_line.advice_high,
                    })
                else:
                    age = ''
                    if self.birthday:
                        end_data = self.patient_id.date_of_death or fields.Datetime.now()
                        delta = relativedelta(end_data, self.birthday)
                        if delta.years < 1 and delta.months != 0:
                            age = str(delta.months) + _("_Month")
                        elif delta.months == 0 and delta.years == 0:
                            age = str(delta.days) + _("_Days")
                        else:
                            age = str(delta.years) + _("_Year")
                    separator_age_patient = age.split("_")
                    unite_age = separator_age_patient[1]
                    num_age = int(separator_age_patient[0])
                    for ref_per_age in res_line.usual_reference_line:
                        if ref_per_age.age_unite == unite_age:
                            txt_range_age = ref_per_age.range_age
                            if txt_range_age.find("<") >= 0:
                                ref = txt_range_age.split('<')
                                if num_age < int(ref[1]):
                                    critearea_vals = self._prepare_critearea(seq, group_sequence, line, res_line, ref_per_age)
                                    Critearea.create(critearea_vals)
                            elif txt_range_age.find("-") >= 0:
                                ref = txt_range_age.split('-')
                                if num_age > int(ref[0]) and num_age <= int(ref[1]):
                                    critearea_vals = self._prepare_critearea(seq, group_sequence, line, res_line, ref_per_age)
                                    Critearea.create(critearea_vals)
                            elif txt_range_age.find(">") >= 0:
                                ref = txt_range_age.split('>')
                                if num_age > int(ref[1]):
                                    critearea_vals = self._prepare_critearea(seq, group_sequence,line, res_line, ref_per_age)
                                    Critearea.create(critearea_vals)
                        else:
                            pass
        self.state = 'pret'
        if not self.tech_user_id:
            self.tech_user_id = self.env.uid

    def check_result(self):
        for line in self.critearea_ids:
            line.onchange_result()
        if not self.check_user_id:
            self.check_user_id = self.env.uid
        self._get_nb_line()
        self.state = 'result_saved'


    def confirm_tree(self):
        active_ids = self.env.context.get("active_ids", [])
        lab_results = self.env['patient.laboratory.test'].browse(active_ids)
        for lab_result in lab_results:
            lab_result.get_analyte()

    def deliver_tree(self):
        active_ids = self.env.context.get("active_ids", [])
        lab_results = self.env['patient.laboratory.test'].browse(active_ids)
        for lab_result in lab_results:
            lab_result.action_deliver()

    def combine_conclusion(self):
        seq_number = []
        seq_id = []
        for rec in self.critearea_ids:
            if rec.display_type == 'line_section':
                seq_number.append(rec.sequence)
                seq_id.append(rec.id)

        if len(seq_number) !=0:
            for i in range(0,len(seq_number)):
                for rec in self.critearea_ids:
                    if i < (len(seq_number)-1):
                        if rec.sequence >= seq_number[i] and rec.sequence < seq_number[i+1]:
                            if rec.result_type == 'warning':
                                id_section = self.critearea_ids.search([('id','=',seq_id[i])])
                                id_section.section_warning = True
                    else:
                        if rec.result_type == 'warning' and rec.sequence >= seq_number[i]:
                                id_section = self.critearea_ids.search([('id','=',seq_id[i])])
                                id_section.section_warning = True
            
            for rec in self.critearea_ids:
                if rec.section_warning is not True and rec.display_type == 'line_section':
                    current_desc = self.note or ''
                    self.note = current_desc+'\n'+rec.name+ ' normal \n' 
                    
    # def print_gs(self):
    #     if self.critearea_ids:
    #         gs_1 = ''
    #         gs_2 = ''
    #         for rec in self.critearea_ids:
    #             if rec.code == 'DET1':
    #                 gs_1 = rec.result
    #             if rec.code == 'DET2':
    #                 gs_2 = rec.result
    #         if gs_1 == gs_2:
    #             self.patient_id.first_determination = str(rec.date_result) + ' n° ' + rec.request_id.name
    #             self.patient_id.second_determination = str(rec.date_result) + ' n° ' + rec.request_id.name
    #             split_gs = gs_1.split(" ")
    #             if len(split_gs) == 3:
    #                 if split_gs[2] == 'POSITIF':
    #                     self.patient_id.blood_group = split_gs[0] + '+'
    #                     return self.env.ref('acs_hms.patient_blood_card_report_action').report_action(self.patient_id)
    #                 elif split_gs[2] == 'NEGATIF':
    #                     self.patient_id.blood_group = split_gs[0] + '-'
    #                     return self.env.ref('acs_hms.patient_blood_card_report_action').report_action(self.patient_id)
    #                 else:
    #                     raise UserError(_("Vérifiez l'orthographe des résultats du groupage sanguin"))
    #             else:
    #                 raise UserError(_("Vérifiez l'espacement des mots dans le résultat du groupage sanguin"))
    #         else:
    #             raise UserError(_("La première et deuxième déterminations ne sont pas identique"))

    def print_gs(self):
        if self.critearea_ids:
            gs = ''
            for rec in self.critearea_ids:
                if rec.code == 'BLOOD':
                    gs = rec.result
                
            if gs:
                split_gs = gs.split(" ")
                if len(split_gs) == 3:
                    if split_gs[2] == 'POSITIF':
                        self.patient_id.blood_group = split_gs[0] + '+'
                        self.message_post(body=_("Carte de groupage sanguin imprimée" ))
                        return self.env.ref('acs_hms.patient_blood_card_report_action').report_action(self.patient_id)
                    elif split_gs[2] == 'NEGATIF':
                        self.patient_id.blood_group = split_gs[0] + '-'
                        self.message_post(body=_("Carte de groupage sanguin imprimée" ))
                        return self.env.ref('acs_hms.patient_blood_card_report_action').report_action(self.patient_id)
                    else:
                        raise UserError(_("Vérifiez l'orthographe des résultats du groupage sanguin"))
                else:
                    raise UserError(_("Vérifiez l'espacement des mots dans le résultat du groupage sanguin"))
            else:
                raise UserError(_("La première et deuxième déterminations ne sont pas identique"))



    def consume_lab_material(self):
        for rec in self:
            if not rec.company_id.laboratory_usage_location:
                raise UserError(_('Please define a location where the consumables will be used during the Laboratory test in company.'))
            if not rec.company_id.laboratory_stock_location:
                raise UserError(_('Please define a Laboratory location from where the consumables will be taken.'))
 
            dest_location_id  = rec.company_id.laboratory_usage_location.id
            source_location_id  = rec.company_id.laboratory_stock_location.id
            for line in rec.consumable_line_ids.filtered(lambda s: not s.move_id):
                move = self.consume_material(source_location_id, dest_location_id,
                    {
                        'product': line.product_id,
                        'qty': line.qty,
                    })
                move.lab_test_id = rec.id
                line.move_id = move.id

    def _compute_access_url(self):
        super(PatientLabTest, self)._compute_access_url()
        for rec in self:
            rec.access_url = '/my/lab_results/%s' % (rec.id)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: