from odoo import models, fields, api
from odoo.exceptions import ValidationError
from lxml import etree
import logging

_logger = logging.getLogger(__name__)


class HrEmployeeInherit(models.Model):

    _inherit = 'hr.employee'

    text = fields.Char()

    @api.model
    def get_views(self, views, options=None):
        """Override get_views to dynamically add custom fields to form view"""
        result = super().get_views(views, options)

        # Only modify the form view
        if 'form' in result['views']:
            result['views']['form'] = self._inject_custom_fields_to_form(
                result['views']['form']
            )

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
            ]

            if fields_to_add:
                # Find insertion point (after coach_id field or fallback locations)
                insertion_point = self._find_insertion_point(arch)

                if insertion_point is not None:
                    # Create and insert the custom fields
                    self._insert_fields_at_point(arch, insertion_point, fields_to_add)

                    # Update the form view architecture
                    form_view['arch'] = etree.tostring(arch, encoding='unicode')

                    _logger.info(f"Successfully added custom fields: {fields_to_add}")
                else:
                    _logger.warning("Could not find suitable insertion point for custom fields")

        except Exception as e:
            _logger.error(f"Error injecting custom fields: {str(e)}")

        return form_view



    def _get_form_custom_fields(self):
        custom_fields = [
            'text'
        ]


        existing_fields = []
        for field_name in custom_fields:
            if field_name in self._fields:
                existing_fields.append(field_name)
            else:
                _logger.warning(f"Field '{field_name}' not found in model, skipping...")

        # check in the dynamic.field.definition
        custom_field_data = self.env['dynamic.field.definition'].search([])

        if len(custom_field_data) > 0:
            for field in custom_field_data:
                if field.name not in custom_fields:
                    existing_fields.append(field.name)

        return existing_fields

    def _get_existing_form_fields(self, arch):
        """Extract existing field names from form architecture"""
        existing_fields = set()
        for field_elem in arch.xpath("//field[@name]"):
            existing_fields.add(field_elem.get('name'))
        return existing_fields

    def _find_insertion_point(self, arch):
        """Find the best insertion point in the form"""
        # Try multiple possible insertion points in order of preference
        insertion_selectors = [
            "//field[@name='coach_id']",  # After coach_id (as in your example)
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
            'string': 'Additional Information',
            'col': '2'
        })

        # Add each custom field to the group
        for field_name in fields_to_add:
            field_element = etree.Element('field', {'name': field_name})
            custom_group.append(field_element)

        # Insert the group after the insertion point
        parent.insert(insert_index, custom_group)


class HrEmployeePublicInherit(models.Model):
    _inherit = 'hr.employee.public'

    text = fields.Char(readonly=True)