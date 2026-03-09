from odoo import models, fields, api, _

class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Estate Property Type'
    _order = 'sequence desc'
    sequence = fields.Integer(string='Sequence', default=1)
    name = fields.Char(string='Property Type', required=True, help='The type of the property')
    description = fields.Text(string='Description', copy=False, help='The description of the property type')
    property_ids = fields.One2many(string='Properties', comodel_name='estate.property', inverse_name='property_type_id')