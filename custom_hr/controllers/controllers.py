# -*- coding: utf-8 -*-
# from odoo import http


# class CustomHr(http.Controller):
#     @http.route('/custom_hr/custom_hr', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_hr/custom_hr/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_hr.listing', {
#             'root': '/custom_hr/custom_hr',
#             'objects': http.request.env['custom_hr.custom_hr'].search([]),
#         })

#     @http.route('/custom_hr/custom_hr/objects/<model("custom_hr.custom_hr"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_hr.object', {
#             'object': obj
#         })

