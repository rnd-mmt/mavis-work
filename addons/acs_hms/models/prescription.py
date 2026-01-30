# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError
import time
import uuid


class ACSPrescriptionOrder(models.Model):
    _name='prescription.order'
    _description = "Prescription Order"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'acs.hms.mixin', 'acs.qrcode.mixin']
    _order = 'id desc'

    @api.model
    def _current_user_doctor(self):
        physician_id =  False
        ids = self.env['hms.physician'].search([('user_id', '=', self.env.user.id)])
        if ids:
            physician_id = ids[0].id
        return physician_id


    @api.depends('medical_alert_ids')
    def _get_alert_count(self):
        for rec in self:
            rec.alert_count = len(rec.medical_alert_ids)

    READONLY_STATES={'cancel': [('readonly', True)], 'prescription': [('readonly', True)]}

    name = fields.Char(size=256, string='Prescription Number', help='Prescription Number of this prescription', readonly=True, copy=False, tracking=True)
    diseases_ids = fields.Many2many('hms.diseases', 'diseases_prescription_rel', 'diseas_id', 'prescription_id', 
        string='Diseases', states=READONLY_STATES, tracking=True)
    group_id = fields.Many2one('medicament.group', ondelete="set null", string='Medicaments Group', states=READONLY_STATES, copy=False)
    patient_id = fields.Many2one('hms.patient', ondelete="restrict", string='Patient', required=True, states=READONLY_STATES, tracking=True)
    pregnancy_warning = fields.Boolean(string='Pregnancy Warning', states=READONLY_STATES)
    notes = fields.Text(string='Prescription Notes', states=READONLY_STATES)
    prescription_line_ids = fields.One2many('prescription.line', 'prescription_id', string='Prescription line')
    company_id = fields.Many2one('res.company', ondelete="cascade", string='Hospital',default=lambda self: self.env.company.id, states=READONLY_STATES)
    prescription_date = fields.Datetime(string='Prescription Date', required=True, default=fields.Datetime.now, states=READONLY_STATES, tracking=True, copy=False)
    physician_id = fields.Many2one('hms.physician', ondelete="restrict", string='Prescribing Doctor',
        states=READONLY_STATES, default=_current_user_doctor, tracking=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('prescription', 'Prescrit'),
        ('part_deliver', 'Partiellement livrés'),
        ('deliver', 'Médicaments livrés'),
        ('canceled', 'Annulé')], string='State', default='draft', tracking=True)
    appointment_id = fields.Many2one('hms.appointment', ondelete="restrict", 
        string='Appointment', states=READONLY_STATES)
    patient_age = fields.Char(related='patient_id.age', string='Age', store=True, readonly=True)
    treatment_id = fields.Many2one('hms.treatment', 'Treatment', states=READONLY_STATES)
    medical_alert_ids = fields.Many2many('acs.medical.alert', 'prescription_medical_alert_rel','prescription_id', 'alert_id',
        string='Medical Alerts', related="patient_id.medical_alert_ids")
    alert_count = fields.Integer(compute='_get_alert_count', default=0)
    old_prescription_id = fields.Many2one('prescription.order', 'Old Prescription', copy=False, states=READONLY_STATES)
    # =====relation à stock============
    dep_location = fields.Many2one('prescription.location.stock', string='Departement',
                                   domain="[('company_id', '=', company_id)]", )
    check_btn_service = fields.Boolean(string='Créer service santé exécuté', default=False)
    #=====Tye de prelevement===
    custom_picking_type_id = fields.Many2one('stock.picking.type', string='Type de prélèvement', copy=False)

    @api.model
    def create(self, values):
        res = super(ACSPrescriptionOrder, self).create(values)
        res.unique_code = uuid.uuid4()
        return res

    @api.onchange('group_id')
    def on_change_group_id(self):
        product_lines = []
        for rec in self:
            appointment_id = rec.appointment_id and rec.appointment_id.id or False
            for line in rec.group_id.medicament_group_line_ids:
                product_lines.append((0,0,{
                    'product_id': line.product_id.id,
                    'common_dosage_id': line.common_dosage_id and line.common_dosage_id.id or False,
                    'dose': line.dose,
                    'active_component_ids': [(6, 0, [x.id for x in line.product_id.active_component_ids])],
                    'form_id' : line.product_id.form_id.id,
                    'qty_per_day': line.dose,
                    'days': line.days,
                    'short_comment': line.short_comment,
                    'allow_substitution': line.allow_substitution,
                    'appointment_id': appointment_id,
                }))
            rec.prescription_line_ids = product_lines

    @api.onchange('appointment_id')
    def onchange_appointment(self):
        if self.appointment_id and self.appointment_id.treatment_id:
            self.treatment_id = self.appointment_id.treatment_id.id

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_('Prescription Order can be delete only in Draft state.'))
        return super(ACSPrescriptionOrder, self).unlink()

    def button_reset(self):
        self.write({'state': 'draft'})

    def button_confirm(self):
        for app in self:
            if not app.prescription_line_ids:
                raise UserError(_('You cannot confirm a prescription order without any order line.'))

            app.state = 'prescription'
            if not app.name:
                app.name = self.env['ir.sequence'].next_by_code('prescription.order') or '/'

    def button_delivrer(self):
        self.state = 'deliver'

    def print_report(self):
        return self.env.ref('acs_hms.report_hms_prescription_id').report_action(self)

    @api.onchange('patient_id')
    def onchange_patient(self):
        if self.patient_id:
            prescription = self.search([('patient_id', '=', self.patient_id.id),('state','=','prescription')], order='id desc', limit=1)
            self.dep_location = self.env['prescription.location.stock'].search([('company_id', '=', self.company_id.id)], order='id desc', limit=1).id
            self.custom_picking_type_id = self.env['stock.picking.type'].search(['&','&',('company_id', '=', self.company_id.id),('code', '=', 'outgoing'),('sequence_code', '=', 'OUT')], order='id desc', limit=1).id
            self.old_prescription_id = prescription.id if prescription else False

    @api.onchange('pregnancy_warning')
    def onchange_pregnancy_warning(self):
        if self.pregnancy_warning:
            warning = {}
            message = ''
            for line in self.prescription_line_ids:
                if line.product_id.pregnancy_warning:
                    message += _("%s Medicine is not Suggastable for Pregnancy.") % line.product_id.name
                    if line.product_id.pregnancy:
                        message += ' ' + line.product_id.pregnancy + '\n'

            if message:
                return {
                    'warning': {
                        'title': _('Pregnancy Warning'),
                        'message': message,
                    }
                }

    def get_prescription_lines(self):
        appointment_id = self.appointment_id and self.appointment_id.id or False
        product_lines = []
        for line in self.old_prescription_id.prescription_line_ids:
            product_lines.append((0,0,{
                'product_id': line.product_id.id,
                'common_dosage_id': line.common_dosage_id and line.common_dosage_id.id or False,
                'dose': line.dose,
                'active_component_ids': [(6, 0, [x.id for x in line.active_component_ids])],
                'form_id' : line.form_id.id,
                'qty_per_day': line.qty_per_day,
                'days': line.days,
                'short_comment': line.short_comment,
                'allow_substitution': line.allow_substitution,
                'appointment_id': appointment_id,
            }))
        self.prescription_line_ids = product_lines

    def action_prescription_send(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('acs_hms', 'acs_prescription_email')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'prescription.order',
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

    # def consume_prescription_medicament(self):
    #     for rec in self:
    #         if not rec.company_id.prescription_usage_location_id:
    #             raise UserError(_('Please define a prescription location where the consumables will be used.'))
    #         if not rec.dep_location.source_location_id:
    #             raise UserError(_('Please define a prescription location from where the consumables will be taken.'))

    #         dest_location_id  = rec.company_id.prescription_usage_location_id.id
    #         source_location_id  = rec.dep_location.source_location_id.id
    #         for line in rec.prescription_line_ids:
    #             verified = self.env['stock.quant'].search(['&','&','&', ('product_id', '=', line.product_id.id),('location_id', '=', rec.dep_location.source_location_id.id),
    #                                                    ('lot_id', '=', line.lot_id.id), ('company_id', '=', line.company_id.id)])
    #             if line.lot_id:
    #                 if verified:
    #                     self.consume_material(source_location_id, dest_location_id,
    #                                           {
    #                                               'product': line.product_id,
    #                                               'lot_id': line.lot_id,
    #                                               'qty': line.quantity,
    #                                               'product_uom': line.product_uom.id,
    #                                           })
    #                 else:
    #                     raise UserError(
    #                         _("Votre département n'a pas de lot %s en sotck", line.lot_id.name))
    #             else:
    #                 pass
    #     self.state = 'deliver'

    def consume_prescription_medicament(self):
        global has_transfert
        has_transfert = False
        stock_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        init_picking_vals = {}

        for rec in self:
            if not rec.company_id.prescription_usage_location_id:
                raise UserError(_('Please define a prescription location where the consumables will be used.'))
            if not rec.dep_location.source_location_id:
                raise UserError(_('Please define a prescription location from where the consumables will be taken.'))

            dest_location_id  = rec.company_id.prescription_usage_location_id.id
            source_location_id  = rec.dep_location.source_location_id.id

            #====PREPARATION TRANSFERT=====
            picking_vals = {
                'partner_id': rec.patient_id.sudo().partner_id.id,
                'location_id': source_location_id,
                'location_dest_id': dest_location_id,
                'picking_type_id': rec.custom_picking_type_id.id,
                'origin': rec.name,
                'company_id': rec.company_id.id,
            }
            init_picking_vals = picking_vals

            for line in rec.prescription_line_ids:
                verified = self.env['stock.quant'].search(['&','&','&', ('product_id', '=', line.product_id.id),('location_id', '=', rec.dep_location.source_location_id.id),
                                                       ('lot_id', '=', line.lot_id.id), ('company_id', '=', line.company_id.id)])
                if line.lot_id:
                    if verified:
                        qte_demande = 0.0
                        qte_disponible = 0.0
                        qte_demande = line.quantity
                        qte_disponible = line.qty_available


                        if qte_disponible < qte_demande or qte_disponible == 0.0:
                            gap = qte_demande - qte_disponible
                            # # Faire une sortie médicaments pour ceux qui sont disponibles en stock
                            receivable = qte_demande - gap
                            #===VERIFICATION SI MVT DEJA EXISTANT
                            verif_mvt = move_obj.search(['&','&','&', ('product_id', '=', line.product_id.id),('location_id', '=', rec.dep_location.source_location_id.id),
                                                       ('product_uom_qty', '=', receivable), ('company_id', '=', line.company_id.id),('origin', '=',rec.name)])
                            if not verif_mvt:
                                self.consume_material(source_location_id, dest_location_id,
                                                  {
                                                      'product': line.product_id,
                                                      'lot_id': line.lot_id,
                                                      'qty': receivable,
                                                      'product_uom': line.product_uom.id,
                                                  })
                                rec.state = 'part_deliver'
                            else:
                                pass
                            has_transfert = True
                        else:
                            verif_mvt2 = move_obj.search(['&', '&', '&', ('product_id', '=', line.product_id.id),
                                                         ('location_id', '=', rec.dep_location.source_location_id.id),
                                                         ('product_uom_qty', '=', line.quantity),
                                                         ('company_id', '=', line.company_id.id),
                                                         ('origin', '=', rec.name)])
                            if not verif_mvt2:
                                self.consume_material(source_location_id, dest_location_id,
                                                       {
                                                           'product': line.product_id,
                                                           'lot_id': line.lot_id,
                                                           'qty': line.quantity,
                                                           'product_uom': line.product_uom.id,
                                                       })
                                rec.state = 'part_deliver'
                            else:
                                pass

                    else:
                        raise UserError(
                            _("Votre département n'a pas de lot %s en sotck", line.lot_id.name))
                else:
                    has_transfert = True
        if has_transfert == True:
            action = {
                'name': 'Confirmation Transfert',
                'type': 'ir.actions.act_window',
                'res_model': 'move.confirmation.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('acs_hms.view_move_confirmation_form').id,
                'target': 'new',
                'context': {
                    'default_picking_vals': init_picking_vals,
                },
            }
            return action
            # self.state = 'part_deliver'
        else:
            self.state = 'deliver'
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Sortie médicament'),
                    'message': 'La sortie des médicaments a été effectué avec succès.',
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
            return notification

        # self.state = 'delivrer'

    def show_picking(self):
        for rec in self:
            res = self.env.ref('stock.action_picking_tree_all')
            res = res.read()[0]
            res['domain'] = str([('origin','=',rec.name)])
        return res

    @api.model
    def _prepare_pick_vals(self, line=False, stock_id=False, gap=False):
        pick_vals = {
            'product_id': line.product_id.id,
            'product_uom_qty': gap,
            'product_uom': line.product_uom.id,
            'location_id': self.dep_location.source_location_id.id,
            'location_dest_id': self.company_id.prescription_usage_location_id.id,
            'name': line.product_id.name,
            'picking_type_id': self.custom_picking_type_id.id,
            'picking_id': stock_id.id,
            'company_id': line.company_id.id,
        }
        return pick_vals

    def generate_service(self):
        self.ensure_one()
        product_line = []
        for line in self.prescription_line_ids:
            vals = {
                'product': line.product_id.id,
                'sale_price': line.product_id.lst_price,
                'name': line.product_id.name,
                'product_uom': line.product_id.uom_id.id,
                'quantity': line.quantity,
            }
            product_line.append((0, 0, vals))
        vals_service = []
        serv_vals = {
            'patient_id': self.patient_id.id,
            #'physician_id': self.physician_id.id,
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
        return True

class ACSPrescriptionLine(models.Model):
    _name = 'prescription.line'
    _description = "Prescription Order Line"

    READONLY_STATES = {'cancel': [('readonly', True)], 'prescription': [('readonly', True)]}

    @api.depends('qty_per_day','days','dose', 'manual_quantity','manual_prescription_qty','state')
    def _get_total_qty(self):
        for rec in self:
            if rec.manual_prescription_qty:
                rec.quantity = rec.manual_quantity
            else:
                rec.quantity = rec.days * rec.qty_per_day * rec.dose

    prescription_id = fields.Many2one('prescription.order', ondelete="cascade", string='Prescription')
    product_id = fields.Many2one('product.product', ondelete="cascade", string='Product', required=True, domain=[('hospital_product_type', '=', 'medicament')])
    allow_substitution = fields.Boolean(string='Allow Substitution')
    prnt = fields.Boolean(string='Print', help='Check this box to print this line of the prescription.',default=True)
    manual_prescription_qty = fields.Boolean(related="product_id.manual_prescription_qty", string="Enter Prescription Qty Manually.", store=True)
    #quantity = fields.Float(string='Units', compute="_get_total_qty", inverse='_inverse_total_qty', compute_sudo=True, store=True, help="Number of units of the medicament. Example : 30 capsules of amoxicillin",default=1.0)
    quantity = fields.Float(string='Units', compute_sudo=True, store=True, help="Number of units of the medicament. Example : 30 capsules of amoxicillin",
                            default=1.0, states=READONLY_STATES)
    manual_quantity = fields.Float(string='Manual Total Qty',states=READONLY_STATES)
    active_component_ids = fields.Many2many('active.comp','product_pres_comp_rel','product_id','pres_id','Active Component',states=READONLY_STATES)
    dose = fields.Float('Dosage', help="Amount of medication (eg, 250 mg) per dose",default=1.0, states=READONLY_STATES)
    form_id = fields.Many2one('drug.form',related='product_id.form_id', string='Form',help='Drug form, such as tablet or gel')
    route_id = fields.Many2one('drug.route', ondelete="cascade", string='Route', help='Drug form, such as tablet or gel')
    common_dosage_id = fields.Many2one('medicament.dosage', ondelete="cascade", string='Dosage/Frequency', help='Drug form, such as tablet or gel')
    short_comment = fields.Char(string='Comment', help='Short comment on the specific drug')
    appointment_id = fields.Many2one('hms.appointment', ondelete="restrict", string='Appointment')
    treatment_id = fields.Many2one('hms.treatment', related='prescription_id.treatment_id', string='Treatment', store=True)
    company_id = fields.Many2one('res.company', ondelete="cascade", string='Hospital', related='prescription_id.company_id')
    #qty_available = fields.Float(related='product_id.qty_available', string='Available Qty')
    days = fields.Float("Days",default=1.0, states=READONLY_STATES)
    qty_per_day = fields.Float(string='Qty Per Day', default=1.0, states=READONLY_STATES)
    state = fields.Selection(related="prescription_id.state", store=True)
    qty_available = fields.Float(string='Available Qty', store=True, states=READONLY_STATES)
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number', ondelete="cascade",
                             domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]")
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True,
                                  domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)

    @api.onchange('product_id')
    def onchange_product(self):
        liste_available = self.env['stock.quant'].search([
            ('product_id', '=', self.product_id.id),
            ('location_id', '=', self.prescription_id.dep_location.source_location_id.id),
        ])
        total_qty = 0
        for liste in liste_available:
            total_qty = liste.available_quantity + total_qty

        if self.product_id:
            self.active_component_ids = [(6, 0, [x.id for x in self.product_id.active_component_ids])]
            self.form_id = self.product_id.form_id and self.product_id.form_id.id or False,
            self.route_id = self.product_id.route_id and self.product_id.route_id.id or False,
            self.quantity = 1
            self.product_uom = self.product_id.uom_id.id
            self.common_dosage_id = self.product_id.common_dosage_id and self.product_id.common_dosage_id.id or False
            self.qty_available = total_qty
            

            if self.prescription_id and self.prescription_id.pregnancy_warning:
                warning = {}
                message = ''
                if self.product_id.pregnancy_warning:
                    message = _("%s Medicine is not Suggastable for Pregnancy.") % self.product_id.name
                    if self.product_id.pregnancy:
                        message += ' ' + self.product_id.pregnancy
                    warning = {
                        'title': _('Pregnancy Warning'),
                        'message': message,
                    }

                if warning:
                    return {'warning': warning}

    @api.onchange('common_dosage_id')
    def onchange_common_dosage(self):
        if self.common_dosage_id:
            self.qty_per_day = self.common_dosage_id.qty_per_day

    @api.onchange('quantity')
    def _inverse_total_qty(self):
        for line in self:
            if line.product_id.manual_prescription_qty:
                line.manual_quantity = line.quantity
            else:
                line.manual_quantity = 0.0

class StockPrescLocation(models.Model):
    _name = 'prescription.location.stock'
    _description = "Emplacement de stock pour prescription"

    name = fields.Char(string='Departement', required=True, translate=True)
    source_location_id = fields.Many2one('stock.location', string='Destination Location')
    company_id = fields.Many2one('res.company', 'Company')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: