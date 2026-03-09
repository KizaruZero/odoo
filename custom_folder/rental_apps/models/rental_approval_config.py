from odoo import models, fields


class RentalApprovalConfig(models.Model):
    _name = 'rental.approval.config'
    _description = 'Rental Approval Configuration'

    level = fields.Selection([
        ('1', 'L1 Manager'),
        ('2', 'L2 Sr Manager'),
        ('3', 'L3 Director'),
    ], required=True)

    user_id = fields.Many2one(
        'res.users',
        required=True
    )