# -*- coding: utf-8 -*-
from odoo import http


class DiscussionApi(http.Controller):
    @http.route('/discussion_api/discussion_api/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/discussion_api/discussion_api/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('discussion_api.listing', {
            'root': '/discussion_api/discussion_api',
            'objects': http.request.env['discussion_api.discussion_api'].search([]),
        })

    @http.route('/discussion_api/discussion_api/objects/<model("discussion_api.discussion_api"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('discussion_api.object', {
            'object': obj
        })
