from odoo import models, fields, api

class LineCategoryWizard(models.TransientModel):
    _name = 'line.product.category.wizard'
    _description = 'Health Service Line category Wizard'

    line_id = fields.Many2one('service.line.category.wizard', string='ligne de categorie', readonly=True)
    product = fields.Many2one('product.product', string='Product', domain="[('categ_id', 'child_of', category)]")
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product.uom_id.category_id', readonly=True)
    sale_price = fields.Float(string='Sale Price', readonly=True)
    quantity = fields.Float(string='Quantity')
    product_type = fields.Char(string='Type')
    name = fields.Text(string='Description')
    category = fields.Many2one(related='line_id.product_categ_id')
    parent_category = fields.Many2one(related='line_id.product_categ_id.parent_id')
    
    @api.onchange('product')
    def onchange_product(self):
        if self.product:
            self.sale_price = self.product.lst_price
            self.product_type = self.product.hospital_product_type
            self.product_uom = self.product.uom_id.id
            self.name = self.product.name
            self.quantity = 1
                

class ServiceLineCategoryWizard(models.TransientModel):
    _name = 'service.line.category.wizard'
    _description = 'Health Service Line category Wizard'
   
    product_categ_id = fields.Many2one('product.category', 'Product Category',required=True, 
                                    domain="[('is_nomenclature', '=', True)]", help="Select category for the current product")
    product_ids = fields.One2many('line.product.category.wizard', 'line_id', string="Ligne d'article")

    service_id = fields.Many2one('acs.health_service', string='Health Service')


    def add_health_service_article(self):
        """ Add selected products to the health service, grouped by hospital product type """
        context = self.env.context
        service_id = context.get('default_service_id')
        active_record = self.env['acs.health_service'].browse(self._context.get('active_id'))
        global_rdv = False
        global_ot = False
        if service_id:
            if self.product_categ_id:
                section = self.product_categ_id.name.rsplit('/', 1)
                if len(section) == 2:
                    section_value = section[1]
                else:
                    section_value = section[0]
                self.env['acs.health_service.line'].create({
                    'service_id': service_id,
                    'name': section_value,
                    'display_type': 'line_section',
                    })
            for product in self.product_ids:
                if product.product_type in ['consultation', 'surgery', 'radio_int']:
                    global_rdv = True
                if product.product_type in ['surgery', 'radio_int']:
                    global_ot = True
                self.env['acs.health_service.line'].create({
                    'service_id': service_id, 
                    'product': product.product.id,
                    'name': product.name,
                    'product_uom': product.product_uom.id,
                    'sale_price': product.sale_price,
                    'quantity': product.quantity,
                    'product_type': product.product_type,                    
                    })
            if global_rdv is True:
                active_record.show_rdv = True
            if global_ot is True:
                active_record.show_ot = True
        return {'type': 'ir.actions.act_window_close'}
