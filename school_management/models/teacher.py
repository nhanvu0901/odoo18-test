from odoo import models, fields, api


# Existing TeacherCertification and SchoolSubject models remain unchanged
class TeacherCertification(models.Model):
    _name = 'teacher.certification'
    _description = 'Teacher Certification'

    name = fields.Char(string='Certification Name', required=True)
    issuing_organization = fields.Char(string='Issuing Organization')
    issue_date = fields.Date(string='Issue Date')
    expiry_date = fields.Date(string='Expiry Date')
    certification_number = fields.Char(string='Certification Number')
    teacher_id = fields.Many2one('teacher', string='Teacher')


class SchoolSubject(models.Model):
    _name = 'school.subject'
    _description = 'School Subject'

    name = fields.Char(string='Subject Name', required=True)
    code = fields.Char(string='Subject Code')
    description = fields.Text(string='Description')
    grade_level = fields.Selection([
        ('elementary', 'Elementary'),
        ('middle', 'Middle School'),
        ('high', 'High School'),
        ('all', 'All Levels')
    ], string='Grade Level', default='all')


class Teacher(models.Model):
    _name = 'teacher'
    _inherits = {'hr.employee': 'employee_id'}
    _description = 'Teacher'
    _sql_constraints = [
        ('unique_employee_id', 'UNIQUE(employee_id)',
         'An employee can only be linked to one teacher record!')
    ]

    # Inherited fields (name is part of hr.employee)
    # phone and email are related from hr.employee
    phone = fields.Char(related='employee_id.phone', readonly=False, store=True)
    email = fields.Char(related='employee_id.email', readonly=False, store=True)

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        help='Employee linked to this teacher'
    )

    classe_ids = fields.Many2many(
        'classe',
        'teacher_class_rel',  # relation table name
        'teacher_id',  # column for this model
        'class_id',  # column for the other model
        string='Classes'
    )

    qualification = fields.Char(string='Qualification')
    years_of_experience = fields.Integer(string='Years of Experience')
    subject_ids = fields.Many2many(
        comodel_name='school.subject',
        relation='teacher_subject_rel',
        column1='teacher_id',
        column2='subject_id',
        string='Subjects Taught'
    )

    academic_degree = fields.Selection([
        ('bachelor', 'Bachelor'),
        ('master', 'Master'),
        ('phd', 'PhD'),
        ('other', 'Other')
    ], string='Academic Degree')

    certification_ids = fields.One2many(
        'teacher.certification',
        'teacher_id',
        string='Certifications'
    )

    # Computed field for class count
    classes_count = fields.Integer(
        string='Classes Count',
        compute='_compute_classes_count'
    )

    @api.depends('classe_ids')
    def _compute_classes_count(self):
        """Compute the number of classes assigned to teacher"""
        for teacher in self:
            teacher.classes_count = len(teacher.classe_ids)

    @api.model
    def create(self, vals):
        # Ensure 'job_id' for 'Teacher' is set if not provided
        if not vals.get('job_id'):
            teacher_job = self.env['hr.job'].search([('name', '=', 'Teacher')], limit=1)
            if not teacher_job:
                teacher_job = self.env['hr.job'].create({
                    'name': 'Teacher',
                    'description': 'School Teacher',
                })
            vals['job_id'] = teacher_job.id

        teacher = super(Teacher, self).create(vals)
        if teacher.employee_id:
            teacher.employee_id.update_teacher_fields()
        return teacher

    def _get_current_teacher(self):
        """Get the teacher record for the current user"""
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if employee:
            teacher = self.search([('employee_id', '=', employee.id)], limit=1)
            return teacher
        return False

    def write(self, vals):
        old_employees = self.env['hr.employee']
        if 'employee_id' in vals:
            old_employees = self.mapped('employee_id')

        res = super(Teacher, self).write(vals)

        if 'employee_id' in vals:
            if old_employees:
                old_employees.update_teacher_fields()
            current_employees = self.mapped('employee_id')
            if current_employees:
                current_employees.update_teacher_fields()
        elif self.mapped('employee_id'):
            self.mapped('employee_id').update_teacher_fields()
        return res

    def unlink(self):
        employees_to_update = self.mapped('employee_id')
        res = super(Teacher, self).unlink()
        if employees_to_update:
            employees_to_update.update_teacher_fields()
        return res

    def action_assign_classes(self):
        """Opens a wizard to assign existing classes to this teacher."""
        self.ensure_one()
        return {
            'name': 'Assign Classes',
            'type': 'ir.actions.act_window',
            'res_model': 'teacher.assign.class.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_teacher_id': self.id,
            }
        }

    def action_view_assigned_classes(self):
        """Opens a view showing all classes assigned to this teacher."""
        self.ensure_one()
        return {
            'name': f'Classes for {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'classe',
            'view_mode': 'list,form',
            'domain': [('teacher_ids', 'in', [self.id])],  # Now this matches the field name
            'context': {
                'default_teacher_ids': [(4, self.id)],
            },
            'target': 'current',
        }

    def action_unassign_all_classes(self):
        """Unassign all classes from this teacher."""
        self.ensure_one()
        # Update to use Many2many commands
        for classe in self.classe_ids:
            classe.teacher_ids = [(3, self.id)]  # Unlink this teacher from each class
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


# Simplified Wizard Model for Assigning Classes
class TeacherAssignClassWizard(models.TransientModel):
    _name = 'teacher.assign.class.wizard'
    _description = 'Wizard to Assign Classes to a Teacher'

    teacher_id = fields.Many2one(
        'teacher',
        string="Teacher",
        required=True,
        readonly=True,
        default=lambda self: self.env.context.get('default_teacher_id')
    )

    # Add a field to show currently assigned classes
    current_class_ids = fields.Many2many(
        'classe',
        string="Currently Assigned Classes",
        related='teacher_id.classe_ids',
        readonly=True
    )

    # This field will be for all available classes
    class_ids = fields.Many2many(
        'classe',
        relation='wizard_class_assign_rel',  # Specify a custom relation to avoid conflicts
        column1='wizard_id',
        column2='class_id',
        string="Classes to Assign"
    )

    @api.model
    def default_get(self, fields_list):
        result = super(TeacherAssignClassWizard, self).default_get(fields_list)
        if 'class_ids' in fields_list:
            # Get ALL classes using sudo
            all_classes = self.env['classe'].sudo().search([])
            result['class_ids'] = [(6, 0, all_classes.ids)]
        return result

    def action_confirm_assignment(self):
        """Assigns the selected classes to the teacher."""
        self.ensure_one()
        if self.class_ids:
            # Use a clean write to replace all assignments
            self.teacher_id.sudo().write({
                'classe_ids': [(6, 0, self.class_ids.ids)]
            })
        return {'type': 'ir.actions.act_window_close'}


class ClasseAssignTeacherWizard(models.TransientModel):
    _name = 'classe.assign.teacher.wizard'
    _description = 'Wizard to Assign Teacher to a Class'

    classe_id = fields.Many2one(
        'classe',
        string="Class",
        required=True,
        readonly=True,
        default=lambda self: self.env.context.get('default_classe_id')
    )

    teacher_id = fields.Many2one(
        'teacher',
        string="Teacher",
        required=True
    )

    current_teacher_ids = fields.Many2many(
        'teacher',
        string="Current Teachers",
        related='classe_id.teacher_ids',
        readonly=True
    )

    def action_confirm_assignment(self):
        """Assigns the selected teacher to the class."""
        self.ensure_one()
        # Add teacher to the class using Many2many command
        self.classe_id.teacher_ids = [(4, self.teacher_id.id)]
        return {'type': 'ir.actions.act_window_close'}
