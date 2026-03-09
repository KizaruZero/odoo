from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class RentalAssetRequestApproval(models.Model):
    _name = 'rental.asset.request.approval'
    _description = 'Rental Asset Request Approval'

    request_id = fields.Many2one(
        'rental.asset.request.header',
        ondelete='cascade'
    )
    
    level = fields.Selection([
        ('1', 'L1 - Manager'),
        ('2', 'L2 - Sr. Manager'),
        ('3', 'L3 - Director'),
    ])

    user_id = fields.Many2one(
        'res.users',
        string="User"
    )

    state = fields.Selection([
        ('waiting', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('', '-'),
    ], default='waiting', tracking=True)
    
    approve_date = fields.Datetime(string="Approve Date")
    reject_date = fields.Datetime(string="Reject Date")
    notes = fields.Text(string="Notes")
    attachment = fields.Binary(string="Reject Attachment", attachment=True)
    attachment_filename = fields.Char(string="Attachment Filename")
    is_active = fields.Boolean(string="Is Active", default=True)

    def action_download_attachment(self):
        self.ensure_one()
        if not self.attachment:
            raise UserError("No attachment to download.")
        filename = (self.attachment_filename or "attachment").replace("/", "_")
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content?model={self._name}&id={self.id}&field=attachment&download=true&filename={filename}",
            "target": "self",
        }

    