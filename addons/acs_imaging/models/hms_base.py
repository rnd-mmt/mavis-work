# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    img_request_id = fields.Many2one('acs.imaging.request', string='Imaging Request', copy=False, ondelete='restrict')
    hospital_invoice_type = fields.Selection(selection_add=[('imaging', 'Imaging')])


# class StockMove(models.Model):
#     _inherit = "stock.move"
#
#     lab_test_id = fields.Many2one('patient.imaging.test', string="Imaging Test", ondelete="restrict")


# class ACSConsumableLine(models.Model):
#     _inherit = "hms.consumable.line"
#
#     patient_imaging_test_id = fields.Many2one('patient.imaging.test', string="Patient Imaging Test", ondelete="restrict")
#     Imaging_test_id = fields.Many2one('acs.imaging.test', string="Imaging Test", ondelete="restrict")

class StockMove(models.Model):
     _inherit = "stock.move"

     img_test_id = fields.Many2one('patient.imaging.test', string="Imaging Test", ondelete="restrict")

class IMGConsumableLine(models.Model):
    _name = 'imaging.consumable.line'
    _description = "Imaging Consumable Line"

    imaging_id = fields.Many2one('patient.imaging.test', string="Patient Imaging Test", ondelete="restrict")
    product_id = fields.Many2one('product.product', ondelete="cascade", string='Produit', required=True, domain=[('type', '=', 'product')])
    quantity = fields.Float(string='Qté', default=1.0)
    company_id = fields.Many2one('res.company', ondelete="cascade", string='Hospital', related='imaging_id.company_id')
    qty_available = fields.Float(string='Available Qty', store=True)
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number', ondelete="cascade",
                             # domain=lambda self: [('id', 'in', self.get_list_lot().ids)])
                             domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]")
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True,
                                  domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)

    @api.onchange('product_id')
    def onchange_product(self):
        liste_available = self.env['stock.quant'].search([
            ('product_id', '=', self.product_id.id),
            ('location_id', '=', self.imaging_id.collection_center_id.source_location_id.id),
        ])
        total_qty = 0
        for liste in liste_available:
            total_qty = + liste.available_quantity

        if self.product_id:
            self.quantity = 1
            self.product_uom = self.product_id.uom_id.id
            self.qty_available = total_qty

    @api.onchange('lot_id')
    def onchange_lot_id(self):
        if self.lot_id:
            self.product_id = self.lot_id.product_id.id
            self.quantity = 1
            self.product_uom = self.product_id.uom_id.id


class ACSPatient(models.Model):
    _inherit = "hms.patient"

    def _rec_count(self):
        rec = super(ACSPatient, self)._rec_count()
        for rec in self:
            rec.img_request_count = len(rec.img_request_ids)
            rec.img_test_count = len(rec.img_test_ids)

    def _acs_get_attachemnts(self):
        attachments = super(ACSPatient, self)._acs_get_attachemnts()
        attachments += self.test_ids.mapped('attachment_ids')
        return attachments

    img_request_ids = fields.One2many('acs.imaging.request', 'patient_id', string='Imaging Requests')
    img_test_ids = fields.One2many('patient.imaging.test', 'patient_id', string='Tests')
    img_request_count = fields.Integer(compute='_rec_count', string='# Imaging Requests')
    img_test_count = fields.Integer(compute='_rec_count', string='# Imaging Tests')

    def action_imaging_requests(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.hms_action_imaging_test_request")
        action['domain'] = [('id','in',self.img_request_ids.ids)]
        action['context'] = {'default_patient_id': self.id}
        return action

    def action_view_img_test_results(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.action_imaging_result")
        action['domain'] = [('id','in',self.img_test_ids.ids)]
        action['context'] = {'default_patient_id': self.id}
        return action

class product_template(models.Model):
    _inherit = "product.template"

    # hospital_product_type = fields.Selection(selection_add=[('scanner', 'SCANNER'), ('echo', 'ECHOGRAPHIE'), ('irm', 'IRM'), ('radio_img', 'RADIOGRAPHIE'), ('exploration', 'EXPLORATION')])
    hospital_product_type = fields.Selection(selection_add=[('CT', 'SCANNER'),
                                                            ('US', 'ECHOGRAPHIE'),
                                                            ('MR', 'IRM'),
                                                            ('CR', 'RADIOGRAPHIE'),
                                                            ('MG', 'MAMMOGRAPHIE'),
                                                            ('AU', 'ECG'),
                                                            ('XA', 'CATLAB'),
                                                            ('exploration', 'EXPLORATION')])


class Physician(models.Model):
    _inherit = "hms.physician"

    def _rec_count_img(self):
        Imagingrequest = self.env['acs.imaging.request']
        Imagingresult = self.env['patient.imaging.test']
        for record in self.with_context(active_test=False):
            record.Imaging_request_count = Imagingrequest.search_count([('physician_id', '=', record.id)])
            record.Imaging_result_count = Imagingresult.search_count([('physician_id', '=', record.id)])

    Imaging_request_count = fields.Integer(compute='_rec_count_img', string='# Imaging Request')
    Imaging_result_count = fields.Integer(compute='_rec_count_img', string='# Imaging Result')

    def action_imaging_request(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.hms_action_imaging_test_request")
        action['domain'] = [('physician_id','=',self.id)]
        action['context'] = {'default_physician_id': self.id}
        return action

    def action_imaging_result(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_imaging.action_imaging_result")
        action['domain'] = [('physician_id','=',self.id)]
        action['context'] = {'default_physician_id': self.id}
        return action

#ACS Note : Option to configure the Collection center in user and set directly in lab request in version 15
# class ResUsers(models.Model):
#     _inherit = "res.users"

#     collection_center_id = fields.Many2one('acs.laboratory', 
#         string='Collection Center')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
