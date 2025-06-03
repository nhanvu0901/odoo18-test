from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Renamed field: default_employee_prefix -> employee_prefix_default
    employee_prefix_default = fields.Char(
        string='Default Employee ID Prefix',
        config_parameter='employee_id_format.default_prefix',  # System parameter key remains the same
        help='Default prefix for new employee IDs'
    )

    employee_number_format = fields.Selection([
        ('{:03d}', '3 digits (001, 002, 003)'),
        ('{:04d}', '4 digits (0001, 0002, 0003)'),
        ('{:05d}', '5 digits (00001, 00002, 00003)'),
        ('{}', 'No leading zeros (1, 2, 3)'),
    ], string='Number Format',
        config_parameter='employee_id_format.number_format',
        help='Format for the numeric part of employee IDs')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        # Use the new field name: self.employee_prefix_default
        set_param('employee_id_format.default_prefix', self.employee_prefix_default or '')
        set_param('employee_id_format.number_format', self.employee_number_format or '{}')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            # Use the new field name for the dict key
            employee_prefix_default=get_param('employee_id_format.default_prefix', default=''),
            employee_number_format=get_param('employee_id_format.number_format', default='{}'),
        )
        return res