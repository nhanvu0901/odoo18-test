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

    # Computed field to show student count in teacher's view
    student_count = fields.Integer(
        string='Students Count',
        compute='_compute_student_count',
        store=True,
        help='Number of students in this class'
    )

    @api.depends('student_ids')
    def _compute_student_count(self):
        """Compute the number of students in the class"""
        for classe in self:
            classe.student_count = len(classe.student_ids)

    @api.constrains('capacity', 'student_ids')
    def check_capacity(self):
        for classe in self:
            if len(classe.student_ids) > classe.capacity:
                raise ValidationError(f"Class {classe.class_name} exceeds capacity of {classe.capacity} students.")

    def name_get(self):
        """Custom name display for better readability"""
        result = []
        for classe in self:
            name = f"{classe.class_name}"
            if classe.room:
                name += f" (Room: {classe.room})"
            if classe.teacher_id:
                name += f" - {classe.teacher_id.name}"
            result.append((classe.id, name))
        return result

    def action_unassign_teacher(self):
        """Unassign teacher from this class."""
        for classe in self:
            classe.teacher_id = False
        return True

    def action_assign_teacher(self):
        """Open wizard to assign a teacher to this class."""
        self.ensure_one()
        return {
            'name': 'Assign Teacher',
            'type': 'ir.actions.act_window',
            'res_model': 'classe.assign.teacher.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_classe_id': self.id,
            }
        }