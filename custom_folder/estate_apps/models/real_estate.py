from odoo import models, fields, api, _
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

class RealEstate(models.Model):
    # Keep model name aligned with demo/views expectations (Odoo tutorial convention).
    _name = 'estate.property'
    _description = 'Estate Property'
    
    name = fields.Char(string='Property Name', required=True, help='The name of the property')
    description = fields.Text(string='Description', copy=False, help='The description of the property')
    price = fields.Float(string='Price', required=True, help='The price of the property')
    selling_price = fields.Float(string='Selling Price', help='The selling price of the property')
    best_offer = fields.Float(string='Best Offer', compute='_compute_best_offer', store=True, help='The best offer for the property')
    bedrooms = fields.Integer(string='Number of Bedrooms', required=True, help='The number of bedrooms in the property')
    bathrooms = fields.Integer(string='Number of Bathrooms', required=True, help='The number of bathrooms in the property')
    garages = fields.Integer(string='Number of Garages', default=2, help='The number of garages in the property')
    garden = fields.Boolean(string='Garden', default=False, help='Whether the property has a garden')
    area = fields.Float(string='Area', required=True, help='The area of the property in square meters or square feet')
    area_unit = fields.Selection(string='Area Unit', selection=[('sqm', 'Square Meters'), ('sqft', 'Square Feet')], required=True, help='The unit of the area')
    living_area = fields.Float(string='Living Area', help='The living area of the property in square meters or square feet')
    garden_area = fields.Float(string='Garden Area', help='The garden area of the property in square meters or square feet')
    total_area = fields.Float(string='Total Area', compute='_compute_total_area', help='The total area of the property in square meters or square feet')
    # property_type = fields.Selection(string='Property Type', selection=[('house', 'House'), ('apartment', 'Apartment'), ('commercial', 'Commercial')], required=True, help='The type of the property')
    property_status = fields.Selection(string='Property Status', selection=[('available', 'Available'), ('sold', 'Sold'), ('rented', 'Rented')], required=True, help='The status of the property')
    is_active = fields.Boolean(string='Is Active', default=True, invisible=True, help='Whether the property is active')
    date_availability = fields.Date(string='Date Availability', help='The date the property will be available')
    created_at = fields.Date(string='Created At', default=fields.Date.today(), help='The date the property was created')
    updated_at = fields.Date(string='Updated At', default=fields.Date.today(), help='The date the property was updated')
    
    # Relations
    property_type_id = fields.Many2one(string='Property Type', comodel_name='estate.property.type', help='The type of the property')
    offer_ids = fields.One2many(string='Offers', comodel_name='estate.property.offer', inverse_name='property_id')
    tag_ids = fields.Many2many(string='Tags', comodel_name='estate.property.tag', inverse_name='property_id')
    
    # computed fields
    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area
            
    @api.depends('offer_ids.price')
    def _compute_best_offer(self):
        for record in self:
            record.best_offer = max(record.offer_ids.mapped('price')) if record.offer_ids else 0

    validity = fields.Integer(default=7)
    date_deadline = fields.Date(string='Date Deadline', compute='_compute_date_deadline', help='The date the property will be sold', inverse='_inverse_date_deadline')

    def _inverse_date_deadline(self):
        for record in self:
            record.validity = (record.date_deadline - fields.Date.today()).days

    @api.depends('validity')
    def _compute_date_deadline(self):
        for record in self:
            record.date_deadline = fields.Date.today() + relativedelta(days=record.validity)
            
    # on change method
    @api.onchange('price')
    def _onchange_price(self):
        if self.price < 0:
            return {
                'warning': {
                    'title': 'Invalid Price',
                    'message': 'The price cannot be negative'
                }
            }

    @api.onchange('garden')
    def _onchange_garden(self):
        if not self.garden:
            return {'value': {'garden_area': 0}}

    @api.onchange('garden_area')
    def _onchange_garden_area(self):
        if self.garden_area and self.garden_area > 0:
            return {'value': {'garden': True}}
        if self.garden_area < 0:
            return {
                'warning': {
                    'title': 'Invalid Garden Area',
                    'message': 'The garden area cannot be negative'
                }
            }

    @api.onchange('date_availability')
    def _onchange_date_availability(self):
        for record in self:
            if record.date_availability and record.date_availability < fields.Date.today():
                return {
                    'warning': {
                        'title': 'Invalid Date Availability',
                        'message': 'The date availability cannot be in the past'
                    }
                }
                
    # sql constraints
    @api.constrains('selling_price')
    def _check_selling_price(self):
        for record in self:
            if record.selling_price < record.price/2:
                raise ValidationError("The selling price cannot be less than 50% of the price")