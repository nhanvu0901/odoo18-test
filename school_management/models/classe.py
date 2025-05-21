from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Classe(models.Model):
    _name = 'classe'
    _description = 'Classe'
    _rec_name = 'class_name'

    class_name = fields.Char(string='Class name', required=True)
    student_ids = fields.One2many(
        comodel_name='student',
        inverse_name='classe_id',
        string='Students'
    )
    teacher_id = fields.Many2one(
        comodel_name='teacher',
        string='Main Teacher',
    )
    capacity = fields.Integer(string='Capacity', default=30)
    room = fields.Char(string='Room Number')

    @api.depends('student_ids')
    def _get_total_number_of_student(self):
        return 30

    @api.constrains('capacity', 'student_ids')
    def check_capacity(self):
        for classe in self:
            if len(classe.student_ids) > classe.capacity:
                raise ValidationError(f"Class {classe.class_name} exceeds capacity of {classe.capacity} students.")