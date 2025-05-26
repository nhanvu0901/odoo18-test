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

    # Fix: Change field name from teacher_id to teacher_ids for Many2many
    teacher_ids = fields.Many2many(
        'teacher',
        'teacher_class_rel',  # relation table name
        'class_id',  # column for this model
        'teacher_id',  # column for the other model
        string='Teachers'
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
            if classe.teacher_ids:  # Fix: Change to teacher_ids
                teacher_names = ', '.join(classe.teacher_ids.mapped('name'))
                name += f" - {teacher_names}"
            result.append((classe.id, name))
        return result

    def action_assign_teacher(self):
        """Opens a wizard to assign a teacher to this class."""
        self.ensure_one()
        return {
            'name': 'Assign Teacher to Class',
            'type': 'ir.actions.act_window',
            'res_model': 'classe.assign.teacher.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_classe_id': self.id,
            }
        }

    def action_unassign_teacher(self):
        """Opens a wizard to manage teachers for this class."""
        self.ensure_one()
        return {
            'name': f'Manage Teachers for {self.class_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'teacher',
            'view_mode': 'list,form',
            'domain': [('classe_ids', 'in', [self.id])],
            'context': {
                'default_classe_ids': [(4, self.id)],
            },
            'target': 'current',
        }