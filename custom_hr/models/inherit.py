# models/inherit.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from lxml import etree
import logging
import json

_logger = logging.getLogger(__name__)


class inheritModel(models.Model):
    _inherit = 'ir.model.fields'

    is_dynamic_field = fields.Boolean(default=False)


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_id = fields.Char(
        string='Employee ID',
        help='Unique Employee Identification Number',
        copy=False,
        index=True
    )
    employee_id_prefix = fields.Char(
        string='ID Prefix',
        size=10,
        help='Prefix for the employee ID (e.g., EMP, DEV, HR)'
    )

    @api.model
    def create(self, vals):
        # Auto-generate employee_id if not provided
        if not vals.get('employee_id'):
            prefix = vals.get('employee_id_prefix') or self._get_default_prefix()
            vals['employee_id'] = self._generate_employee_id(prefix)
            if not vals.get('employee_id_prefix'):
                vals['employee_id_prefix'] = prefix
        elif vals.get('employee_id_prefix'):
            # If both employee_id and prefix are provided, validate format
            self._validate_employee_id_format(vals['employee_id'], vals['employee_id_prefix'])

        return super(HrEmployee, self).create(vals)

    def write(self, vals):
        # Handle prefix changes
        if 'employee_id_prefix' in vals:
            for record in self:
                new_prefix = vals['employee_id_prefix'] or self._get_default_prefix()
                if record.employee_id_prefix != new_prefix:
                    # Generate new employee_id with new prefix
                    vals['employee_id'] = self._generate_employee_id(new_prefix)

        return super(HrEmployee, self).write(vals)

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

    def _generate_employee_id(self, prefix):
        """Generate employee ID with prefix and auto-increment number"""
        if not prefix:
            prefix = self._get_default_prefix()

        # Clean the prefix (remove non-alphanumeric characters except underscore)
        prefix = re.sub(r'[^A-Za-z0-9_]', '', prefix).upper()

        # Get the next sequence number for this prefix
        next_number = self._get_next_sequence_number(prefix)

        # Get the number format from config parameters
        number_format = self._get_number_format()

        try:
            # Format the number according to the specified format
            if number_format == '{}':
                # No formatting, just convert to string
                formatted_number = str(next_number)
            else:
                # Use the format string (e.g., {:03d}, {:04d}, {:05d})
                formatted_number = number_format.format(next_number)

            return f"{prefix}{formatted_number}"

        except (ValueError, TypeError) as e:
            _logger.error(
                "Error formatting employee ID number %s with format '%s': %s. Using default format.",
                next_number, number_format, str(e)
            )
            # Fallback to default 3-digit format
            formatted_number = "{:03d}".format(next_number)
            return f"{prefix}{formatted_number}"

    def _get_next_sequence_number(self, prefix):
        """Get the next available sequence number for a given prefix"""
        # Find all employee IDs with the same prefix
        pattern = f"^{re.escape(prefix)}(\d+)$"

        employees = self.search([('employee_id', '!=', False)])
        existing_numbers = []

        for emp in employees:
            if emp.employee_id:
                match = re.match(pattern, emp.employee_id)
                if match:
                    try:
                        existing_numbers.append(int(match.group(1)))
                    except ValueError:
                        # Skip if number can't be converted to int
                        continue

        # Return the next number in sequence
        if existing_numbers:
            return max(existing_numbers) + 1
        else:
            return 1

    def _validate_employee_id_format(self, employee_id, prefix):
        """Validate that employee_id matches the expected format with prefix"""
        if not employee_id or not prefix:
            return

        pattern = f"^{re.escape(prefix)}\d+$"
        if not re.match(pattern, employee_id):
            raise ValidationError(
                _("Employee ID '%s' does not match the expected format with prefix '%s'")
                % (employee_id, prefix)
            )

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

    @api.constrains('employee_id')
    def _check_employee_id_unique(self):
        """Ensure employee ID is unique"""
        for record in self:
            if record.employee_id:
                duplicate = self.search([
                    ('employee_id', '=', record.employee_id),
                    ('id', '!=', record.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(
                        _("Employee ID '%s' already exists for employee '%s'")
                        % (record.employee_id, duplicate.name)
                    )