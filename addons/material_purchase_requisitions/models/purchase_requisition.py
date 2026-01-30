# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import Warning, UserError

class MaterialPurchaseRequisition(models.Model):
    _name = 'material.purchase.requisition'
    _description = 'Purchase Requisition'
    #_inherit = ['mail.thread', 'ir.needaction_mixin']
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']      # odoo11
    _order = 'id desc'
    
    #@api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel', 'reject'):
                raise UserError(_('You can not delete Purchase Requisition which is not in draft or cancelled or rejected state.'))
#                raise Warning(_('You can not delete Purchase Requisition which is not in draft or cancelled or rejected state.'))
        return super(MaterialPurchaseRequisition, self).unlink()
    
    name = fields.Char(string='Number',index=True,readonly=1)
    state = fields.Selection([
        ('draft', 'Nouveau'),
        ('dept_confirm', "Attente validation responsable"),
        ('ir_approve', 'Attente validation RAF'),
        ('approve', 'Validé'),
        ('stock', 'Bon de commande créé'),
        ('receive', 'Articles reçus'),
        ('cancel', 'Annulé'),
        ('reject', 'Refusé')],
        default='draft',
        track_visibility='onchange',
    )
    request_date = fields.Date(string='Date de la demande', default=fields.Date.today(), required=True)
    department_id = fields.Many2one('hr.department', string='Département', required=True, copy=True)
    employee_id = fields.Many2one('hr.employee', string='Employé',
        default=lambda self: self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1),
        required=True, readonly=True, copy=True)
    approve_manager_id = fields.Many2one('hr.employee', string='Responsable de département', readonly=True, copy=False)
    reject_manager_id = fields.Many2one('hr.employee', string='Department Manager Reject', readonly=True)
    approve_employee_id = fields.Many2one('hr.employee', string='Approuvé par', readonly=True, copy=False)
    reject_employee_id = fields.Many2one('hr.employee', string='Refusé par', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.user.company_id, required=True, copy=True)
    location_id = fields.Many2one('stock.location', string='Source Location', copy=True)
    requisition_line_ids = fields.One2many('material.purchase.requisition.line', 'requisition_id', string='Purchase Requisitions Line', copy=True)
    date_end = fields.Date(string='Date limite de la demande', readonly=True, help='Last date for the product to be needed', copy=True)
    date_done = fields.Date(string='Date effective', readonly=True, help="Date de finalisation de la demande d'achat")
    managerapp_date = fields.Date(string="Date d'approbation du département",readonly=True,copy=False)
    manareject_date = fields.Date(string='Date de refus du responsable', readonly=True, help="Date de refus du responsable de département")
    userreject_date = fields.Date(string='Refusé le', readonly=True, copy=False)
    userrapp_date = fields.Date(string='Approuvé le', readonly=True, copy=False)
    receive_date = fields.Date(string='Reçu le', readonly=True, copy=False)
    reason = fields.Text(string='Motif de la demande', required=False, copy=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Compte analytique', copy=True)
    dest_location_id = fields.Many2one('stock.location', string='Emplacement de destination', required=False, copy=True)
    delivery_picking_id = fields.Many2one('stock.picking', string='Internal Picking', readonly=True, copy=False)
    requisiton_responsible_id = fields.Many2one('hr.employee', string='Responsable de la demande', copy=True)
    employee_confirm_id = fields.Many2one('hr.employee', string='Confirmé par', readonly=True, copy=False)
    confirm_date = fields.Date(string='Confirmé le', readonly=True, copy=False)
    
    purchase_order_ids = fields.One2many('purchase.order', 'custom_requisition_id', string='Bons de commande')
    custom_picking_type_id = fields.Many2one('stock.picking.type', string='Type de prélèvement', copy=False)
    
    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('purchase.requisition.seq')
        vals.update({
            'name': name
            })
        res = super(MaterialPurchaseRequisition, self).create(vals)
        return res
        
    #@api.multi
    def requisition_confirm(self):
        for rec in self:
            # manager_mail_template = self.env.ref('material_purchase_requisitions.email_confirm_material_purchase_requistion')
            #rec.employee_confirm_id = rec.employee_id.
            rec.employee_confirm_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.confirm_date = fields.Date.today()
            rec.state = 'dept_confirm'
            # if manager_mail_template:
            #     manager_mail_template.send_mail(self.id)
            
    #@api.multi
    def requisition_reject(self):
        for rec in self:
            rec.state = 'reject'
            rec.reject_employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.userreject_date = fields.Date.today()

    #@api.multi
    def manager_approve(self):
        if self.requisiton_responsible_id == self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1):
            for rec in self:
                rec.managerapp_date = fields.Date.today()
                rec.approve_manager_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
                employee_mail_template = self.env.ref('material_purchase_requisitions.email_purchase_requisition_iruser_custom')
                email_iruser_template = self.env.ref('material_purchase_requisitions.email_purchase_requisition')
                employee_mail_template.sudo().send_mail(self.id)
                email_iruser_template.sudo().send_mail(self.id)
                rec.state = 'ir_approve'
        else:
            raise UserError(_("Vous n'êtes pas autorisé à faire cette action"))

    #@api.multi
    def user_approve(self):
        for rec in self:
            rec.userrapp_date = fields.Date.today()
            rec.approve_employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.state = 'approve'

    #@api.multi
    def reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.model
    def _prepare_pick_vals(self, line=False, stock_id=False):
        pick_vals = {
            'product_id' : line.product_id.id,
            'product_uom_qty' : line.qty,
            'product_uom' : line.uom.id,
            'location_id' : self.location_id.id,
            'location_dest_id' : self.dest_location_id.id,
            'name' : line.product_id.name,
            'picking_type_id' : self.custom_picking_type_id.id,
            'picking_id' : stock_id.id,
            'custom_requisition_line_id' : line.id,
            'company_id' : line.requisition_id.company_id.id,
        }
        return pick_vals

    @api.model
    def _prepare_po_line(self, line=False, purchase_order=False):
        po_line_vals = {
                 'product_id': line.product_id.id,
                 'name':line.product_id.name,
                 'product_qty': line.qty,
                 'product_uom': line.uom.id,
                 'date_planned': fields.Date.today(),
                 'price_unit': line.product_id.standard_price,
                 'order_id': purchase_order.id,
                 'account_analytic_id': self.analytic_account_id.id,
                 'custom_requisition_line_id': line.id
        }
        return po_line_vals
    
    #@api.multi
    def request_stock(self):
        stock_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        #internal_obj = self.env['stock.picking.type'].search([('code','=', 'internal')], limit=1)
        #internal_obj = self.env['stock.location'].search([('usage','=', 'internal')], limit=1)
        purchase_obj = self.env['purchase.order']
        purchase_line_obj = self.env['purchase.order.line']
#         if not internal_obj:
#             raise UserError(_('Please Specified Internal Picking Type.'))
        for rec in self:
            if not rec.requisition_line_ids:
#                raise Warning(_('Please create some requisition lines.'))
                raise UserError(_('Please create some requisition lines.'))
            if any(line.requisition_type =='internal' for line in rec.requisition_line_ids):
                if not rec.location_id.id:
#                        raise Warning(_('Select Source location under the picking details.'))
                    raise UserError(_('Select Source location under the picking details.'))
                if not rec.custom_picking_type_id.id:
#                        raise Warning(_('Select Picking Type under the picking details.'))
                    raise UserError(_('Select Picking Type under the picking details.'))
                if not rec.dest_location_id:
#                    raise Warning(_('Select Destination location under the picking details.'))
                    raise UserError(_('Select Destination location under the picking details.'))
#                 if not rec.employee_id.dest_location_id.id or not rec.employee_id.department_id.dest_location_id.id:
#                     raise Warning(_('Select Destination location under the picking details.'))
                picking_vals = {
                        'partner_id' : rec.employee_id.sudo().address_home_id.id,
                        #'min_date' : fields.Date.today(),
                        'location_id' : rec.location_id.id,
                        'location_dest_id' : rec.dest_location_id and rec.dest_location_id.id or rec.employee_id.dest_location_id.id or rec.employee_id.department_id.dest_location_id.id,
                        'picking_type_id' : rec.custom_picking_type_id.id,#internal_obj.id,
                        'note' : rec.reason,
                        'custom_requisition_id' : rec.id,
                        'origin' : rec.name,
                        'company_id' : rec.company_id.id,
                        
                    }
                stock_id = stock_obj.sudo().create(picking_vals)
                delivery_vals = {
                        'delivery_picking_id' : stock_id.id,
                    }
                rec.write(delivery_vals)
                
            po_dict = {}
            for line in rec.requisition_line_ids:
                if line.requisition_type =='internal':
                    pick_vals = rec._prepare_pick_vals(line, stock_id)
                    move_id = move_obj.sudo().create(pick_vals)
                #else:
                if line.requisition_type == 'purchase': #10/12/2019
                    if not line.partner_id:
                        raise UserError(_('Please enter atleast one vendor on Requisition Lines for Requisition Action Purchase'))
#                        raise Warning(_('Please enter atleast one vendor on Requisition Lines for Requisition Action Purchase'))
                    for partner in line.partner_id:
                        if partner not in po_dict:
                            po_vals = {
                                'partner_id':partner.id,
                                'currency_id':rec.env.user.company_id.currency_id.id,
                                'date_order':fields.Date.today(),
#                                'company_id':rec.env.user.company_id.id,
                                'company_id':rec.company_id.id,
                                'custom_requisition_id':rec.id,
                                'origin': rec.name,
                            }
                            purchase_order = purchase_obj.create(po_vals)
                            po_dict.update({partner:purchase_order})
                            po_line_vals = rec._prepare_po_line(line, purchase_order)
#                            {
#                                     'product_id': line.product_id.id,
#                                     'name':line.product_id.name,
#                                     'product_qty': line.qty,
#                                     'product_uom': line.uom.id,
#                                     'date_planned': fields.Date.today(),
#                                     'price_unit': line.product_id.lst_price,
#                                     'order_id': purchase_order.id,
#                                     'account_analytic_id': rec.analytic_account_id.id,
#                            }
                            purchase_line_obj.sudo().create(po_line_vals)
                        else:
                            purchase_order = po_dict.get(partner)
                            po_line_vals = rec._prepare_po_line(line, purchase_order)
#                            po_line_vals =  {
#                                 'product_id': line.product_id.id,
#                                 'name':line.product_id.name,
#                                 'product_qty': line.qty,
#                                 'product_uom': line.uom.id,
#                                 'date_planned': fields.Date.today(),
#                                 'price_unit': line.product_id.lst_price,
#                                 'order_id': purchase_order.id,
#                                 'account_analytic_id': rec.analytic_account_id.id,
#                            }
                            purchase_line_obj.sudo().create(po_line_vals)
                rec.state = 'stock'
    
    #@api.multi
    def action_received(self):
        for rec in self:
            rec.receive_date = fields.Date.today()
            rec.state = 'receive'
    
    #@api.multi
    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
    
    @api.onchange('employee_id')
    def set_department(self):
        for rec in self:
            rec.department_id = rec.employee_id.sudo().department_id.id
            rec.requisiton_responsible_id = rec.employee_id.sudo().parent_id.id or False
            rec.dest_location_id = rec.employee_id.sudo().dest_location_id.id or rec.employee_id.sudo().department_id.dest_location_id.id 

    #@api.multi
    def show_picking(self):
        for rec in self:
            res = self.env.ref('stock.action_picking_tree_all')
            res = res.read()[0]
            res['domain'] = str([('custom_requisition_id','=',rec.id)])
        return res
        
    #@api.multi
    def action_show_po(self):
        for rec in self:
            purchase_action = self.env.ref('purchase.purchase_rfq')
            purchase_action = purchase_action.read()[0]
            purchase_action['domain'] = str([('custom_requisition_id','=',rec.id)])
        return purchase_action
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
