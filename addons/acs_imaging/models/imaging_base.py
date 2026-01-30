# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression


# class ACSLabTestUom(models.Model):
#     _name = "acs.lab.test.uom"
#     _description = "Lab Test UOM"
#     _order = 'sequence asc'
#     _rec_name = 'code'
#
#     name = fields.Char(string='UOM Name', required=True)
#     code = fields.Char(string='Code', required=True, index=True, help="Short name - code for the test UOM")
#     sequence = fields.Integer("Sequence", default="100")
#
#     _sql_constraints = [('code_uniq', 'unique (name)', 'The Lab Test code must be unique')]


class AcsImaging(models.Model):
    _name = 'acs.imaging'
    _description = 'Imaging Center'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'acs.hms.mixin']
    _inherits = {
        'res.partner': 'partner_id',
    }

    description = fields.Text()
    is_collection_center = fields.Boolean('Is Collection Center')
    partner_id = fields.Many2one('res.partner', 'Partner', ondelete='restrict', required=True)
    source_location_id = fields.Many2one('stock.location', string='Emplacement source')

class ImgSalle(models.Model):
    _name = 'acs.imaging.cabine'
    _description = 'Salle '
    _inherit = ['mail.thread', 'mail.activity.mixin', 'acs.hms.mixin']

    name = fields.Char(string='Salle', required=True)
    test_type = fields.Selection([
        ('CT', 'SCANNER'),
        ('MR', 'IRM'),
        ('exploration', 'EXPLORATION'),
        ('CR', 'RADIOGRAPHIE'),
        ('US', 'ECHOGRAPHIE'),
        ('MG', 'MAMMOGRAPHIE'),
        ('AU', 'ECG'),
        ('radio_int', 'RADIOLOGIE INTERVENTIONNELLE'),
    ], string='Test Type', default='CT')
    company_id = fields.Many2one('res.company', ondelete='restrict',
                                 string='Company', default=lambda self: self.env.user.company_id.id)


class ImagingTest(models.Model):
    _name = "acs.imaging.test"
    _description = "Imaging Test Type"

    name = fields.Char(string='Name', help="Test type, eg X-Ray,biopsy...", index=True)
    code = fields.Char(string='Code', help="Short name - code for the test")
    description = fields.Text(string='Description')
    product_id = fields.Many2one('product.product',string='Service', required=True)
    remark = fields.Char(string='Remark')
    report = fields.Text(string='Test Report')
    company_id = fields.Many2one('res.company', ondelete='restrict', 
        string='Company', default=lambda self: self.env.user.company_id.id)
    
    acs_tat = fields.Char(string='Turnaround Time')
    test_type = fields.Selection([
        ('CT', 'SCANNER'),
        ('MR', 'IRM'),
        ('exploration', 'EXPLORATION'),
        ('CR', 'RADIOGRAPHIE'),
        ('US', 'ECHOGRAPHIE'),
        ('MG', 'MAMMOGRAPHIE'),
        ('AU', 'ECG'),
        ('radio_int', 'RADIOLOGIE INTERVENTIONNELLE'),
    ], string='Test Type', default='CT')

    _sql_constraints = [
        ('code_company_uniq', 'unique (code,company_id)', 'The code of the account must be unique per company !')
    ]

    def name_get(self):
        res = []
        for rec in self:
            name = rec.name
            if rec.code:
                name = "%s [%s]" % (rec.name, rec.code)
            res += [(rec.id, name)]
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)


class ImagingGroupLine(models.Model):
    _name = "imaging.group.line"
    _description = "Imaging Group Line"

    group_id = fields.Many2one('imaging.group', ondelete='restrict', string='Imaging Group')
    test_id = fields.Many2one('acs.imaging.test',string='Test', ondelete='cascade', required=True)
    acs_tat = fields.Char(related='test_id.acs_tat', string='Turnaround Time', readonly=True)
    #instruction = fields.Char(string='Special Instructions')
    instruction = fields.Many2one('imaging.protocol',
                                  string='Protocole',
                                  domain="[('test_id', '=', test_id)]", copy=False)
    sale_price = fields.Float(string='Sale Price')
    test_type = fields.Selection([
        ('CT', 'SCANNER'),
        ('MR', 'IRM'),
        ('exploration', 'EXPLORATION'),
        ('CR', 'RADIOGRAPHIE'),
        ('US', 'ECHOGRAPHIE'),
        ('MG', 'MAMMOGRAPHIE'),
        ('AU', 'ECG'),
        ('radio_int', 'RADIOLOGIE INTERVENTIONNELLE'),
    ], string='Test Type', default='CT')

    @api.onchange('test_id')
    def onchange_test(self):
        if self.test_id:
            self.sale_price = self.test_id.product_id.lst_price


class ImagingGroup(models.Model):
    _name = "imaging.group"
    _description = "Imaging Group"

    name = fields.Char(string='Group Name', required=True)
    line_ids = fields.One2many('imaging.group.line', 'group_id', string='Medicament line')
    test_type = fields.Selection([
        ('CT', 'SCANNER'),
        ('MR', 'IRM'),
        ('exploration', 'EXPLORATION'),
        ('XR', 'RADIOGRAPHIE'),
        ('US', 'ECHOGRAPHIE'),
        ('MG', 'MAMMOGRAPHIE'),
        ('AU', 'ECG'),
        ('radio_int', 'RADIOLOGIE INTERVENTIONNELLE'),
    ], string='Test Type', default='CT')


class ImagingDevice(models.Model):
    _name = "imaging.device"
    _description = "Appareil imagerie"

    name = fields.Char(string='Nom', required=True)
    type = fields.Selection([
        ('automate', 'Automate'),
        ('consommable', 'Consommable'),
    ], string='Type', default='automate')
    first_date = fields.Char('Date de mise en service')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: