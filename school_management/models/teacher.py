from odoo import models, fields, api


class Teacher(models.Model):
    _name = 'teacher'
    _inherits = {'hr.employee': 'employee_id'}  # Change from _inherit to _inherits
    _description = 'Teacher'
    phone = fields.Char(related='employee_id.phone', readonly=False, store=True)
    email = fields.Char(related='employee_id.email', readonly=False, store=True)
    # Reference to hr.employee model
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        help='Employee linked to this teacher'
    )

    # Existing fields that don't overlap with hr.employee
    classe_ids = fields.One2many(
        comodel_name='classe',
        inverse_name='teacher_id',
        string='Classes'
    )

    # New teacher-specific fields
    qualification = fields.Char(string='Qualification')
    years_of_experience = fields.Integer(string='Years of Experience')
    subject_ids = fields.Many2many(
        comodel_name='school.subject',
        relation='teacher_subject_rel',  # Explicit relation table name
        column1='teacher_id',
        column2='subject_id',
        string='Subjects Taught'
    )

    # Academic fields
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

    # Override create to set default job position to 'Teacher' if not specified
    @api.model
    def create(self, vals):
        # Find or create the 'Teacher' job position
        if not vals.get('job_id'):
            teacher_job = self.env['hr.job'].search([('name', '=', 'Teacher')], limit=1)
            if not teacher_job:
                teacher_job = self.env['hr.job'].create({
                    'name': 'Teacher',
                    'description': 'School Teacher',
                })
            vals['job_id'] = teacher_job.id

        return super(Teacher, self).create(vals)


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