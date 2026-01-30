from odoo import fields, models, api, _

class ResCompany(models.Model):
    _description = "Hospital"
    _inherit = "res.company"

    auth_token = fields.Char('Authentication Token')
    senderName = fields.Char('Sender name',help="This is the name of your mobile app. It is set up in the console when you create the app")
    dev_phone_number = fields.Char('Dev Phone number', help="the developer's phone number which was used when activating sms.")
    overwrite_odoo_sms = fields.Boolean('Overwrite Odoo SMS')
    client_id = fields.Char('Client ID')
    client_secret = fields.Char('Client secret')

# class ResConfigSetting(models.TransientModel):
#     _inherit = 'res.config.settings'

#     # clientID = fields.Char('Account SID')
#     auth_token = fields.Char('Authentication Token')
#     senderName = fields.Char('App Name', help="This is the name of your mobile app. It is set up in the console when you create the app")
#     dev_phone_number = fields.Char('Dev Phone number', help="the developer's phone number which was used when activating sms.")
#     overwrite_odoo_sms = fields.Boolean('Overwrite Odoo SMS')

#     @api.model
#     def get_values(self):
#         res = super(ResConfigSetting, self).get_values()
#         param_obj = self.env['ir.config_parameter']
#         res.update({
#             'dev_phone_number': param_obj.sudo().get_param('ql_scheduler_reminder.dev_phone_number'),
#             'auth_token': param_obj.sudo().get_param('ql_scheduler_reminder.auth_token'),
#             'senderName': param_obj.sudo().get_param('ql_scheduler_reminder.senderName'),
#             'overwrite_odoo_sms': param_obj.sudo().get_param('ql_scheduler_reminder.overrwrite_odoo_sms'),
#         })
#         return res

#     @api.model
#     def set_values(self):
#         super(ResConfigSetting, self).set_values()
#         param_obj = self.env['ir.config_parameter']
#         param_obj.sudo().set_param('ql_scheduler_reminder.dev_phone_number', self.dev_phone_number)
#         param_obj.sudo().set_param('ql_scheduler_reminder.auth_token', self.auth_token)
#         param_obj.sudo().set_param('ql_scheduler_reminder.senderName', self.senderName)
#         param_obj.sudo().set_param('ql_scheduler_reminder.overrwrite_odoo_sms', self.overwrite_odoo_sms)
