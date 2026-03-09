from odoo import models, fields, api
from odoo.exceptions import ValidationError  

class RentalAssetRequestLine(models.Model):
    _name = 'rental.asset.request.line'
    _description = 'Rental Asset Request Line'

    request_id = fields.Many2one(
        'rental.asset.request.header',
        ondelete='cascade'
    )
    # default 1, auto increment ketika tambah line di request yang sama
    line_number = fields.Integer(string="Line Number", default=1)
    

    brand_id = fields.Many2one(
        'fleet.vehicle.model.brand',
        string="Product Brand"
    )

    model_id = fields.Many2one(
        'fleet.vehicle.model',
        string="Product Model"
    )

    quantity = fields.Integer(default=1)
    
    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError("Quantity must be greater than 0")

    @api.model_create_multi
    def create(self, vals_list):
        # Pakai next number per request_id agar batch create (beberapa line sekaligus) dapat 1, 2, 3, ...
        next_by_request = {}
        for vals in vals_list:
            request_id = vals.get("request_id") or self.env.context.get("default_request_id")
            if request_id:
                if request_id not in next_by_request:
                    last = self.search(
                        [("request_id", "=", request_id)],
                        order="line_number desc",
                        limit=1,
                    )
                    next_by_request[request_id] = (last.line_number + 1) if last else 1
                vals["line_number"] = next_by_request[request_id]
                next_by_request[request_id] += 1
        return super().create(vals_list)