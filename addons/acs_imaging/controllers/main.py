# -*- coding: utf-8 -*-

from odoo import http, fields, _
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo import fields as odoo_fields, http, tools, _, SUPERUSER_ID
import base64

class ACSHms(http.Controller):

    @http.route(['/validate/patientimagingtest/<imagingresult_unique_code>'], type='http', auth="public", website=True)
    def imagingresult_details(self, imagingresult_unique_code, **post):
        if imagingresult_unique_code:
            imagingresult = request.env['patient.imaging.test'].sudo().search([('unique_code','=',imagingresult_unique_code)], limit=1)
            if imagingresult:
                return request.render("acs_imaging.acs_imagingresult_details", {'imagingresult': imagingresult})
        return request.render("acs_hms.acs_no_details")


class HMSPortal(CustomerPortal):
    def _prepare_portal_layout_values(self):
        values = super(HMSPortal, self)._prepare_portal_layout_values()
        imaging_result_count = 0
        if request.env['patient.imaging.test'].check_access_rights('read', raise_exception=False):
            imaging_result_count = request.env['patient.imaging.test'].search_count([])

        imaging_request_count = 0
        if request.env['acs.imaging.request'].check_access_rights('read', raise_exception=False):
            imaging_request_count = request.env['acs.imaging.request'].search_count([])
        values.update({
            'imaging_result_count': imaging_result_count,
            'imaging_request_count': imaging_request_count,
        })
        return values

    #Imaging Result
    @http.route(['/my/imaging_results', '/my/imaging_results/page/<int:page>'], type='http', auth="user", website=True)
    def my_imaging_results(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        if not sortby:
            sortby = 'date'

        sortings = {
            'date': {'label': _('Newest'), 'order': 'date_analysis desc'},
            'name': {'label': _('Name'), 'order': 'name'},
        }

        order = sortings.get(sortby, sortings['date'])['order']
 
        pager = portal_pager(
            url="/my/imaging_results",
            url_args={},
            total=values['imaging_result_count'],
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected

        imaging_results = request.env['patient.imaging.test'].search([],
            order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'sortings': sortings,
            'sortby': sortby,
            'imaging_results': imaging_results,
            'page_name': 'imaging_result',
            'default_url': '/my/imaging_results',
            'searchbar_sortings': sortings,
            'pager': pager
        })
        return request.render("acs_imaging.imaging_results", values)

    @http.route(['/my/imaging_results/<int:result_id>'], type='http', auth="user", website=True)
    def my_imaging_test_result(self, result_id=None, access_token=None, **kw):
        try:
            order_sudo = self._document_check_access('patient.imaging.test', result_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        return request.render("acs_imaging.my_imaging_test_result", {'imaging_result': order_sudo})

    #Imaging Request
    @http.route(['/my/imaging_requests', '/my/imaging_requests/page/<int:page>'], type='http', auth="user", website=True)
    def my_imaging_requests(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        if not sortby:
            sortby = 'date'

        sortings = {
            'date': {'label': _('Newest'), 'order': 'date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
        }

        order = sortings.get(sortby, sortings['date'])['order']
 
        pager = portal_pager(
            url="/my/imaging_requests",
            url_args={},
            total=values['imaging_request_count'],
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        imaging_requests = request.env['acs.imaging.request'].search([],
            order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'sortings': sortings,
            'sortby': sortby,
            'imaging_requests': imaging_requests,
            'page_name': 'lab_request',
            'default_url': '/my/imaging_requests',
            'searchbar_sortings': sortings,
            'pager': pager
        })
        return request.render("acs_imaging.imaging_requests", values)

    @http.route(['/my/imaging_requests/<int:request_id>'], type='http', auth="user", website=True)
    def my_imaging_test_request(self, request_id=None, access_token=None, **kw):
        try:
            order_sudo = self._document_check_access('acs.imaging.request', request_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        return request.render("acs_imaging.my_imaging_test_request", {'imaging_request': order_sudo})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: