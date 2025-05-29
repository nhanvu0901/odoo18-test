# models/inherit.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from lxml import etree
import logging
import json

_logger = logging.getLogger(__name__)


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    text = fields.Char()

    # Store all dynamic field values in JSON format
    dynamic_fields_data = fields.Text('Dynamic Fields Data', default='{}')

    def _create_dynamic_field(self, field_def):
        """Create a field object based on the field definition"""
        field_type = field_def.field_type
        field_args = {
            'string': field_def.label,
            'required': field_def.required,
            'help': field_def.help_text or '',
            'compute': '_compute_dynamic_field',
            'inverse': '_inverse_dynamic_field',
            'store': False,  # Don't store in database, we use JSON storage
        }

        if field_type == 'char':
            return fields.Char(**field_args)
        elif field_type == 'text':
            return fields.Text(**field_args)
        elif field_type == 'boolean':
            return fields.Boolean(**field_args)
        elif field_type == 'integer':
            return fields.Integer(**field_args)
        elif field_type == 'float':
            return fields.Float(**field_args)
        elif field_type == 'date':
            return fields.Date(**field_args)
        elif field_type == 'datetime':
            return fields.Datetime(**field_args)
        elif field_type == 'selection':
            # Parse selection options
            options = []
            if field_def.selection_options:
                for line in field_def.selection_options.split('\n'):
                    line = line.strip()
                    if line:
                        options.append((line.lower().replace(' ', '_'), line))

            field_args['selection'] = options
            return fields.Selection(**field_args)
        else:
            # Default to Char
            return fields.Char(**field_args)

    @api.depends('dynamic_fields_data')
    def _compute_dynamic_field(self):
        """Compute method for all dynamic fields"""
        for record in self:
            try:
                data = json.loads(record.dynamic_fields_data or '{}')

                # Get all dynamic field definitions
                dynamic_fields = self.env['dynamic.field.definition'].search([
                    ('target_model', '=', 'hr.employee'),
                    ('active', '=', True)
                ])

                for field_def in dynamic_fields:
                    field_name = field_def.name
                    if hasattr(record, field_name):
                        value = data.get(field_name, '')

                        # Convert value based on field type
                        if field_def.field_type in ['integer']:
                            try:
                                value = int(value) if value else 0
                            except:
                                value = 0
                        elif field_def.field_type in ['float']:
                            try:
                                value = float(value) if value else 0.0
                            except:
                                value = 0.0
                        elif field_def.field_type == 'boolean':
                            value = bool(value)
                        elif field_def.field_type == 'date':
                            # Handle date conversion if needed
                            pass
                        elif field_def.field_type == 'datetime':
                            # Handle datetime conversion if needed
                            pass

                        setattr(record, field_name, value)

            except Exception as e:
                _logger.error(f"Error computing dynamic field: {e}")

    def _inverse_dynamic_field(self):
        """Inverse method to save dynamic field values"""
        for record in self:
            try:
                data = json.loads(record.dynamic_fields_data or '{}')

                # Get all dynamic field definitions
                dynamic_fields = self.env['dynamic.field.definition'].search([
                    ('target_model', '=', 'hr.employee'),
                    ('active', '=', True)
                ])

                for field_def in dynamic_fields:
                    field_name = field_def.name
                    if hasattr(record, field_name):
                        value = getattr(record, field_name)
                        data[field_name] = value

                record.dynamic_fields_data = json.dumps(data)

            except Exception as e:
                _logger.error(f"Error saving dynamic field: {e}")

    def read(self, fields=None, load='_classic_read'):
        """Override read to include dynamic field values"""
        result = super().read(fields, load)

        if not fields:
            return result

        try:
            # Get dynamic field definitions
            dynamic_fields = self.env['dynamic.field.definition'].search([
                ('target_model', '=', 'hr.employee'),
                ('active', '=', True)
            ])

            dynamic_field_names = [f.name for f in dynamic_fields]
            requested_dynamic_fields = [f for f in fields if f in dynamic_field_names]

            if not requested_dynamic_fields:
                return result

            # Add dynamic field values to each record
            for i, record in enumerate(self):
                data = record.get_dynamic_fields_dict()
                for field_name in requested_dynamic_fields:
                    result[i][field_name] = data.get(field_name, '')

        except Exception as e:
            _logger.error(f"Error reading dynamic fields: {e}")

        return result

    def write(self, vals):
        """Override write to handle dynamic field values"""
        # Extract dynamic field values from vals
        dynamic_vals = {}
        regular_vals = {}

        try:
            dynamic_fields = self.env['dynamic.field.definition'].search([
                ('target_model', '=', 'hr.employee'),
                ('active', '=', True)
            ])
            dynamic_field_names = [f.name for f in dynamic_fields]

            for key, value in vals.items():
                if key in dynamic_field_names:
                    dynamic_vals[key] = value
                else:
                    regular_vals[key] = value

            # Write regular fields first
            result = super().write(regular_vals) if regular_vals else True

            # Write dynamic fields
            if dynamic_vals:
                for record in self:
                    data = record.get_dynamic_fields_dict()
                    data.update(dynamic_vals)
                    record.dynamic_fields_data = json.dumps(data)

            return result

        except Exception as e:
            _logger.error(f"Error writing dynamic fields: {e}")
            return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle dynamic field values"""
        try:
            dynamic_fields = self.env['dynamic.field.definition'].search([
                ('target_model', '=', 'hr.employee'),
                ('active', '=', True)
            ])
            dynamic_field_names = [f.name for f in dynamic_fields]

            # Process each values dict
            processed_vals_list = []
            dynamic_data_list = []

            for vals in vals_list:
                dynamic_vals = {}
                regular_vals = {}

                for key, value in vals.items():
                    if key in dynamic_field_names:
                        dynamic_vals[key] = value
                    else:
                        regular_vals[key] = value

                processed_vals_list.append(regular_vals)
                dynamic_data_list.append(dynamic_vals)

            # Create records with regular fields
            records = super().create(processed_vals_list)

            # Set dynamic field data
            for record, dynamic_vals in zip(records, dynamic_data_list):
                if dynamic_vals:
                    record.dynamic_fields_data = json.dumps(dynamic_vals)
                elif not record.dynamic_fields_data:
                    record.dynamic_fields_data = '{}'

            return records

        except Exception as e:
            _logger.error(f"Error creating with dynamic fields: {e}")
            return super().create(vals_list)

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Override fields_get to include dynamic fields in field definitions"""
        res = super().fields_get(allfields, attributes)

        try:
            # Add dynamic fields to the fields definition
            dynamic_fields = self.env['dynamic.field.definition'].search([
                ('target_model', '=', 'hr.employee'),
                ('active', '=', True)
            ])

            for field_def in dynamic_fields:
                field_name = field_def.name
                if not allfields or field_name in allfields:
                    field_info = {
                        'type': field_def.field_type,
                        'string': field_def.label,
                        'required': field_def.required,
                        'help': field_def.help_text or '',
                        'readonly': False,
                        'store': False,
                    }

                    # Add selection options if it's a selection field
                    if field_def.field_type == 'selection' and field_def.selection_options:
                        options = []
                        for line in field_def.selection_options.split('\n'):
                            line = line.strip()
                            if line:
                                options.append([line.lower().replace(' ', '_'), line])
                        field_info['selection'] = options

                    res[field_name] = field_info

        except Exception as e:
            _logger.error(f"Error in fields_get for dynamic fields: {e}")

        return res

    @api.model
    def get_views(self, views, options=None):
        """Override get_views to dynamically add custom fields to form view"""
        result = super().get_views(views, options)

        # Only modify the form view if dynamic fields are properly loaded
        if 'form' in result['views']:
            try:
                # Check if we have any dynamic field definitions
                dynamic_fields = self.env['dynamic.field.definition'].search([
                    ('target_model', '=', 'hr.employee'),
                    ('active', '=', True)
                ])

                # Only inject fields if all defined fields exist on the model
                all_fields_exist = True
                for field_def in dynamic_fields:
                    if field_def.name not in self._fields:
                        all_fields_exist = False
                        _logger.warning(f"Dynamic field '{field_def.name}' not found in model, form injection disabled")
                        break

                if all_fields_exist and dynamic_fields:
                    result['views']['form'] = self._inject_custom_fields_to_form(
                        result['views']['form']
                    )
                elif dynamic_fields:
                    _logger.warning("Some dynamic fields are not properly loaded. Skipping form injection.")

            except Exception as e:
                _logger.error(f"Error in get_views: {e}")

        return result

    def _inject_custom_fields_to_form(self, form_view):
        """Inject custom fields into the employee form view dynamically"""
        try:
            # Parse the existing form architecture
            arch = etree.fromstring(form_view['arch'])

            # Get all custom fields defined in this model
            custom_fields = self._get_form_custom_fields()

            # Check if fields are already in the form to avoid duplicates
            existing_fields = self._get_existing_form_fields(arch)

            # Filter out fields that already exist in the form
            fields_to_add = [
                field for field in custom_fields
                if field not in existing_fields
            ]

            if fields_to_add:
                # Double-check that all fields actually exist on the model before adding
                verified_fields = []
                for field_name in fields_to_add:
                    if field_name in self._fields:
                        verified_fields.append(field_name)
                    else:
                        _logger.warning(f"Skipping field '{field_name}' - not found in model._fields")

                if verified_fields:
                    # Find insertion point
                    insertion_point = self._find_insertion_point(arch)

                    if insertion_point is not None:
                        # Create and insert the custom fields
                        self._insert_fields_at_point(arch, insertion_point, verified_fields)

                        # Update the form view architecture
                        form_view['arch'] = etree.tostring(arch, encoding='unicode')

                        _logger.info(f"Successfully added verified fields: {verified_fields}")
                    else:
                        _logger.warning("Could not find suitable insertion point for custom fields")
                else:
                    _logger.warning("No verified fields to add to form")

        except Exception as e:
            _logger.error(f"Error injecting custom fields: {str(e)}")

        return form_view

    def _get_form_custom_fields(self):
        """Get list of custom fields to add to the form"""
        custom_fields = ['text']  # Static fields

        try:
            # Get dynamic fields from dynamic.field.definition
            dynamic_field_data = self.env['dynamic.field.definition'].search([
                ('target_model', '=', 'hr.employee'),
                ('active', '=', True)
            ])

            for field in dynamic_field_data:
                if field.name not in custom_fields:
                    custom_fields.append(field.name)

        except Exception as e:
            _logger.error(f"Error getting dynamic fields: {e}")

        return custom_fields

    def _get_existing_form_fields(self, arch):
        """Extract existing field names from form architecture"""
        existing_fields = set()
        for field_elem in arch.xpath("//field[@name]"):
            existing_fields.add(field_elem.get('name'))
        return existing_fields

    def _find_insertion_point(self, arch):
        """Find the best insertion point in the form"""
        insertion_selectors = [
            "//field[@name='coach_id']",
            "//field[@name='parent_id']",
            "//group[last()]",  # Last group as fallback
        ]

        for selector in insertion_selectors:
            elements = arch.xpath(selector)
            if elements:
                return elements[0]

        return None

    def _insert_fields_at_point(self, arch, insertion_point, fields_to_add):
        """Insert custom fields at the specified point"""
        parent = insertion_point.getparent()
        insert_index = list(parent).index(insertion_point) + 1

        # Create a group to contain our custom fields
        custom_group = etree.Element('group', {
            'string': 'Dynamic Fields',
            'col': '2'
        })

        # Add each custom field to the group
        for field_name in fields_to_add:
            field_element = etree.Element('field', {'name': field_name})
            custom_group.append(field_element)

        # Insert the group after the insertion point
        parent.insert(insert_index, custom_group)

    # Helper methods for dynamic field values
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


class HrEmployeePublicInherit(models.Model):
    _inherit = 'hr.employee.public'

    text = fields.Char(readonly=True)
    dynamic_fields_data = fields.Text('Dynamic Fields Data', default='{}', readonly=True)