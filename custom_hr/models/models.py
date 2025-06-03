# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EmployeeDynamicFields(models.TransientModel):
    _name = 'employee.dynamic.fields'
    _description = 'Dynamic Fields'

    # Field definition fields (similar to ir.model.fields but without inheritance)
    name = fields.Char(string='Field Name', required=True)
    field_description = fields.Char(string='Field Label', required=True)
    help = fields.Text(string='Field Help')
    required = fields.Boolean(string='Required')
    readonly = fields.Boolean(string='Readonly')
    index = fields.Boolean(string='Indexed')
    store = fields.Boolean(string='Stored', default=True)
    copied = fields.Boolean(string='Copied', default=True)
    widget = fields.Selection([
        ('image', 'Image'),
        ('many2many_tags', 'Tags'),
        ('binary', 'Binary'),
        ('radio', 'Radio'),
        ('priority', 'Priority'),
        ('monetary', 'Monetary'),
        ('selection', 'Selection')
    ], string='Widget')

    # Position and placement fields
    position_field = fields.Many2one('ir.model.fields', string='Field Name', required=True)
    position = fields.Selection([('before', 'Before'),
                                 ('after', 'After')], string='Position', required=True)
    model_id = fields.Many2one('ir.model', string='Model', required=True,
                               default=lambda self: self.env.ref('hr.model_hr_employee').id,
                               readonly=True)
    ref_model_id = fields.Many2one('ir.model', string='Model', index=True)


    selection_field = fields.Char(string="Selection Options")
    rel_field = fields.Many2one('ir.model.fields', string='Related Field')
    field_type = fields.Selection(selection='get_possible_field_types', string='Field Type', required=True)
    extra_features = fields.Boolean(string="Show Extra Properties")

    @api.model
    def get_possible_field_types(self):
        """Return all available field types other than 'one2many' and 'reference' fields."""
        field_list = sorted((key, key) for key in fields.MetaField.by_type)
        field_list.remove(('one2many', 'one2many'))
        field_list.remove(('reference', 'reference'))
        return field_list

    @api.onchange('field_type')
    def onchange_field_type(self):

        if self.field_type:
            self.widget = False

    def create_fields(self):

        field_name = self.name if self.name.startswith('x_') else 'x_' + self.name

        # Create the field in ir.model.fields
        field_values = {
            'name': field_name,
            'field_description': self.field_description,
            'model_id': self.model_id.id,
            'ttype': self.field_type,
            'required': self.required,
            'index': self.index,
            'store': self.store,
            'help': self.help,
            'readonly': self.readonly,
            'copied': self.copied,
            'is_dynamic_field': True
        }

        #
        # if self.ref_model_id and self.field_type in ['many2one', 'many2many']:
        #     field_values['relation'] = self.ref_model_id.model
        #
        #
        # if self.selection_field and self.field_type == 'selection':
        #     field_values['selection'] = self.selection_field

        self.env['ir.model.fields'].sudo().create(field_values)

        inherit_id = self.env.ref('hr.view_employee_form')
        arch_base = '''<?xml version="1.0"?>
                      <data>
                          <field name="%s" position="%s">
                              <field name="%s"/>
                          </field>
                      </data>''' % (self.position_field.name, self.position, field_name)

        if self.widget:
            arch_base = '''<?xml version="1.0"?>
                          <data>
                              <field name="%s" position="%s">
                                  <field name="%s" widget="%s"/>
                              </field>
                          </data>''' % (self.position_field.name, self.position, field_name, self.widget)

        self.env['ir.ui.view'].sudo().create({
            'name': 'employee.dynamic.fields.%s' % field_name,
            'type': 'form',
            'model': 'hr.employee',
            'mode': 'extension',
            'inherit_id': inherit_id.id,
            'arch_base': arch_base,
            'active': True
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }