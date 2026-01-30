# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Imagingprotocole(models.Model):
    _name = 'imaging.protocol'
    _description = "Protocole imagerie"

    name = fields.Char('Nom', required=True)
    test_id = fields.Many2one('acs.imaging.test',string='Test', ondelete='cascade')

class PatientImagingTestLine(models.Model):
    _name = "imaging.request.line"
    _description = "Test Lines"

    STATES = {'requested': [('readonly', True)], 'accepted': [('readonly', True)], 'in_progress': [('readonly', True)], 'cancel': [('readonly', True)], 'done': [('readonly', True)]}
    STATES_PROTOCOL = {'done': [('readonly', True)]}

    @api.depends('quantity', 'sale_price')
    def _compute_amount(self):
        for line in self:
            line.amount_total = line.quantity * line.sale_price

    test_id = fields.Many2one('acs.imaging.test',string='Test', ondelete='cascade', required=True, states=STATES)
    acs_tat = fields.Char(related='test_id.acs_tat', string='Turnaround Time', readonly=True, states=STATES)
    test_type = fields.Selection(related='test_id.test_type', string='Test Type', readonly=True, states=STATES)
    instruction = fields.Many2many('imaging.protocol',
                                  string='Protocole',
                                  domain="[('test_id', '=', test_id)]", copy=False, states=STATES_PROTOCOL)
    request_id = fields.Many2one('acs.imaging.request',string='Lines', ondelete='cascade', states=STATES)
    sale_price = fields.Float(string='Sale Price', states=STATES)
    company_id = fields.Many2one('res.company', ondelete='restrict', 
        string='Company',related='request_id.company_id') 
    quantity = fields.Integer(string='Quantity', default=1, states=STATES)
    amount_total = fields.Float(compute="_compute_amount", string="Sub Total", store=True, states=STATES)
    state = fields.Selection(related="request_id.state", store=True)

    @api.onchange('test_id')
    def onchange_test(self):
        if self.test_id:
            if self.request_id.pricelist_id:
                product_id = self.test_id.product_id.with_context(pricelist=self.request_id.pricelist_id.id)
                self.sale_price = product_id.price
            else:
                self.sale_price = self.test_id.product_id.lst_price


class ImagingRequest(models.Model):
    _name = 'acs.imaging.request'
    _description = 'Imaging Request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'acs.hms.mixin']
    _order = 'date desc, id desc'

    @api.depends('line_ids','line_ids.amount_total')
    def _get_total_price(self):
        for rec in self:
            rec.total_price = sum(line.amount_total for line in rec.line_ids)

    STATES = {'requested': [('readonly', True)], 'accepted': [('readonly', True)], 'in_progress': [('readonly', True)], 'cancel': [('readonly', True)], 'done': [('readonly', True)]}

    name = fields.Char(string='Imaging Request ID', readonly=True, index=True, copy=False, tracking=True)
    notes = fields.Text(string='Notes', states=STATES)
    date = fields.Datetime('Date', readonly=True, default=fields.Datetime.now, states=STATES, tracking=True)
    state = fields.Selection([
        ('draft','Accepté'),
        ('requested','Ordonnance vérifiée'),
        ('accepted','En attente'),
        ('in_progress','Acquisition en cours'),
        ('to_invoice','To Invoice'),
        ('done','Fait'),
        ('cancel','Annulé'),],
        string='State',readonly=True, default='draft', tracking=True)
    patient_id = fields.Many2one('hms.patient', string='Patient', required=True, ondelete='restrict', states=STATES, tracking=True)
    physician_id = fields.Many2one('hms.physician',
        string='Prescribing Doctor', help="Doctor who Request the lab test.", ondelete='restrict', states=STATES, tracking=True)
    invoice_id = fields.Many2one('account.move',string='Invoice', copy=False, states=STATES)
    imaging_bill_id = fields.Many2one('account.move',string='Vendor Bill', copy=False, states=STATES)
    line_ids = fields.One2many('imaging.request.line', 'request_id',
        string='Imaging Test Line', states=STATES, copy=True)
    no_invoice = fields.Boolean(string='Invoice Exempt', states=STATES)
    total_price = fields.Float(compute=_get_total_price, string='Total', store=True)
    info = fields.Text(string='Extra Info', states=STATES)
    #critearea_ids = fields.One2many('lab.test.critearea', 'request_id', string='Test Cases', states=STATES)
    company_id = fields.Many2one('res.company', ondelete='restrict', 
        string='Hospital', default=lambda self: self.env.user.company_id.id, states=STATES)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', check_company=True, 
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="If you change the pricelist, related invoice will be affected.")
    test_type = fields.Selection([
        ('CT', 'SCANNER'),
        ('MR', 'IRM'),
        ('exploration', 'EXPLORATION'),
        ('CR', 'RADIOGRAPHIE'),
        ('US', 'ECHOGRAPHIE'),
        ('MG', 'MAMMOGRAPHIE'),
        ('AU', 'ECG'),
        ('radio_int', 'RADIOLOGIE INTERVENTIONNELLE'),
    ], string='Test Type', states=STATES, default='CT')
    payment_state = fields.Selection(related="invoice_id.payment_state", store=True, string="Payment Status")
    acs_imaging_invoice_policy = fields.Selection(related="company_id.acs_imaging_invoice_policy")

    LABSTATES = {'cancel': [('readonly', True)], 'done': [('readonly', True)]}

    #other_laboratory = fields.Boolean(string='Send to Other Laboratory', states=LABSTATES)
    collection_center_id = fields.Many2one('acs.imaging', string='Collection Center', states=LABSTATES)
    imaging_id = fields.Many2one('acs.imaging', ondelete='restrict', string='Imaging', states=LABSTATES)

    #Just to make object selectable in selction field this is required: Waiting Screen
    acs_show_in_wc = fields.Boolean(default=True)
    is_group_request = fields.Boolean(default=False, states=STATES)
    group_patient_ids = fields.Many2many("hms.patient", "hms_patient_imaging_req_rel", "request_id", "patient_id", string="Other Group Patients", states=STATES)
    # Harnetprod
    health_service_id = fields.Many2one('acs.health_service', string='Service santé', readonly=True)
    group_manip = fields.Many2many(comodel_name='res.partner', string="Manipulateurs", domain=[('type_prof', '=', 'is_manip')], states=STATES)
    group_medimg = fields.Many2many('hms.physician', domain=[('medecin_smi', '=', True)], string="Médecin imagerie", states=STATES)
    prescripteur = fields.Many2one('res.partner', string='Médecin prescripteur',
                                   domain=[('is_referring_doctor', '=', True)], states=STATES)
    cabine_id = fields.Many2one('acs.imaging.cabine', ondelete='restrict', string='Salle', domain="[('test_type', '=', test_type),('company_id', '=', company_id)]")
    pj_count = fields.Integer(compute='_smart_pj_count', string='Ordonnances')
    department_id = fields.Many2one('hr.department', ondelete='restrict', string='Département', tracking=True)
    file_patient = fields.Char(string="Ticket patient", readonly=True)
    clinic_info = fields.Char("Renseignement clinique", states=STATES)
    description = fields.Char(related='health_service_id.desc', string="Description")
    acquisition_date = fields.Datetime("Date d'acquisition", readonly=True, states=STATES, tracking=True)

    @api.onchange('imaging_group_id')
    def onchange_imaging_group(self):
        test_line_ids = []
        if self.imaging_group_id:
            for line in self.imaging_group_id.line_ids:
                test_line_ids.append((0,0,{
                    'test_id': line.test_id.id,
                    'instruction': line.instruction,
                    'test_type' : line.test_type,
                    'sale_price' : line.sale_price,
                }))
            self.line_ids = test_line_ids

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_("Imaging Requests can be delete only in Draft state."))
        return super(ImagingRequest, self).unlink()

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

    def button_requested(self):
        if not self.line_ids:
            raise UserError(_('Please add at least one Imaging test line before submiting request.'))
        self.name = self.env['ir.sequence'].next_by_code('acs.imaging.request')
        self.date = fields.Datetime.now()
        # if self.is_group_request:
        #     for line in self.line_ids:
        #         line.quantity = len(self.group_patient_ids) + 1
        self.state = 'requested'

    def button_accept(self):
        self.state = 'accepted'

    def prepare_test_result_data(self, line, patient):
        manip_data = []
        medimg_data = []
        list_manip = self.mapped('group_manip')
        for manip in list_manip:
            manip_data.append(manip.id)

        domain = [  
                ('patient_id', '=', self.patient_id.id), 
                ('test_id', '=', line.test_id.id),  
                ('date_analysis', '<=', self.date),
                ('state', '=', 'done'),
        ]
        res = {
            'patient_id': patient.id,
            'mobile': patient.mobile,
            'physician_id': self.physician_id and self.physician_id.id,
            'prescripteur': self.prescripteur.id,
            'test_id': line.test_id.id,
            'user_id': self.env.user.id,
            'date_analysis': self.date,
            'request_id': self.id,
            'health_service_id': self.health_service_id.id,
            'department_id' : self.department_id.id,
            'clinic_info' : self.clinic_info,
            'old_interpretation': self.env['patient.imaging.test'].search(domain, limit=1, order="date_analysis desc").interpretation,
            'result_date_antérieur': self.env['patient.imaging.test'].search(domain, limit=1, order="date_analysis desc").date_analysis,
            'old_rc': self.env['patient.imaging.test'].search(domain, limit=1, order="date_analysis desc").clinic_info,
        }
        return res

    # def prepare_test_result_data(self, line, patient):
    #     manip_data = []
    #     medimg_data = []
    #     list_manip = self.mapped('group_manip')
    #     for manip in list_manip:
    #         manip_data.append(manip.id)

    #     list_medimg = self.mapped('group_medimg')
    #     for medimg in list_medimg:
    #         medimg_data.append(medimg.id)
    #     res = {
    #         'patient_id': patient.id,
    #         'mobile': patient.mobile,
    #         #'physician_id': self.physician_id and self.physician_id.id,
    #         'test_id': line.test_id.id,
    #         'user_id': self.env.user.id,
    #         'date_analysis': self.date,
    #         'request_id': self.id,
    #         'group_manip': [(6, 0, manip_data)],
    #         'group_medimg': [(6, 0, medimg_data)],
    #         'prescripteur': self.prescripteur and self.prescripteur.id,
    #     }
    #     return res

    def button_in_progress(self):
        self.state = 'in_progress'

    def button_done(self):
        IMGTest = self.env['patient.imaging.test']
        patients = self.mapped('patient_id') + self.mapped('group_patient_ids')
        for line in self.line_ids:
            for patient in patients:
                img_test_data = self.prepare_test_result_data(line, patient)
                IMGTest.create(img_test_data)
        self.acquisition_date = fields.Datetime.now()
        self.state = 'done'

    def button_cancel(self):
        self.state = 'cancel'

    def button_draft(self):
        self.state = 'draft'    

    def create_invoicew(self):
        if not self.line_ids:
            raise UserError(_("Please add lab Tests first."))

        product_data = []
        for line in self.line_ids:
            product_data.append({
                'product_id': line.test_id.product_id,
                'price_unit': line.sale_price,
                'quantity': line.quantity,
            })
        pricelist_context = {}
        if self.pricelist_id:
            pricelist_context = {'acs_pricelist_id': self.pricelist_id.id}

        invoice = self.with_context(pricelist_context).acs_create_invoice(partner=self.patient_id.partner_id, patient=self.patient_id, product_data=product_data, inv_data={'hospital_invoice_type': 'imaging','physician_id': self.physician_id and self.physician_id.id or False})
        self.invoice_id = invoice.id
        invoice.img_request_id = self.id
        if self.state == 'to_invoice':
            self.state = 'done'

    def create_imaging_bill(self):
        if not self.line_ids:
            raise UserError(_("Please add Imaging Tests first."))

        product_data = []
        for line in self.line_ids:
            product_data.append({
                'product_id': line.test_id.product_id,
                'price_unit': line.test_id.product_id.standard_price,
            })

        inv_data={'type': 'in_invoice'}
        bill = self.acs_create_invoice(partner=self.imaging_id.partner_id, patient=self.patient_id, product_data=product_data, inv_data=inv_data)
        self.imaging_bill_id = bill.id
        bill.request_id = self.id

    def view_invoice(self):
        invoices = self.mapped('invoice_id')
        action = self.acs_action_view_invoice(invoices)
        return action

    def action_view_test_results(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.action_imaging_result")
        action['domain'] = [('request_id','=',self.id)]
        action['context'] = {'default_request_id': self.id, 'default_physician_id': self.physician_id.id}
        return action

    # def action_view_imaging_samples(self):
    #     action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.action_acs_patient_imaging_sample")
    #     action['domain'] = [('request_id','=',self.id)]
    #     action['context'] = {'default_request_id': self.id}
    #     return action
    
    def action_sendmail(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('acs_imaging', 'acs_imaging_req_email')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'acs.imaging.request',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
