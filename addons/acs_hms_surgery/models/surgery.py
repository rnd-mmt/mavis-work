# coding=utf-8
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ACSSurgeryTemplate(models.Model):
    _name = "hms.surgery.template"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'acs.hms.mixin']
    _description = "Surgery Template"

    name= fields.Char(string='Surgery Code', 
        help="Procedure Code, for example ICD-10-PCS Code 7-character string")
    surgery_name= fields.Char (string='Surgery Name', tracking=True)
    diseases_id = fields.Many2one ('hms.diseases', ondelete='restrict', string='Disease', help="Reason for the surgery.", tracking=True)
    dietplan = fields.Many2one('hms.dietplan', ondelete='set null', string='Diet Plan', tracking=True)
    surgery_product_id = fields.Many2one('product.product', ondelete='cascade',
        string= "Product", required=True, tracking=True)
    diagnosis = fields.Text(string="Diagnosis", tracking=True)
    clinincal_history = fields.Text(string="Clinical History", tracking=True)
    examination = fields.Text(string="Examination", tracking=True)
    investigation = fields.Text(string="Investigation", tracking=True)
    adv_on_dis = fields.Text(string="Advice on Discharge", tracking=True)
    notes = fields.Text(string='Operative Notes', tracking=True)
    classification = fields.Selection ([
        ('o','Optional'),
        ('r','Required'),
        ('u','Urgent')], string='Surgery Classification', index=True, tracking=True)
    extra_info = fields.Text (string='Extra Info', tracking=True)
    special_precautions = fields.Text(string="Special Precautions", tracking=True)
    consumable_line_ids = fields.One2many('hms.consumable.line', 'surgery_template_id', string='Consumable Line', help="List of items that are consumed during the surgery.")
    medicament_line_ids = fields.One2many('medicament.line', 'surgery_template_id', string='Medicament Line', help="Define the medicines to be taken after the surgery")
    company_id = fields.Many2one('res.company', ondelete='restrict', 
        string='Hospital', default=lambda self: self.env.user.company_id.id)


class ACSSurgery(models.Model):
    _name = "hms.surgery"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'acs.hms.mixin']
    _description = "Surgery"

    @api.model
    def _default_prechecklist(self):
        vals = []
        prechecklists = self.env['pre.operative.check.list.template'].search([])
        for prechecklist in prechecklists:
            vals.append((0,0,{
                'name': prechecklist.name,
                'remark': prechecklist.remark,
            }))
        return vals

    @api.depends('pre_operative_checklist_ids','pre_operative_checklist_ids.is_done')
    def _compute_checklist_done(self):
        for rec in self:
            if rec.pre_operative_checklist_ids:
                done_checklist = rec.pre_operative_checklist_ids.filtered(lambda s: s.is_done)
                rec.pre_operative_checklist_done = (len(done_checklist)* 100)/len(rec.pre_operative_checklist_ids)
            else:
                rec.pre_operative_checklist_done = 0

    STATES = {'cancel': [('readonly', True)], 'done': [('readonly', True)]}

    name = fields.Char(string='Surgery Number', copy=False, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancelled'),
        ('done', 'Done'),], string='Status', default='draft', states=STATES, tracking=True)
    surgery_name= fields.Char (string='Surgery Name', states=STATES, tracking=True)
    diseases_id = fields.Many2one ('hms.diseases', ondelete='restrict', 
        string='Disease', help="Reason for the surgery.", states=STATES, tracking=True)
    dietplan = fields.Many2one('hms.dietplan', ondelete='set null', 
        string='Diet Plan', states=STATES, tracking=True)
    surgery_product_id = fields.Many2one('product.product', ondelete='cascade',
        string= "Surgery Product", required=True, states=STATES, tracking=True)
    surgery_template_id = fields.Many2one('hms.surgery.template', ondelete='restrict',
        string= "Surgery Template", states=STATES, tracking=True)
    patient_id = fields.Many2one('hms.patient', ondelete="restrict", string='Patient', states=STATES, tracking=True)
    diagnosis = fields.Text(string="Diagnosis", states=STATES, tracking=True)
    clinincal_history = fields.Text(string="Clinical History", states=STATES, tracking=True)
    examination = fields.Text(string="Examination", states=STATES, tracking=True)
    investigation = fields.Text(string="Investigation", states=STATES, tracking=True)
    adv_on_dis = fields.Text(string="Advice on Discharge", states=STATES, tracking=True)
    notes = fields.Text(string='Operative Notes', states=STATES, tracking=True)
    classification = fields.Selection ([
            ('o','Optional'),
            ('r','Required'),
            ('u','Urgent')
        ], string='Surgery Classification', index=True, states=STATES, tracking=True)
    age = fields.Char(string='Patient age',
        help='Patient age at the moment of the surgery. Can be estimative', states=STATES)
    extra_info = fields.Text (string='Extra Info', states=STATES, tracking=True)
    special_precautions = fields.Text(string="Special Precautions", states=STATES, tracking=True)
    consumable_line_ids = fields.One2many('hms.consumable.line', 'surgery_id', string='Consumable Line', help="List of items that are consumed during the surgery.", states=STATES)
    medicament_line_ids = fields.One2many('medicament.line', 'surgery_id', string='Medicament Line', help="Define the medicines to be taken after the surgery", states=STATES)

    #Hospitalization Surgery
    start_date = fields.Datetime(string='Surgery Date', states=STATES, tracking=True)
    end_date = fields.Datetime(string='End Date', states=STATES, tracking=True)
    anesthetist_id = fields.Many2many('hms.physician', string='Anesthetist',
        help='Anesthetist data of the patient', states=STATES, tracking=True)
    anesthesia_id = fields.Many2many('hms.anesthesia',
        string="Anesthesia", states=STATES, tracking=True)
    primary_physician = fields.Many2one ('hms.physician', ondelete="restrict", 
        string='Main Surgeon', states=STATES, tracking=True)
    primary_physician_ids = fields.Many2many('hms.physician','hosp_pri_doc_rel','hosp_id','doc_id',
        string='Primary Surgeons', states=STATES, tracking=True)
    assisting_surgeons = fields.Many2many('hms.physician','hosp_doc_rel','hosp_id','doc_id',
        string='Assisting Surgeons', states=STATES, tracking=True)
    scrub_nurse = fields.Many2many('res.users',
        string='Scrub Nurse', states=STATES, tracking=True)
    pre_operative_checklist_ids = fields.One2many('pre.operative.check.list', 'surgery_id', 
        string='Pre-Operative Checklist', default=lambda self: self._default_prechecklist(), states=STATES, tracking=True)
    pre_operative_checklist_done = fields.Float('Pre-Operative Checklist Done', compute='_compute_checklist_done', store=True, tracking=True)
    notes = fields.Text(string='Operative Notes', states=STATES, tracking=True)
    post_instruction = fields.Text(string='Instructions', states=STATES, tracking=True)

    special_precautions = fields.Text(string="Special Precautions", states=STATES, tracking=True)
    company_id = fields.Many2one('res.company', ondelete='restrict', 
        string='Hospital', default=lambda self: self.env.user.company_id.id)
    invoice_id = fields.Many2one('account.move', string='Invoice', copy=False)
    intervention = fields.Text(string="Intervention", states=STATES, tracking=True)
    compte_rendu = fields.Text(string="Compte rendu", states=STATES, tracking=True)
    soins_postop = fields.Text(string="Soins post-opératoires", states=STATES, tracking=True)
    # =====Vérifier état bouton create service============
    check_btn_service = fields.Boolean(string='Créer service santé exécuté', default=False)

    @api.onchange('surgery_template_id')
    def on_change_surgery_id(self):
        medicament_lines = []
        consumable_lines = []
        Consumable = self.env['hms.consumable.line']
        if self.surgery_template_id:
            self.surgery_name = self.surgery_template_id.surgery_name
            self.diseases_id = self.surgery_template_id.diseases_id and self.surgery_template_id.diseases_id.id
            self.surgery_product_id = self.surgery_template_id.surgery_product_id and self.surgery_template_id.surgery_product_id.id
            self.diagnosis = self.surgery_template_id.diagnosis
            self.clinincal_history = self.surgery_template_id.clinincal_history
            self.examination = self.surgery_template_id.examination
            self.investigation = self.surgery_template_id.investigation
            self.adv_on_dis = self.surgery_template_id.adv_on_dis
            self.notes = self.surgery_template_id.notes
            self.classification = self.surgery_template_id.classification

            for line in self.surgery_template_id.consumable_line_ids:
                self.consumable_line_ids += Consumable.new({
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom and line.product_uom.id or False,
                    'qty': line.qty,
                })

            for line in self.surgery_template_id.medicament_line_ids:
                medicament_lines.append((0,0,{
                    'product_id': line.product_id.id,
                    'common_dosage_id': line.common_dosage_id and line.common_dosage_id.id or False,
                    'dose': line.dose,
                    'active_component_ids': [(6, 0, [x.id for x in line.active_component_ids])],
                    'form_id' : line.form_id.id,
                    'qty': line.qty,
                    'instruction': line.instruction,
                }))
                self.medicament_line_ids = medicament_lines

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('hms.surgery') or 'Surgery#'
        return super(ACSSurgery, self).create(values)

    def action_confirm(self):
        self.state = 'confirm'

    def action_done(self):
        self.state = 'done'
        #self.consume_surgery_material()

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'

    def consume_surgery_material(self):
        for rec in self:
            if not rec.company_id.surgery_usage_location:
                raise UserError(_('Please define a location where the consumables will be used in settings.'))
            if not rec.hospital_ot.source_location_id:
                raise UserError(_('Please define a surgery location from where the consumables will be taken.'))
            # source_location_id  = rec.company_id.surgery_stock_location.id
            source_location_id = rec.hospital_ot.source_location_id.id
            dest_location_id  = rec.company_id.surgery_usage_location.id
            for line in rec.consumable_line_ids.filtered(lambda s: not s.move_id):
                move = self.consume_material(source_location_id, dest_location_id,
                    {
                        'product': line.product_id,
                        'qty': line.qty
                    })
                move.surgery_id = rec.id
                line.move_id = move.id

    def get_surgery_invoice_data(self):
        product_data = [{
            'name': _("Surgery Charges"),
        }]
        for surgery in self:
            if surgery.surgery_product_id:
                #Line for Surgery Charge
                product_data.append({
                    'product_id': surgery.surgery_product_id,
                    'quantity': 1,
                })

            #Line for Surgery Consumables
            for surgery_consumable in surgery.consumable_line_ids:
                product_data.append({
                    'product_id': surgery_consumable.product_id,
                    'quantity': surgery_consumable.qty,
                })
        return product_data

    def action_create_invoice(self):
        product_data = self.get_surgery_invoice_data()
        inv_data = {
            'physician_id': self.primary_physician and self.primary_physician.id or False,
        }

        invoice_id = self.acs_create_invoice(partner=self.patient_id.partner_id, patient=self.patient_id, product_data=product_data, inv_data=inv_data)
        invoice_id.write({
            'surgery_id': self.id,
        })
        self.invoice_id = invoice_id.id
        return invoice_id

    def generate_service(self):
        self.ensure_one()
        product_line = []
        vals_product = {
            'product': self.surgery_product_id.id,
            'sale_price': self.surgery_product_id.lst_price,
            'name': self.surgery_product_id.name,
            'product_uom': self.surgery_product_id.uom_id.id,
            'quantity': 1,
        }
        product_line.append((0,0, vals_product))
        for line in self.consumable_line_ids:
            vals = {
                'product': line.product_id.id,
                'sale_price': line.product_id.lst_price,
                'name': line.product_id.name,
                'product_uom': line.product_id.uom_id.id,
                'quantity': line.qty,
            }
            product_line.append((0, 0, vals))
        vals_service = []
        serv_vals = {
            'patient_id': self.patient_id.id,
            'ref_acte': self.name,
            'service_line': product_line,
            'show_update_pricelist': True,
            'pricelist_id': self.patient_id.property_product_pricelist.id,
        }
        if len(product_line) > 0:
            service = self.env['acs.health_service'].sudo().create(serv_vals)
            vals_service.append((4, service.id))
            self.check_btn_service = True
        else:
            raise UserError(_("Liste de produits vide."))