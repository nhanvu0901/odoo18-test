# models/dynamic_field_definition.py
from odoo import models, fields, api
from odoo.exceptions import UserError
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

    _sql_constraints = [
        ('unique_field_name', 'unique(name, target_model)',
         'Field name must be unique per model!'),
    ]

    @api.model
    def create(self, vals):
        """Override create to refresh target model after creating field"""
        record = super().create(vals)
        self._refresh_target_model(vals.get('target_model', 'hr.employee'))
        self._add_field_to_model(record)
        return record

    def write(self, vals):
        """Override write to refresh target model after updating field"""
        result = super().write(vals)
        target_models = set()

        # Collect all affected target models
        for record in self:
            target_models.add(record.target_model)
            self._add_field_to_model(record)

        if 'target_model' in vals:
            target_models.add(vals['target_model'])

        # Refresh all affected models
        for model_name in target_models:
            self._refresh_target_model(model_name)

        return result

    def unlink(self):
        """Override unlink to refresh target model after deleting field"""
        target_models = set(self.mapped('target_model'))
        result = super().unlink()

        # Refresh all affected models
        for model_name in target_models:
            self._refresh_target_model(model_name)

        return result

    def _add_field_to_model(self, field_record):
        """Add a single dynamic field to the target model"""
        try:
            model_name = field_record.target_model
            if model_name in self.env.registry:
                model = self.env[model_name]
                field_name = field_record.name

                # Skip if field already exists
                if field_name in model._fields:
                    return

                # Create the field object
                field_obj = model._create_dynamic_field_obj(field_record)

                # Add the field to the model
                model._add_field(field_name, field_obj)

                _logger.info(f"Added dynamic field '{field_name}' to model '{model_name}'")

        except Exception as e:
            _logger.error(f"Error adding field to model: {e}")

    def _refresh_target_model(self, model_name):
        """Refresh the target model to clear caches"""
        try:
            if model_name in self.env.registry:
                # Clear the model's field cache
                model = self.env[model_name]
                model.clear_caches()

                # Re-add all dynamic fields
                if hasattr(model, '_add_dynamic_fields_to_model'):
                    model._add_dynamic_fields_to_model()

                _logger.info(f"Cleared caches for model: {model_name}")

        except Exception as e:
            _logger.error(f"Error refreshing model {model_name}: {e}")

    @api.model
    def get_active_fields_for_model(self, model_name):
        """Get all active dynamic fields for a specific model"""
        return self.search([
            ('target_model', '=', model_name),
            ('active', '=', True)
        ], order='sequence')

    def action_refresh_model(self):
        """Manual action to refresh the target model"""
        for record in self:
            record._refresh_target_model(record.target_model)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success!',
                'message': 'Model refreshed successfully!',
                'type': 'success',
            }
        }


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

    @api.onchange('field_type')
    def _onchange_field_type(self):
        """Clear selection options when field type is not selection"""
        if self.field_type != 'selection':
            self.selection_options = False

    @api.constrains('name')
    def _check_field_name(self):
        """Validate field name format"""
        for record in self:
            if record.name:
                # Check for valid Python identifier
                if not record.name.replace('_', '').isalnum():
                    raise UserError("Field name can only contain letters, numbers, and underscores")

                if record.name.startswith('_'):
                    raise UserError("Field name cannot start with underscore")

                if record.name in ['id', 'create_date', 'write_date', 'create_uid', 'write_uid']:
                    raise UserError("Field name conflicts with system fields")

    def action_create_field(self):
        """Create the dynamic field definition"""
        self.ensure_one()

        # Validate selection options for selection fields
        if self.field_type == 'selection' and not self.selection_options:
            raise UserError("Selection options are required for dropdown fields")

        # Check if field already exists
        existing = self.env['dynamic.field.definition'].search([
            ('name', '=', self.name),
            ('target_model', '=', self.target_model)
        ])

        if existing:
            raise UserError(f"Field '{self.name}' already exists for model '{self.target_model}'")

        # Create the field definition
        field_def = self.env['dynamic.field.definition'].create({
            'name': self.name,
            'label': self.label,
            'field_type': self.field_type,
            'target_model': self.target_model,
            'selection_options': self.selection_options,
            'required': self.required,
            'help_text': self.help_text,
        })

        # Return success notification and close wizard
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success!',
                'message': f'Dynamic field "{self.label}" created successfully!',
                'type': 'success',
            }
        }

    def action_create_and_continue(self):
        """Create field and keep wizard open for creating more fields"""
        self.action_create_field()

        # Clear the form for next field
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dynamic.field.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_target_model': self.target_model,
            }
        }