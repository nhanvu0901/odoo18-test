# -*- coding: utf-8 -*-
# from odoo import http


# class CustomHrModule(http.Controller):
#     @http.route('/custom_hr_module/custom_hr_module', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_hr_module/custom_hr_module/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_hr_module.listing', {
#             'root': '/custom_hr_module/custom_hr_module',
#             'objects': http.request.env['custom_hr_module.custom_hr_module'].search([]),
#         })

#     @http.route('/custom_hr_module/custom_hr_module/objects/<model("custom_hr_module.custom_hr_module"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_hr_module.object', {
#             'object': obj
#         })

