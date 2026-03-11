from odoo import models, fields, api
from odoo.exceptions import ValidationError

class RentalAssetApprovalConfig(models.Model):
    _name = 'rental.asset.approval.config'
    _description = 'Rental Asset Approval Configuration'
    
    description = fields.Char(string='Description')
    brand_ids = fields.Many2many(
        'fleet.vehicle.model.brand',
        string='Brands',
        help='Brand yang terkena rule ini'
    )
    min_qty = fields.Integer(string='Min Qty', required=True, default=1)
    max_qty = fields.Integer(
        string='Max Qty',
        help='0 atau kosong = tidak terbatas'
    )

    level_ids = fields.Many2many(
        'rental.approval.config',
        string='Approval Levels',
        help='Level-level approval yang dipakai untuk kombinasi brand & qty ini'
    )

    @api.constrains('min_qty', 'max_qty')
    def _check_qty_range(self):
        for rec in self:
            if rec.min_qty <= 0:
                raise ValidationError("Min Qty must be > 0")
            if rec.max_qty and rec.max_qty < rec.min_qty:
                raise ValidationError("Max Qty must be >= Min Qty")