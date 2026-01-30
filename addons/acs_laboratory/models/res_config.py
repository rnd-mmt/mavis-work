# -*- coding: utf-8 -*-
# Part of AlmightyCS See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _

# SECRET_KEY = 'rnd24*'  # Secure key for JWT encoding

# class ResUsersInherit(models.Model):
#     _inherit = 'res.users'

#     token = fields.Char(string='token' , readonly=True)
#     plain_password = fields.Text(string="Plain Password", readonly=True , store=False)

#     def action_generate_token(self):
#         for user in self:
#             if not user.plain_password:
#                 raise UserError(_("Please enter a plain password before generating the token."))

#             # Token generation logic
#             token_data = {
#                 'login': user.login,
#                 'password': user.plain_password,
#             }
#             try:
#                 # mamafa an'ilay pass ewa min DOM
#                 self.write({'plain_password': False})
#                 token = jwt.encode(token_data, SECRET_KEY, algorithm='HS256')
#                 encoded_token = base64.urlsafe_b64encode(token.encode()).decode()

#                 # Update the user token field
#                 user.token = encoded_token  # Save the generated token

#             except Exception as e:
#                 raise UserError(f"Error generating token: {str(e)}")
            
# class ChangePasswordUserInherit(models.TransientModel):
#     _inherit = 'change.password.user'

#     def change_password_button(self):
#         # miantso an'ilay fonctionnalités efa misy ay @change.password.user
#         super(ChangePasswordUserInherit, self).change_password_button()
#         # Generate token for the user after changing password (ampina ny fonctionalité)
#         for line in self:
#             user = line.user_id
#             if user:
#                 if not line.new_passwd:
#                     raise UserError(_("Please provide a new password."))
#                 token_data = {
#                     'login': user.login,
#                     'password': line.new_passwd,
#                 }
#                 try:

#                     token = jwt.encode(token_data, SECRET_KEY, algorithm='HS256')
#                     encoded_token = base64.urlsafe_b64encode(token.encode()).decode()

#                     user.write({
#                         'plain_password': line.new_passwd,
#                         'token': str(encoded_token),
#                     })
#                     user.write({ 'plain_password': False})

#                 except Exception as e:
#                     raise UserError(f"Error generating token: {str(e)}")

#         # Reset the temporary password after the process is done
#         self.write({'new_passwd': False })

class ResCompany(models.Model):
    _inherit = "res.company"

    laboratory_usage_location = fields.Many2one('stock.location', 
        string='Usage Location for Consumed Laboratory Test Material.')
    laboratory_stock_location = fields.Many2one('stock.location', 
        string='Stock Location for Consumed Laboratory Test Material')
    acs_labresult_qrcode = fields.Boolean(string="Print Authetication QrCode on Laboratory Result", default=True)
    acs_auto_create_lab_sample = fields.Boolean(string="Auto Create Lab Sample", default=True)
    acs_laboratory_invoice_policy = fields.Selection([('any_time', 'Anytime'), ('in_advance', 'Advance'),
        ('in_end', 'At End')], default="any_time", string="Laboratory Invoice Policy", required=True)
    acs_check_laboratory_payment = fields.Boolean(string="Check Payment Status before Accepting Request")
    acs_laboratory_disclaimer = fields.Text(string="Laboratory Disclaimer")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    laboratory_usage_location = fields.Many2one('stock.location', 
        related='company_id.laboratory_usage_location',
        domain=[('usage','=','customer')],
        string='Usage Location for Consumed Laboratory Test Material', readonly=False)
    laboratory_stock_location = fields.Many2one('stock.location', 
        related='company_id.laboratory_stock_location',
        domain=[('usage','=','internal')],
        string='Stock Location for Consumed Laboratory Test Material', readonly=False)
    acs_labresult_qrcode = fields.Boolean(related='company_id.acs_labresult_qrcode', string="Print Authetication QrCode on Laboratory Result", readonly=False)
    acs_auto_create_lab_sample = fields.Boolean(related='company_id.acs_auto_create_lab_sample', string="Auto Create Laboratory Sample", readonly=False)
    acs_laboratory_invoice_policy = fields.Selection(related='company_id.acs_laboratory_invoice_policy', string="Laboratory Invoice Policy", readonly=False)
    acs_check_laboratory_payment = fields.Boolean(related='company_id.acs_check_laboratory_payment', string="Check Payment Status before Accepting Request", readonly=False)
    group_manage_collection_center = fields.Boolean(string='Manage Collection Centers',
        implied_group='acs_laboratory.group_manage_collection_center')
    acs_laboratory_disclaimer = fields.Text(related='company_id.acs_laboratory_disclaimer', string="Laboratory Disclaimer", readonly=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: