from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Estate Property Offer'

    price = fields.Float(string='Price', required=True, help='The price of the offer')
    status = fields.Selection(
        string='Status',
        selection=[('new', 'New'), ('accepted', 'Accepted'), ('refused', 'Refused')],
        default='new',
        required=True,
        help='The status of the offer',
    )
    partner_id = fields.Many2one(string='Partner', comodel_name='res.partner', help='The partner who made the offer')
    property_id = fields.Many2one(string='Property', comodel_name='estate.property', help='The property the offer is for')
    date_created = fields.Date(string='Date Created', default=fields.Date.today(), help='The date the offer was created')
    type_id = fields.Many2one(string='Type', related='property_id.property_type_id', help='The type of the offer', store=True)

    def button_accept_offer(self):
        self.ensure_one()
        if self.property_id.offer_ids.filtered(lambda o: o.status == 'accepted'):
            raise UserError(_('An offer has already been accepted for this property.'))
        self.status = 'accepted'
        self.property_id.write({
            'property_status': 'sold',
            'selling_price': self.price,
        })
        return True

    def button_refuse_offer(self):
        self.ensure_one()
        self.status = 'refused'
        return True