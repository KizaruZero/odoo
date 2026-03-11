from odoo import models, fields, api

class RentalDelegateApproval(models.Model):
    _name = 'rental.delegate.approval'
    _description = 'Rental Delegate Approval'
    
    approval_id = fields.Many2one(
        'rental.approval.config',
        string='Approval',
        required=True,
        ondelete='cascade',
    )

    approval_user_id = fields.Many2one(
        'res.users',
        string='Approval User',
        related='approval_id.user_id',
        readonly=True,
        store=False,
    )
    
    delegate_id = fields.Many2one(
        'res.users',
        string='Delegate',
        required=True,
        ondelete='cascade',
    )
    
    delegate_date = fields.Date(
        string='Delegate Date',
        required=True,
        ondelete='cascade',
    )
    
    delegate_maximum_date = fields.Date(
        string='Delegate Maximum Date',
        required=True,
        ondelete='cascade',
    )
    
    notes = fields.Text(string='Notes')
    
    @api.onchange('delegate_id')
    def _onchange_delegate_id(self):
        if self.delegate_id:
            self.delegate_date = fields.Date.today()
            self.delegate_maximum_date = fields.Date.today()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        ApprovalLine = self.env['rental.asset.request.approval']

        for rec in records:
            original_user = rec.approval_id.user_id
            if not original_user or not rec.delegate_id:
                continue

            lines = ApprovalLine.search([
                ('user_id', '=', original_user.id),
                ('state', '=', 'waiting'),
                ('is_active', '=', True),
                ('request_id.state', 'not in', ['approved', 'rejected']),
            ])

            if lines:
                lines.write({'user_id': rec.delegate_id.id})
        return records

    def write(self, vals):
        ApprovalLine = self.env['rental.asset.request.approval']
        # simpan delegate lama sebelum write
        old_data = {rec.id: rec.delegate_id for rec in self}
        res = super().write(vals)

        # jika delegate_id diganti, pindahkan juga approval line waiting ke delegate baru
        if 'delegate_id' in vals:
            for rec in self:
                old_delegate = old_data.get(rec.id)
                new_delegate = rec.delegate_id
                if not old_delegate or not new_delegate or old_delegate == new_delegate:
                    continue

                lines = ApprovalLine.search([
                    ('user_id', '=', old_delegate.id),
                    ('state', '=', 'waiting'),
                    ('is_active', '=', True),
                    ('request_id.state', 'not in', ['approved', 'rejected']),
                ])
                if lines:
                    lines.write({'user_id': new_delegate.id})

        return res

    
