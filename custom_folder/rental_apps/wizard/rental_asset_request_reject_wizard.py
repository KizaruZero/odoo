from odoo import models, fields, api
from odoo.exceptions import ValidationError


class RentalAssetRequestRejectWizard(models.TransientModel):
    _name = 'rental.asset.request.reject.wizard'
    _description = 'Reject Request Wizard'

    request_id = fields.Many2one(
        'rental.asset.request.header',
        string="Request",
        required=True,
        readonly=True,
        default=lambda self: self.env.context.get('active_id')
    )

    notes = fields.Text(
        string="Notes",
        help="Reason for rejection"
    )

    attachment = fields.Binary(
        string="Attachment (PDF)",
        attachment=True
    )

    attachment_filename = fields.Char(
        string="Filename"
    )

    def action_confirm_reject(self):
        self.ensure_one()
        request = self.request_id

        approval = request.approval_line_ids.filtered(
            lambda x: x.user_id == self.env.user and x.state == 'waiting' and x.is_active
        )
        if not approval:
            raise ValidationError("You have no pending approval to reject")

        previous_approval = request.approval_line_ids.filtered(
            lambda x: x.level < approval.level and x.is_active
        )
        if previous_approval.filtered(lambda x: x.state != 'approved' and x.is_active):
            raise ValidationError("Previous approval level is not approved")
        
        # Simpan notes dan attachment ke approval
        approval_vals = {
            'state': 'rejected',
            'reject_date': fields.Datetime.now(),
            'notes': self.notes or '',
        }
        if self.attachment:
            approval_vals['attachment'] = self.attachment
            approval_vals['attachment_filename'] = self.attachment_filename or 'reject_attachment.pdf'
        approval.write(approval_vals)

        if self.attachment:
            self.env['ir.attachment'].create({
                'name': self.attachment_filename or 'reject_attachment.pdf',
                'datas': self.attachment,
                'res_model': 'rental.asset.request.header',
                'res_id': request.id,
                'type': 'binary',
            })
            
        # if not previous_approval:
        #     all_approval = request.approval_line_ids.filtered(lambda x: x.state == 'waiting')
        #     for approval_line in all_approval:
        #         approval_line.write({'state': 'rejected', 'reject_date': fields.Datetime.now()})
        #     request.state = 'rejected'
        #     return
        # # Hanya 1 level di bawahnya yang dikembalikan ke waiting
        # user_level = approval.level
        # immediate_previous = previous_approval.filtered(
        #     lambda x: x.level == str(int(user_level) - 1)
        # )
        # if immediate_previous:
        #     immediate_previous.write({'state': 'waiting', 'approve_date': False})

        # # Hanya jika semua reject, state baru rejected
        # if all(a.state == 'rejected' for a in request.approval_line_ids):
        #     request.state = 'rejected'
        request.state = 'rejected'
        # approval selanjutnya di set ke inactive
        next_approval = request.approval_line_ids.filtered(
            lambda x: x.state == 'waiting' and x.is_active
        )
        if next_approval:
            next_approval.write({'state': '', 'reject_date': False, 'approve_date': False, 'is_active': False})

        return {'type': 'ir.actions.act_window_close'}
