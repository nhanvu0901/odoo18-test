import logging

_logger = logging.getLogger(__name__)

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_id = fields.Char(
        string='Employee ID',
        help='Automatically generated Employee Identification Number based on prefix and employee database ID',
        compute='_compute_employee_id',
        store=False,  # Not stored in database
        search='_search_employee_id'  # Enable search functionality
    )
    employee_id_prefix = fields.Char(
        string='ID Prefix',
        size=10,
        help='Prefix for the employee ID (e.g., EMP, DEV, HR)',
    )

    @api.depends('employee_id_prefix')
    def _compute_employee_id(self):
        """Compute employee_id based on prefix and database ID"""
        for record in self:
            # Handle different ID types: regular ID, NewId, or no ID
            record_id = None

            if hasattr(record.id, 'origin') and record.id.origin:
                # This is a NewId object with an origin
                record_id = record.id.origin
            elif isinstance(record.id, int) and record.id > 0:
                # This is a regular database ID
                record_id = record.id
            elif hasattr(record, '_origin') and record._origin.id:
                # Try to get ID from the original record
                record_id = record._origin.id

            if record_id:
                prefix = record.employee_id_prefix or self._get_default_prefix()
                # Clean the prefix (remove non-alphanumeric characters except underscore)
                prefix = re.sub(r'[^A-Za-z0-9_]', '', prefix).upper()

                # Get the number format and apply it to the database ID
                number_format = self._get_number_format()
                try:
                    if number_format == '{}':
                        formatted_number = str(record_id)
                    else:
                        formatted_number = number_format.format(record_id)
                    record.employee_id = f"{prefix}{formatted_number}"
                except (ValueError, TypeError) as e:
                    _logger.error(
                        "Error formatting employee ID number %s with format '%s': %s. Using default format.",
                        record_id, number_format, str(e)
                    )
                    # Fallback to default 3-digit format
                    formatted_number = "{:03d}".format(record_id)
                    record.employee_id = f"{prefix}{formatted_number}"
            else:
                # For completely new records without any ID, show a placeholder
                prefix = record.employee_id_prefix or self._get_default_prefix()
                prefix = re.sub(r'[^A-Za-z0-9_]', '', prefix).upper()
                record.employee_id = f"{prefix}---"

    def _search_employee_id(self, operator, value):
        """Enable search functionality for computed employee_id field"""
        if operator in ('=', '!=', 'like', 'ilike', 'in', 'not in'):
            # Get all employees and filter based on computed employee_id
            all_employees = self.search([])
            matching_ids = []

            for employee in all_employees:
                computed_id = employee.employee_id
                if operator == '=' and computed_id == value:
                    matching_ids.append(employee.id)
                elif operator == '!=' and computed_id != value:
                    matching_ids.append(employee.id)
                elif operator in ('like', 'ilike'):
                    # Odoo's 'like' is case-sensitive, 'ilike' is case-insensitive
                    # For simplicity here, making both case-insensitive,
                    # or adjust if specific SQL-like behavior is needed.
                    if value.lower() in computed_id.lower():
                        matching_ids.append(employee.id)
                elif operator == 'in' and computed_id in value:
                    matching_ids.append(employee.id)
                elif operator == 'not in' and computed_id not in value:
                    matching_ids.append(employee.id)

            return [('id', 'in', matching_ids)]

        return [('id', '=', -1)]  # Return empty result for unsupported operators

    def _get_default_prefix(self):
        """Get default prefix from system parameters"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'employee_id_format.default_prefix', 'EMP'
        )

    def _get_number_format(self):
        """Get number format from system parameters with validation"""
        # Valid format options
        valid_formats = ['{:03d}', '{:04d}', '{:05d}', '{}']

        # Get the format from config parameters
        number_format = self.env['ir.config_parameter'].sudo().get_param(
            'employee_id_format.number_format', '{:03d}'
        )

        # Validate the format is one of the expected values
        if number_format not in valid_formats:
            _logger.warning(
                "Invalid number format '%s' found in config. Using default '{:03d}'",
                number_format
            )
            number_format = '{:03d}'

        return number_format

    @api.constrains('employee_id_prefix')
    def _check_prefix_format(self):
        """Validate prefix format"""
        for record in self:
            if record.employee_id_prefix:
                if not re.match(r'^[A-Za-z0-9_]+$', record.employee_id_prefix):
                    raise ValidationError(
                        _("Prefix can only contain letters, numbers, and underscores")
                    )
                if len(record.employee_id_prefix) > 10:
                    raise ValidationError(
                        _("Prefix cannot be longer than 10 characters")
                    )



