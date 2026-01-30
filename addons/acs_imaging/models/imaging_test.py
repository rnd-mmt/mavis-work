# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
import uuid

class ImagingInterpretationTemplate(models.Model):
    _name = 'imaging.template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Imaging Template Report'

    name = fields.Char("Modèle")
    interpretation_content = fields.Html("Contenu de l'interprétation")
    user_id = fields.Many2one('res.users', string="Utilisateurs")

class PatientImagingTest(models.Model):
    _name = "patient.imaging.test"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'acs.hms.mixin', 'portal.mixin', 'acs.documnt.mixin', 'acs.qrcode.mixin']
    _description = "Patient Imaging Test"
    _order = 'date_analysis desc, id desc'

    @api.model
    def _get_disclaimer(self):
        return self.env.user.sudo().company_id.acs_imaging_disclaimer or ''

    STATES = {'cancel': [('readonly', True)], 'done': [('readonly', True)]}

    name = fields.Char(string='Test ID', help="Imaging result ID", readonly="1",copy=False, index=True, tracking=True)
    mobile = fields.Char(string='Mobile', copy=False, states=STATES, tracking=True)
    test_id = fields.Many2one('acs.imaging.test', string='Test', required=True, ondelete='restrict', states=STATES, tracking=True)
    patient_id = fields.Many2one('hms.patient', string='Patient', required=True, ondelete='restrict', states=STATES, tracking=True)
    user_id = fields.Many2one('res.users',string='Imaging User', default=lambda self: self.env.user, states=STATES)
    physician_id = fields.Many2one('hms.physician',string='Prescribing Doctor', help="Doctor who requested the test", ondelete='restrict', states=STATES)
    diagnosis = fields.Text(string='Diagnosis', states=STATES)
    #critearea_ids = fields.One2many('lab.test.critearea', 'patient_lab_id', string='Test Cases', copy=True, states=STATES)
    date_requested = fields.Datetime(string='Date de la demande', states=STATES)
    date_analysis = fields.Date(string='Date résultat', default=fields.Date.context_today, states=STATES)
    request_id = fields.Many2one('acs.imaging.request', string="Demande d'imagerie", ondelete='restrict', states=STATES)
    imaging_id = fields.Many2one('acs.imaging', related="request_id.imaging_id", string='Imaging', readonly=True, store=True)
    report = fields.Text(string='Test Report', states=STATES)
    note = fields.Text(string='Extra Info', states=STATES)
    #sample_ids = fields.Many2many('acs.patient.laboratory.sample', 'test_lab_sample_rel', 'test_id', 'sample_id', string='Test Samples', states=STATES)
    company_id = fields.Many2one('res.company', ondelete='restrict', 
        string='Company',default=lambda self: self.env.user.company_id.id, states=STATES)
    state = fields.Selection([
        ('draft','Draft'),
        ('assign_pret', 'Interprétation assignée'),
        ('pret', 'Interprété'),
        ('assign_relu', 'Relecture assignée'),
        ('relu', 'Relu'),
        ('done','Mise en enveloppe'),
        ('deliver', 'Résultat livré'),
        ('verified', 'Revérifié'),
        ('cancel','Cancel'),
    ], string='State', default='draft', tracking=True)
    disclaimer = fields.Text("Dislaimer", states=STATES, default=_get_disclaimer)
    collection_center_id = fields.Many2one('acs.imaging', string='Collection Center', related="request_id.collection_center_id", states=STATES)

    group_manip = fields.Many2many('res.partner', string="Manipulateurs/Aide-soignants", domain=[('type_prof', '=', 'is_manip')],tracking=True)
    group_medimg_interpret = fields.Many2many('hms.physician', 'medimg_interpret_rel', domain=[('medecin_smi', '=', True)], string="Médecin imagerie", states=STATES,tracking=True)
    group_medimg_relecture = fields.Many2many('hms.physician', 'medimg_relecture_rel', domain=[('medecin_smi', '=', True)], string="Médecin imagerie",tracking=True)
    interpretation = fields.Html('Interpretation', states=STATES)
    
    #Just to make object selectable in selction field this is required: Waiting Screen
    acs_show_in_wc = fields.Boolean(default=True)
    prescripteur = fields.Many2one('res.partner', string='Médecin prescripteur',
                                   domain=[('is_referring_doctor', '=', True)], states=STATES)
    template = fields.Many2one('imaging.template', string="Modèle compte rendu")
    health_service_id = fields.Many2one('acs.health_service', string='Service santé', readonly=True)
    description = fields.Char(related='health_service_id.desc', string="Description")
    editable_reason = fields.Text(string="Motif de revérification", states=STATES)
    reverifed_user_id = fields.Many2one('res.users', string='Re-vérifié par', readonly=True)
    #===============Historique resultat=============
    print_state = fields.Selection([
        ('to_do', 'A faire'),
        ('assign', 'Assigné'),
        #('in_progress', 'En cours'),
        ('done', 'Fait'),
    ], string='Impr. cliché/image/tracé/gravage', tracking=True)
    interpretation_state = fields.Selection([
        ('to_do', 'A faire'),
        ('assign', 'Assigné'),
        #('in_progress', 'En cours'),
        ('done', 'Fait'),
    ], string='Interprétation', tracking=True)
    relecture_state = fields.Selection([
        ('to_do', 'A faire'),
        ('assign', 'Assigné'),
        #('in_progress', 'En cours'),
        ('done', 'Fait'),
    ], string='Relecture', tracking=True)
    resp_cliche = fields.Many2one('res.users', string='Chargé impression cliché', readonly=True, tracking=True, store=True)
    resp_relecture = fields.Many2one('res.users', string='Responsable relecture', readonly=True, tracking=True, store=True)
    resp_interpretation = fields.Many2one('res.users', string='Responsable interprétation', readonly=True, tracking=True, store=True)
    # ====== Consumable lines =========
    imaging_consumable_line_ids = fields.One2many('imaging.consumable.line', 'imaging_id', string='imaging line',
                                                  states=STATES)
    mvt_stock = fields.Boolean('Mouvement de stock effectué')
    diseases_ids = fields.Many2many('hms.diseases', 'diseases_img_rel', 'diseas_id', 'imaging_id',
                                    'Hypothèse diagnostique', states=STATES)
    department_id = fields.Many2one('hr.department', ondelete='restrict', string='Department', tracking=True)
    clinic_info = fields.Char("Renseignement clinique")
    make_envelope = fields.Selection([
        ('to_do', 'A faire'),
        ('assign', 'Assigné'),
        #('in_progress', 'En cours'),
        ('done', 'Fait'),
    ], string='Mise en enveloppe', tracking=True)
    resp_enveloppe = fields.Many2one('res.users', string='Responsable mise en enveloppe', readonly=True, tracking=True, store=True)
    resp_saisie = fields.Many2one('res.users', string='Responsable saisie', readonly=True, tracking=True, store=True)

    #==Resultat antérieur ==
    old_interpretation = fields.Html('Interpretation antérieur', states=STATES)
    result_date_antérieur = fields.Date(string='Date résultat antérieur')
    old_rc = fields.Char(string="RC antérieur")

    #====INFO APPAREIL ====
    device = fields.Many2one('imaging.device', string="Appareil d'acquisition", domain=[('type', '=', 'automate')], tracking=True, states=STATES)
    device_firt_using = fields.Char(related="device.first_date")
    sonde = fields.Many2many('imaging.device', string="Sondes", domain=[('type', '=', 'consommable')], tracking=True, states=STATES)
    pdl_t = fields.Integer(string="PDL T", help="mGy*cm", states=STATES)
    instruction = fields.Many2one('imaging.protocol', string="Technique d'acquisition", domain="[('test_id', '=', test_id)]", copy=False, states=STATES)
    pj_count = fields.Integer(compute='_smart_pj_count', string='Ordonnances')
    interp_jr = fields.Html('Interpretation pour medecin junior', states=STATES)
    is_jr_doctor = fields.Boolean(compute='_compute_is_jr_doctor')

    _sql_constraints = [
        ('name_company_uniq', 'unique (name,company_id)', 'Test Name must be unique per company !')
    ]

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('patient.imaging.test')
        res = super(PatientImagingTest, self).create(vals)
        res.unique_code = uuid.uuid4()
        return res

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_("Imaging Test can be delete only in Draft state."))
        return super(PatientImagingTest, self).unlink()

    def get_previous_result(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.action_get_img_resultat_anterieur_wizard")
        action['context'] = {
            'active_model':'patient.imaging.test',
        }
        return action

    #=== VOIR ORDONNANCE ==
    def action_open_pj(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ordonnances',
            'res_model': 'ir.attachment',
            'domain': [('res_model', '=', 'acs.health_service'),('res_id', '=', self.health_service_id.id)],
            'context': {
                'default_res_model': 'acs.health_service',
                'default_is_document': True
            },
            'view_mode': 'tree,form',
            'target': 'current',
        }

    def _smart_pj_count(self):
        for rec in self:
            pj_count = self.env['ir.attachment'].search_count([('res_model', '=', 'acs.health_service'),
                        ('res_id', '=', rec.health_service_id.id)])
            rec.pj_count = pj_count

    @api.onchange('template')
    def onchange_template(self):
        if self.template:
            template_id = self.template.id
            modele = self.env['imaging.template'].search([('id', '=', template_id)])
            self.interp_jr = modele.interpretation_content

    def _compute_is_jr_doctor(self):
        self.is_jr_doctor = self.env.user.has_group("acs_imaging.group_imaging_jr_doctor")

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
        return res   

    @api.onchange('request_id')
    def onchange_request_id(self):
        if self.request_id and self.request_id.date:
            self.date_requested = self.request_id.date

    def reverified_record(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.action_imaging_reverificaiton_reason")
        action['context'] = {
            'active_model':'patient.imaging.test',
        }
        return action

    def action_verified(self):
        if not self.reverifed_user_id:
            self.reverifed_user_id = self.env.uid
        self.state = 'verified'

    def input_interp_done(self):
        if not self.resp_saisie:
            self.resp_saisie = self.env.uid 

    def make_envelope_tree(self):
        active_ids = self.env.context.get("active_ids", [])
        img_results = self.env['patient.imaging.test'].browse(active_ids)
        for img_result in img_results:
            if img_result.state != 'relu':
                raise UserError(_("L'enregistrement doit être en état relû."))
            img_result.resp_enveloppe = self.env.uid
            img_result.make_envelope = 'done'
            img_result.state = 'done'

    def delivered(self):
        if self.state != 'done':
            raise UserError(_("L'enregistrement est déjà en état Mise en enveloppe."))
        self.state = 'deliver'

    def delivered_tree(self):
        active_ids = self.env.context.get("active_ids", [])
        img_results = self.env['patient.imaging.test'].browse(active_ids)
        for img_result in img_results:
            img_result.delivered()

    def action_print_cliche(self):
        self.resp_cliche = self.env.uid
        self.print_state = 'done'

    def action_assign_pret(self):
        if self.resp_interpretation:
            raise UserError(_("L'interprétation est déjà assignée à un médecin."))
        else:
            self.resp_interpretation = self.env.uid
            self.interpretation_state = 'assign'
            self.state = 'assign_pret'

    def action_interpretation_done(self):
        if self.resp_interpretation.id != self.env.uid:
            raise UserError(_("Vous n'êtes pas autorisé à faire cette opération"))
        else:
            self.interpretation_state = 'done'
            self.state = 'pret'

    def action_assign_relu(self):
        if self.resp_relecture:
            raise UserError(_("La relecture est déjà assignée à un médecin."))
        else:
            self.resp_relecture = self.env.uid
            self.interpretation = self.interp_jr
            self.relecture_state = 'assign'
            self.state = 'assign_relu'

    def action_relecture_done(self):
        if self.resp_relecture.id != self.env.uid:
            raise UserError(_("Vous n'êtes pas autorisé à faire cette opération"))
        else:
            self.relecture_state = 'done'
            self.state = 'relu'

    def action_mise_enveloppe(self):
        self.resp_enveloppe = self.env.uid
        self.make_envelope = 'done'
        self.state = 'done'

    def action_redone(self):
        #self.consume_lab_material()
        self.resp_relecture = self.env.uid
        self.state = 'relu'

    def action_cancel(self):
        self.state = 'cancel'

    @api.model
    def _prepare_pick_vals(self, line=False, stock_id=False):
        pick_vals = {
            'product_id': line.product_id.id,
            'product_uom_qty': line.quantity,
            'product_uom': line.product_uom.id,
            'location_id': self.collection_center_id.source_location_id.id,
            'location_dest_id': self.company_id.prescription_usage_location_id.id,
            'name': line.product_id.name,
            'picking_type_id': self.custom_picking_type_id.id,
            'picking_id': stock_id.id,
            'company_id': line.company_id.id,
        }
        return pick_vals

    def consume_imaging_medicament(self):
        stock_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        for rec in self:
            if not rec.company_id.imaging_usage_location:
                raise UserError(_('Please define a imaging location where the consumables will be used.'))
            if not rec.collection_center_id.source_location_id:
                raise UserError(_('Please define a imaging location from where the consumables will be taken.'))

            dest_location_id = rec.company_id.imaging_usage_location.id
            source_location_id = rec.collection_center_id.source_location_id.id

            for line in rec.imaging_consumable_line_ids:
                verified = self.env['stock.quant'].search(['&', '&', '&', ('product_id', '=', line.product_id.id),
                                                           ('location_id', '=', source_location_id),
                                                           ('lot_id', '=', line.lot_id.id),
                                                           ('company_id', '=', line.company_id.id)])
                if line.lot_id:
                    if verified:
                        qte_demande = 0.0
                        qte_demande = line.quantity
                        self.consume_material(source_location_id, dest_location_id,
                                              {
                                                  'product': line.product_id,
                                                  'lot_id': line.lot_id,
                                                  'qty': qte_demande,
                                                  'product_uom': line.product_uom.id,
                                              })
                        stock_id = stock_obj.search([('origin', '=', rec.name)])
                        if stock_id:
                            pick_vals = rec._prepare_pick_vals(line, stock_id, line.quantity)
                            move_id = move_obj.sudo().create(pick_vals)
                    else:
                        raise UserError(
                            _("Votre département n'a pas de lot %s en sotck", line.lot_id.name))
        self.mvt_stock = True

    def _compute_access_url(self):
        super(PatientImagingTest, self)._compute_access_url()
        for rec in self:
            rec.access_url = '/my/imaging_results/%s' % (rec.id)

class ImagingReport(models.AbstractModel):
    _name = 'report.acs_imaging.img_report'
    _description = 'Imaging Report'

    @api.model
    def _get_report_values(self, docids, data=None):        
        env = api.Environment(self.env.cr, SUPERUSER_ID, {})        
        mavis_user = self.env.user.sudo()        
        odoobot_id = env['ir.model.data'].xmlid_to_res_id('base.partner_root')
        odoobot = env['res.partner'].browse(odoobot_id)
        records = env['patient.imaging.test'].browse(docids)
        if records: 
            for record in records:
                message = f"Imprimé par <b>{mavis_user.name}.</b>"
                record.message_post(
                    body=message,
                    message_type='comment',
                    subtype_xmlid='mail.mt_note',
                    author_id=odoobot.id,
                    attachment_ids=False,
                )
        return {
            'doc_ids': docids,
            'doc_model': 'patient.imaging.test',
            'docs': records,
            'user': odoobot.id,
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: