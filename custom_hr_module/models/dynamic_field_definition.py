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

    # Store all dynamic field values in JSON format
    dynamic_fields_data = fields.Text('Dynamic Fields Data', default='{}')

    def get_dynamic_field_value(self, field_name):
        """Get value for a dynamic field"""
        try:
            data = json.loads(self.dynamic_fields_data or '{}')
            return data.get(field_name, '')
        except:
            return ''

    def set_dynamic_field_value(self, field_name, value):
        """Set value for a dynamic field"""
        try:
            data = json.loads(self.dynamic_fields_data or '{}')
            data[field_name] = value
            self.dynamic_fields_data = json.dumps(data)
        except:
            self.dynamic_fields_data = json.dumps({field_name: value})

    def get_dynamic_fields_dict(self):
        """Get all dynamic fields as dictionary"""
        try:
            return json.loads(self.dynamic_fields_data or '{}')
        except:
            return {}


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
        from odoo.exceptions import UserError

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