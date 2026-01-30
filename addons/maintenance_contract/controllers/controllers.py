# -*- coding: utf-8 -*-
# from odoo import http


# class MaintenanceContract(http.Controller):
#     @http.route('/maintenance_contract/maintenance_contract/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/maintenance_contract/maintenance_contract/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('maintenance_contract.listing', {
#             'root': '/maintenance_contract/maintenance_contract',
#             'objects': http.request.env['maintenance_contract.maintenance_contract'].search([]),
#         })

#     @http.route('/maintenance_contract/maintenance_contract/objects/<model("maintenance_contract.maintenance_contract"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('maintenance_contract.object', {
#             'object': obj
#         })
