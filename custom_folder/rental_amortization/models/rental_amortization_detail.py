from odoo import models, fields, api


class RentalAmortizationDetail(models.Model):
    _name = 'rental.amortization.detail'
    _description = 'Rental Amortization Detail'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    rental_amortization_header_id = fields.Many2one(
        'rental.amortization.header',
        string='Rental Amortization Header',
        required=True,
        ondelete='cascade',
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='rental_amortization_header_id.currency_id',
        store=True,
        readonly=True,
    )
    payment_date = fields.Date(string='Payment Date', required=True)
    payment_amount = fields.Float(string='Payment Amount', required=True)
    interest_rate = fields.Float(string='Interest Rate', required=True, digits=(16, 9))
    interest_amount = fields.Float(string='Interest Amount', required=True)
    net_depreciation_amount = fields.Float(string='Net Depreciation Amount', required=True)
    principal_amount = fields.Float(string='Principal Amount', required=True)
    remaining_balance = fields.Float(string='Remaining Balance', required=True)
    notes = fields.Text(string='Notes')