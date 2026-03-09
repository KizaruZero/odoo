from odoo import models, fields

class RentalAssetRequestBrand(models.Model):
    _name = 'rental.asset.request.brand'
    _description = 'Rental Asset Request Brand'

    name = fields.Char(
        string="Name",
        required=True,
        copy=False,
        default='New'
    )