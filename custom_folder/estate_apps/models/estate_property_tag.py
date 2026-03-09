from odoo import models, fields, api, _

class EstatePropertyTag(models.Model):
    _name = 'estate.property.tag'
    _description = 'Estate Property Tag'
    _sql_constraints = [
        ('check_name', 'UNIQUE(name)', 'Tag name must be unique'),
    ]
    _order = 'name'
    name = fields.Char(string='Tag Name', required=True, help='The name of the tag')
    color = fields.Integer(string='Color', help='The color of the tag')
    property_ids = fields.Many2many(string='Properties', comodel_name='estate.property', relation='estate_property_tag_property_rel', column1='tag_id', column2='property_id')