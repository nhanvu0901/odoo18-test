from odoo import models, fields, api


class StudentInvoiceWizard(models.TransientModel):
    """Wizard for creating student invoices"""
    _name = 'student.invoice.wizard'
    _description = 'Create Student Invoice Wizard'

    student_ids = fields.Many2many(
        comodel_name='student',
        string='Students',
        required=True,
        help='Students to create invoices for'
    )
    invoice_date = fields.Date(
        string='Invoice Date',
        default=fields.Date.today,
        required=True
    )
    semester = fields.Selection([
        ('fall', 'Fall Semester'),
        ('spring', 'Spring Semester'),
        ('summer', 'Summer Semester'),
    ], string='Semester', required=True)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Tuition Fee Product',
        required=True,
        domain=[('type', '=', 'service')]
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        required=True,
        domain=[('type', '=', 'sale')]
    )

    def action_create_invoices(self):
        """Create invoices for selected students"""
        self.ensure_one()
        invoice_vals_list = []

        for student in self.student_ids:
            # Find the partner for this student
            partner = self.env['res.partner'].search([
                ('student_id', '=', student.id)
            ], limit=1)

            if not partner:
                # If no partner linked to student, use the first contact
                partner = self.env['res.partner'].search([], limit=1)

            # Create invoice values
            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': partner.id,
                'invoice_date': self.invoice_date,
                'journal_id': self.journal_id.id,
                'student_id': student.id,
                'is_tuition_fee': True,
                'semester': self.semester,
                'invoice_line_ids': [(0, 0, {
                    'product_id': self.product_id.id,
                    'name': f'Tuition Fee - {student.name} - {self.semester.capitalize()} Semester',
                    'quantity': 1,
                    'price_unit': self.product_id.list_price,
                })],
            }
            invoice_vals_list.append(invoice_vals)

        # Create all invoices at once
        if invoice_vals_list:
            invoices = self.env['account.move'].create(invoice_vals_list)

            # Open the invoices
            action = {
                'name': 'Student Invoices',
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', invoices.ids)],
            }
            return action

        return {'type': 'ir.actions.act_window_close'}


class StudentReportWizard(models.TransientModel):
    """Wizard for generating student reports"""
    _name = 'student.report.wizard'
    _description = 'Student Report Wizard'

    student_id = fields.Many2one(
        comodel_name='student',
        string='Student',
        required=True
    )
    report_type = fields.Selection([
        ('grades', 'Grades Report'),
        ('attendance', 'Attendance Report'),
        ('full', 'Full Report Card')
    ], string='Report Type', default='full', required=True)
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To', default=fields.Date.today)

    def action_generate_report(self):
        """Generate the selected report for the student"""
        self.ensure_one()

        if self.report_type == 'grades':
            # Generate grades report
            return self._generate_grades_report()
        elif self.report_type == 'attendance':
            # Generate attendance report
            return self._generate_attendance_report()
        else:
            # Generate full report card
            return self._generate_full_report()

    def _generate_grades_report(self):
        """Generate a grades report"""
        # This is where you would implement the actual report generation
        # For example, using Odoo's QWeb reports
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'student.grade',
            'name': f'Grades for {self.student_id.name}',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.student_id.id)],
            'context': {'create': False}
        }

    def _generate_attendance_report(self):
        """Generate an attendance report"""
        # Implement attendance report logic
        return {'type': 'ir.actions.act_window_close'}

    def _generate_full_report(self):
        """Generate a full report card"""
        # Implement full report card generation
        return {
            'type': 'ir.actions.report',
            'report_name': 'school_management.report_student_card',
            'report_type': 'qweb-pdf',
            'data': {
                'student_id': self.student_id.id,
                'date_from': self.date_from,
                'date_to': self.date_to,
            }
        }


class StudentBulkUpdateWizard(models.TransientModel):
    """Wizard for updating multiple students at once"""
    _name = 'student.bulk.update.wizard'
    _description = 'Bulk Update Students Wizard'

    student_ids = fields.Many2many(
        comodel_name='student',
        string='Students',
        required=True
    )
    classe_id = fields.Many2one(
        comodel_name='classe',
        string='Move to Class'
    )
    stage = fields.Selection([
        ('draft', 'Draft'),
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
    ], string='Update Stage')

    def action_update_students(self):
        """Update the selected students with the specified values"""
        self.ensure_one()

        update_vals = {}
        if self.classe_id:
            update_vals['classe_id'] = self.classe_id.id
        if self.stage:
            update_vals['stage'] = self.stage

        if update_vals:
            self.student_ids.write(update_vals)

        return {'type': 'ir.actions.act_window_close'}