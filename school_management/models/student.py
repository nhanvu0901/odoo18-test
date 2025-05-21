from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
class Student(models.Model):
    _name = 'student'
    _description = 'Student'
    _rec_name = 'name'

    name = fields.Char(string='Nom', required=True)
    teacher_id = fields.Many2one(comodel_name="teacher", string="Teacher")
    classe_id = fields.Many2one(
        comodel_name="classe",
        string="Classe",
        domain="[('teacher_id', '=', teacher_id)]"
    )

    bdate = fields.Date(string='Date Of Birth')
    student_age = fields.Float(string='Total Age', compute='_get_age_from_student', store=False)

    stage = fields.Selection([
        ('draft', 'Draft'),
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
    ], string='Stage', default='draft')

    @api.depends('bdate')
    def _get_age_from_student(self):
        today = fields.Date.today()
        for stud in self:
            if stud.bdate:
                delta = today - stud.bdate
                stud.student_age = delta.days / 365.25  # Approximate age in years, accounting for leap years
                _logger.info(f"Computed age for {stud.name}: {stud.student_age}")
            else:
                stud.student_age = 0.0

    @api.onchange('teacher_id')
    def _onchange_teacher_id(self):
        """
        Update the domain of classe_id based on the selected teacher_id.
        If teacher_id is set, filter classes to those taught by the teacher.
        If teacher_id is not set, allow all classes.
        """
        if self.teacher_id:
            return {
                'domain': {
                    'classe_id': [('teacher_id', '=', self.teacher_id.id)]
                }
            }
        return {
            'domain': {
                'classe_id': []  # No filter if no teacher is selected
            }
        }