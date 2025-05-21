from odoo import models, fields, api


class Teacher(models.Model):
    _name = 'teacher'
    _description = 'Teacher'

    name = fields.Char(string='Name', required=True)
    classe_ids = fields.One2many(
        comodel_name='classe',
        inverse_name='teacher_id',
        string='Classes'
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True
    )
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    active = fields.Boolean(string='Active', default=True)