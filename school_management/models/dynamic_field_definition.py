# models/dynamic_field_definition.py
from odoo import models, fields, api
from lxml import etree
import json
import logging

_logger = logging.getLogger(__name__)


class DynamicFieldDefinition(models.Model):
    """Model to store dynamic field definitions"""
    _name = 'dynamic.field.definition'
    _description = 'Dynamic Field Definition'

    name = fields.Char('Field Name', required=True)
    label = fields.Char('Field Label', required=True)
    field_type = fields.Selection([
        ('char', 'Text'),
        ('text', 'Long Text'),
        ('boolean', 'Checkbox'),
        ('integer', 'Number'),
        ('float', 'Decimal'),
        ('selection', 'Dropdown'),
        ('date', 'Date'),
        ('datetime', 'Date & Time'),
    ], string='Field Type', required=True)

    target_model = fields.Char('Target Model', required=True, default='hr.employee')
    selection_options = fields.Text('Selection Options', help='For dropdown fields, one option per line')
    required = fields.Boolean('Required', default=False)
    help_text = fields.Text('Help Text')
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)

    @api.model
    def get_active_fields_for_model(self, model_name):
        """Get all active dynamic fields for a specific model"""
        return self.search([
            ('target_model', '=', model_name),
            ('active', '=', True)
        ], order='sequence')


class DynamicFieldData(models.Model):
    """Model to store dynamic field data"""
    _name = 'dynamic.field.data'
    _description = 'Dynamic Field Data Storage'

    record_id = fields.Integer('Record ID', required=True)
    model_name = fields.Char('Model Name', required=True)
    field_name = fields.Char('Field Name', required=True)
    field_value = fields.Text('Field Value')

    _sql_constraints = [
        ('unique_field_data', 'unique(record_id, model_name, field_name)',
         'Only one value per field per record allowed!')
    ]

    @api.model
    def get_field_value(self, record_id, model_name, field_name):
        """Get value for a specific dynamic field"""
        data = self.search([
            ('record_id', '=', record_id),
            ('model_name', '=', model_name),
            ('field_name', '=', field_name)
        ], limit=1)
        return data.field_value if data else ''

    @api.model
    def set_field_value(self, record_id, model_name, field_name, value):
        """Set value for a specific dynamic field"""
        data = self.search([
            ('record_id', '=', record_id),
            ('model_name', '=', model_name),
            ('field_name', '=', field_name)
        ], limit=1)

        if data:
            data.field_value = str(value) if value else ''
        else:
            self.create({
                'record_id': record_id,
                'model_name': model_name,
                'field_name': field_name,
                'field_value': str(value) if value else ''
            })


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    # JSON field to store all dynamic field values (alternative approach)
    dynamic_fields_data = fields.Text('Dynamic Fields Data', default='{}')

    @api.model
    def get_views(self, views, options=None):
        """Override get_views to dynamically add custom fields to form view"""
        result = super().get_views(views, options)

        # Only modify the form view
        if 'form' in result['views']:
            result['views']['form'] = self._inject_dynamic_fields_to_form(
                result['views']['form']
            )

        return result

    def _inject_dynamic_fields_to_form(self, form_view):
        """Inject dynamic fields into the employee form view"""
        try:
            # Parse the existing form architecture
            arch = etree.fromstring(form_view['arch'])

            # Get dynamic field definitions
            dynamic_fields = self.env['dynamic.field.definition'].get_active_fields_for_model('hr.employee')

            if dynamic_fields:
                # Find insertion point
                insertion_point = self._find_insertion_point(arch)

                if insertion_point is not None:
                    # Create and insert the dynamic fields
                    self._insert_dynamic_fields_at_point(arch, insertion_point, dynamic_fields)

                    # Update the form view architecture
                    form_view['arch'] = etree.tostring(arch, encoding='unicode')

                    _logger.info(f"Successfully added dynamic fields: {[f.name for f in dynamic_fields]}")

        except Exception as e:
            _logger.error(f"Error injecting dynamic fields: {str(e)}")

        return form_view

    def _find_insertion_point(self, arch):
        """Find the best insertion point in the form"""
        insertion_selectors = [
            "//field[@name='coach_id']",
            "//field[@name='parent_id']",
            "//field[@name='department_id']",
            "//group[1]",
        ]

        for selector in insertion_selectors:
            elements = arch.xpath(selector)
            if elements:
                return elements[0]

        return None

    def _insert_dynamic_fields_at_point(self, arch, insertion_point, dynamic_fields):
        """Insert dynamic fields at the specified point"""
        parent = insertion_point.getparent()
        insert_index = list(parent).index(insertion_point) + 1

        # Create a group to contain dynamic fields
        dynamic_group = etree.Element('group', {
            'string': 'Dynamic Fields',
            'col': '2'
        })

        # Add each dynamic field to the group
        for field_def in dynamic_fields:
            field_attrs = {
                'name': f'dynamic_{field_def.name}',
                'string': field_def.label
            }

            if field_def.help_text:
                field_attrs['help'] = field_def.help_text

            if field_def.required:
                field_attrs['required'] = '1'

            # Handle selection fields
            if field_def.field_type == 'selection' and field_def.selection_options:
                options = field_def.selection_options.strip().split('\n')
                selection_str = str([(opt.strip(), opt.strip()) for opt in options if opt.strip()])
                field_attrs['selection'] = selection_str

            field_element = etree.Element('field', field_attrs)
            dynamic_group.append(field_element)

        # Insert the group after the insertion point
        parent.insert(insert_index, dynamic_group)

    @api.model
    def create(self, vals):
        """Override create to handle dynamic fields"""
        # Extract dynamic field values
        dynamic_vals = self._extract_dynamic_field_values(vals)

        # Create the record normally
        record = super().create(vals)

        # Save dynamic field values
        if dynamic_vals:
            self._save_dynamic_field_values(record.id, dynamic_vals)

        return record

    def write(self, vals):
        """Override write to handle dynamic fields"""
        # Extract dynamic field values
        dynamic_vals = self._extract_dynamic_field_values(vals)

        # Update the record normally
        result = super().write(vals)

        # Save dynamic field values for each record
        if dynamic_vals:
            for record in self:
                self._save_dynamic_field_values(record.id, dynamic_vals)

        return result

    def read(self, fields=None, load='_classic_read'):
        """Override read to include dynamic field values"""
        result = super().read(fields, load)

        # Add dynamic field values to the result
        if isinstance(result, list):
            for record_data in result:
                self._add_dynamic_field_values_to_read(record_data)
        else:
            self._add_dynamic_field_values_to_read(result)

        return result

    def _extract_dynamic_field_values(self, vals):
        """Extract dynamic field values from vals"""
        dynamic_vals = {}
        keys_to_remove = []

        for key, value in vals.items():
            if key.startswith('dynamic_'):
                field_name = key[8:]  # Remove 'dynamic_' prefix
                dynamic_vals[field_name] = value
                keys_to_remove.append(key)

        # Remove dynamic fields from vals to avoid database errors
        for key in keys_to_remove:
            vals.pop(key, None)

        return dynamic_vals

    def _save_dynamic_field_values(self, record_id, dynamic_vals):
        """Save dynamic field values"""
        for field_name, value in dynamic_vals.items():
            self.env['dynamic.field.data'].set_field_value(
                record_id, 'hr.employee', field_name, value
            )

    def _add_dynamic_field_values_to_read(self, record_data):
        """Add dynamic field values to read result"""
        if 'id' not in record_data:
            return

        record_id = record_data['id']
        dynamic_fields = self.env['dynamic.field.definition'].get_active_fields_for_model('hr.employee')

        for field_def in dynamic_fields:
            field_key = f'dynamic_{field_def.name}'
            value = self.env['dynamic.field.data'].get_field_value(
                record_id, 'hr.employee', field_def.name
            )

            # Convert value based on field type
            if field_def.field_type == 'boolean':
                record_data[field_key] = value.lower() == 'true' if value else False
            elif field_def.field_type in ['integer']:
                record_data[field_key] = int(value) if value and value.isdigit() else 0
            elif field_def.field_type == 'float':
                try:
                    record_data[field_key] = float(value) if value else 0.0
                except ValueError:
                    record_data[field_key] = 0.0
            else:
                record_data[field_key] = value


# wizard/dynamic_field_wizard.py
class DynamicFieldWizard(models.TransientModel):
    """Wizard to create dynamic fields"""
    _name = 'dynamic.field.wizard'
    _description = 'Dynamic Field Creation Wizard'

    name = fields.Char('Field Name', required=True, help='Internal field name (no spaces, lowercase)')
    label = fields.Char('Field Label', required=True, help='Display label for the field')
    field_type = fields.Selection([
        ('char', 'Text'),
        ('text', 'Long Text'),
        ('boolean', 'Checkbox'),
        ('integer', 'Number'),
        ('float', 'Decimal'),
        ('selection', 'Dropdown'),
        ('date', 'Date'),
        ('datetime', 'Date & Time'),
    ], string='Field Type', required=True, default='char')

    target_model = fields.Selection([
        ('hr.employee', 'Employee'),
        # Add more models as needed
    ], string='Target Model', required=True, default='hr.employee')

    selection_options = fields.Text('Selection Options',
                                    help='For dropdown fields only. Enter one option per line.')
    required = fields.Boolean('Required Field', default=False)
    help_text = fields.Text('Help Text')

    def action_create_field(self):
        """Create the dynamic field definition"""
        # Validate field name
        if not self.name.replace('_', '').isalnum():
            raise UserError("Field name can only contain letters, numbers, and underscores")

        # Check if field already exists
        existing = self.env['dynamic.field.definition'].search([
            ('name', '=', self.name),
            ('target_model', '=', self.target_model)
        ])

        if existing:
            raise UserError(f"Field '{self.name}' already exists for model '{self.target_model}'")

        # Create the field definition
        self.env['dynamic.field.definition'].create({
            'name': self.name,
            'label': self.label,
            'field_type': self.field_type,
            'target_model': self.target_model,
            'selection_options': self.selection_options,
            'required': self.required,
            'help_text': self.help_text,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success!',
                'message': f'Dynamic field "{self.label}" created successfully!',
                'type': 'success',
            }
        }