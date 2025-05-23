from odoo import models, fields, api
from odoo.exceptions import ValidationError

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)



class StudentInvoice(models.Model):
    """Extend the account.move model to connect with students"""
    _inherit = 'account.move'

    student_id = fields.Many2one(
        comodel_name='student',
        string='Student',
        help='Student related to this invoice'
    )
    is_tuition_fee = fields.Boolean(
        string='Is Tuition Fee',
        default=False,
        help='Check if this invoice is for tuition fees'
    )
    semester = fields.Selection([
        ('fall', 'Fall Semester'),
        ('spring', 'Spring Semester'),
        ('summer', 'Summer Semester'),
    ], string='Semester', help='Semester this tuition is for')

    # Related fields to access student.classe_id and student.student_age
    student_classe_id = fields.Many2one(
        comodel_name='classe',
        string='Class',
        related='student_id.classe_id',
        readonly=True
    )
    student_age = fields.Float(
        string='Student Age',
        related='student_id.student_age',
        readonly=True
    )

    @api.onchange('student_id')
    def _onchange_student_id(self):
        if self.student_id and self.is_tuition_fee:
            self.partner_id = self.student_id.teacher_id.partner_id
            self.invoice_date = fields.Date.today()
            self.payment_reference = f"Tuition Fee - {self.student_id.name}"

    def action_register_payment(self):
        """Override the payment registration method to add custom logic"""
        # Execute the original method
        res = super(StudentInvoice, self).action_register_payment()

        # Add custom logic for student invoices
        for invoice in self:
            if invoice.is_tuition_fee and invoice.state == 'posted':
                _logger.info(f"Tuition payment registered for student {invoice.student_id.name}")
                # Update student status
                if invoice.student_id:
                    invoice.student_id.write({'stage': 'enrolled'})

        return res

class SaleOrderInheritance(models.Model):
    """Extend the sale.order model to connect with the school system"""
    _inherit = 'sale.order'

    classe_id = fields.Many2one(
        comodel_name='classe',
        string='Class',
        help='Class associated with this sale order'
    )
    is_school_material = fields.Boolean(
        string='Is School Material',
        default=False,
        help='Check if this order is for school materials'
    )
    student_ids = fields.Many2many(
        comodel_name='student',
        string='Students',
        help='Students associated with this order'
    )

    @api.onchange('classe_id')
    def _onchange_classe_id(self):
        """Load all students from the class when class is selected"""
        if self.classe_id:
            self.student_ids = [(6, 0, self.classe_id.student_ids.ids)]

    def action_confirm(self):
        """Override the confirm method to add custom school logic"""
        # Check if there are students selected for school material orders
        for order in self:
            if order.is_school_material and not order.student_ids:
                raise ValidationError("You must select at least one student for school material orders.")

        # Call the original method
        return super(SaleOrderInheritance, self).action_confirm()


class HrEmployeeInherit(models.Model):

    _inherit = 'hr.employee'


    is_teacher = fields.Boolean(
        string='Is Teacher',
        compute='_compute_is_teacher',
        store=True,
        help='Automatically checked if this employee has a teacher record'
    )
    teacher_id = fields.Many2one(
        'teacher',
        string='Teacher Record',
        compute='_compute_teacher_id',
        store=True,
        help='Teacher record associated with this employee'
    )

    def _compute_teacher_id(self):
        for employee in self:
            if employee.id:
                teacher = self.env['teacher'].search([('employee_id', '=', employee.id)], limit=1)
                employee.teacher_id = teacher.id if teacher else False
            else:
                employee.teacher_id = False

    @api.depends('teacher_id')
    def _compute_is_teacher(self):
        """Automatically check is_teacher if teacher_id is found"""
        for employee in self:
            employee.is_teacher = bool(employee.teacher_id)
            if employee.is_teacher:
                _logger.info(
                    f"Employee {employee.name} automatically marked as teacher (Teacher ID: {employee.teacher_id.id})")

    def update_teacher_fields(self):
        """Manual method to update teacher-related fields"""
        self._compute_teacher_id()
        self._compute_is_teacher()