from odoo import api, fields, models, _
class MoveConfirmationLine(models.TransientModel):
    _name = 'move.confirmation.line'
    _description = 'Move Confirmation Line'

    wizard_id = fields.Many2one('move.confirmation.wizard', string='Confirmation')
    line_id = fields.One2many('stock.move.line', 'picking_id', 'Operations')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom_qty = fields.Float(string='Quantity')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True,
                                  domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)

class MoveConfirmationWizard(models.TransientModel):
    _name = 'move.confirmation.wizard'
    _inherit = ['acs.hms.mixin']
    _description = 'Move Confirmation'

    line_ids = fields.One2many('move.confirmation.line', 'wizard_id', string='Move Lines')
    location_id = fields.Integer(string="Source Location")
    location_dest_id = fields.Integer(string="Destination Location")
    picking_type_id = fields.Integer(string="Type de transfert")

    @api.model
    def default_get(self, fields):
        default_values = super(MoveConfirmationWizard, self).default_get(fields)
        active_model = self._context.get('active_model')
        if active_model == 'prescription.order':
            active_record = self.env['prescription.order'].browse(self._context.get('active_id'))
            lines = []
            for line in active_record.prescription_line_ids:
                qte_demande = line.quantity
                qte_disponible = line.qty_available
                if qte_disponible < qte_demande or qte_disponible == 0.0:
                    gap = qte_demande - qte_disponible
                    lines.append((0, 0, {
                        'wizard_id': self.id,
                        'product_id': line.product_id and line.product_id.id or False,
                        'product_uom_qty': gap,
                        'product_uom': line.product_uom.id,
                    }))
                elif not line.lot_id:
                    lines.append((0, 0, {
                        'wizard_id': self.id,
                        'product_id': line.product_id and line.product_id.id or False,
                        'product_uom_qty': line.quantity,
                        'product_uom': line.product_uom.id,
                    }))
            default_values.update({
                'line_ids': lines,
                'location_id': active_record.dep_location.source_location_id.id,
                'location_dest_id': active_record.company_id.prescription_usage_location_id.id,
                'picking_type_id': active_record.custom_picking_type_id.id
            })
        return default_values
    def confirm_moves(self):
        move_obj = self.env['stock.move']
        stock_obj = self.env['stock.picking']
        global confirmation_done
        confirmation_done = False

        init_pick_vals = self.env.context.get('default_picking_vals', {})
        picking = stock_obj.sudo().create(init_pick_vals)

        for move_line in self.line_ids:
            move_line_vals = {
                'name': move_line.product_id.name,
                'product_id': move_line.product_id.id,
                'product_uom': move_line.product_id.uom_id.id,
                'product_uom_qty': move_line.product_uom_qty,
                'location_id': self.location_id,
                'location_dest_id': self.location_dest_id,
                'picking_type_id': self.picking_type_id,
                'picking_id': picking.id,
            }
            move_id = move_obj.sudo().create(move_line_vals)
            confirmation_done = True

        active_model = self._context.get('active_model')
        if active_model == 'prescription.order':
            active_record = self.env['prescription.order'].browse(self._context.get('active_id'))
            if confirmation_done:
                active_record.state = 'part_deliver'








