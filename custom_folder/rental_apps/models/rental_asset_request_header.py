from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class RentalAssetRequestHeader(models.Model):
    _name = 'rental.asset.request.header'
    _description = 'Rental Asset Request Header'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(
        string="Request Description",
        required=True,
        copy=False,
        default='New'
    )

    date = fields.Date(
        string="Date",
        default=fields.Date.today
    )

    partner_id = fields.Many2one(
        'res.partner',
        string="Customer/Partner"
    )

    request_type = fields.Selection([
        ('replacement_temp', 'Replacement Car Temporary'),
        ('replacement_new', 'Replacement Car New'),
    ], string="Type of Request")

    required_date = fields.Date(string="Required Date")

    state = fields.Selection([
        ('new', 'New'),
        ('draft', 'Draft'),
        ('waiting', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='new', tracking=True)

    line_ids = fields.One2many(
        'rental.asset.request.line',
        'request_id',
        string="Line Items"
    )

    approval_line_ids = fields.One2many(
        'rental.asset.request.approval',
        'request_id',
        string="Approval Lines",
        domain=[('state', '!=', '')]
    )

    total_qty = fields.Integer(
        compute="_compute_total_qty",
        store=True
    )
    
    notes = fields.Text(string="Notes")
    attachment = fields.Binary(string="Attachment", attachment=True)
    attachment_filename = fields.Char(string="Attachment Filename")

    can_approve = fields.Boolean(
        compute="_compute_can_approve",
        help="True if current user has a waiting approval line for this request"
    )

    can_reject = fields.Boolean(
        compute="_compute_can_reject",
        help="True if current user can reject this request"
    )

    @api.depends('approval_line_ids', 'approval_line_ids.state', 'approval_line_ids.user_id', 'state')
    def _compute_can_approve(self):
        for rec in self:
            rec.can_approve = False
            if rec.state != 'waiting':
                continue
            # User harus punya approval line dengan state waiting
            waiting_for_user = rec.approval_line_ids.filtered(
                lambda x: x.user_id == rec.env.user and x.state == 'waiting' and x.is_active
            )
            if not waiting_for_user:
                continue
            # Cek jika level sebelumnya belum di approve maka tidak bisa approve
            user_level = waiting_for_user.level
            previous_approval = rec.approval_line_ids.filtered(
                lambda x: x.level < user_level and x.is_active
            )
            if previous_approval.filtered(lambda x: x.state != 'approved'):
                continue
            rec.can_approve = True

    @api.depends('approval_line_ids', 'approval_line_ids.state', 'approval_line_ids.user_id', 'state')
    def _compute_can_reject(self):
        for rec in self:
            rec.can_reject = False
            if rec.state != 'waiting':
                continue
            # User harus punya approval line dengan state waiting
            waiting_for_user = rec.approval_line_ids.filtered(
                lambda x: x.user_id == rec.env.user and x.state == 'waiting' and x.is_active
            )
            if not waiting_for_user:
                continue
            # Cek jika level sebelumnya belum di approve maka tidak bisa reject
            user_level = waiting_for_user.level
            previous_approval = rec.approval_line_ids.filtered(
                lambda x: x.level < user_level and x.is_active
            )
            if previous_approval.filtered(lambda x: x.state != 'approved'):
                continue
            rec.can_reject = True
            

    @api.depends('line_ids.quantity')
    def _compute_total_qty(self):
        for rec in self:
            rec.total_qty = sum(rec.line_ids.mapped('quantity'))

    @api.onchange('line_ids')
    def _onchange_line_ids_set_line_numbers(self):
        """Auto set nomor urut 1,2,3,... di UI saat user tambah/edit line."""
        for rec in self:
            for idx, line in enumerate(rec.line_ids, start=1):
                line.line_number = idx

    def action_submit(self):
        for rec in self:
            rec.state = 'waiting' 
            rec._generate_approval_matrix() 
    
    def action_draft(self):
        for rec in self:
            if rec.create_uid != self.env.user:
                raise UserError("Only the request creator can set this record to Draft.")
            rec.state = 'draft'
            
    def _generate_approval_matrix(self):
        # self.approval_line_ids.unlink()
        # Nonaktifkan approval lama (riwayat tetap), buat approval baru untuk submit ini
        self.approval_line_ids.write({'is_active': False})

        brands = self.line_ids.mapped('brand_id.name')
        total_qty = self.total_qty

        for rec in self:

            # Honda group
            if any(b in ['Honda', 'Toyota', 'Mitsubishi', 'Mazda'] for b in brands):
                if total_qty <= 2:
                    rec._create_approval('1')
                else:
                    rec._create_approval('1')
                    rec._create_approval('2')
                    rec._create_approval('3')

            # BMW group
            elif any(b in ['BMW', 'Mercedes'] for b in brands):
                if total_qty <= 2:
                    rec._create_approval('1')
                    rec._create_approval('2')
                else:
                    rec._create_approval('1')
                    rec._create_approval('2')
                    rec._create_approval('3')


    def _create_approval(self, level):

        config = self.env['rental.approval.config'].search([
            ('level', '=', level)
        ], limit=1)

        if not config:
            return

        self.env['rental.asset.request.approval'].create({
            'request_id': self.id,
            'level': level,
            'user_id': config.user_id.id,
        })

        # Notifikasi Odoo ke user yang ditugaskan approval: chatter + bell (inbox)
        if config.user_id.partner_id:
            partner_id = config.user_id.partner_id.id
            self.message_subscribe(partner_ids=[partner_id])
            body = (
                f"Approval Level {level} has been assigned to <b>%s</b>. Your action is required."
                % config.user_id.name
            )
            self.message_post(
                body=body,
                subtype_xmlid='mail.mt_note',
            )
            # Agar muncul di bell/notifikasi user (inbox)
            self.message_notify(
                subject=f"Approval Level {level} assigned: {self.name}",
                body=body,
                partner_ids=[partner_id],
            )
        
    def action_approve(self):
        approval = self.approval_line_ids.filtered(
            lambda x: x.user_id == self.env.user and x.state == 'waiting' and x.is_active
        )
        if not approval:
            raise UserError("You have no pending approval to approve")
        approval = approval[:1]

        # jika approval level sebelumnya belum di approve maka tidak bisa approve
        previous_approval = self.approval_line_ids.filtered(
            lambda x: x.is_active and x.level < approval.level
        )
        if previous_approval.filtered(lambda x: x.state != 'approved'):
            raise ValidationError("Previous approval level is not approved")
        
        if approval:
            approval.state = 'approved'
            approval.approve_date = fields.Datetime.now()

        active_approvals = self.approval_line_ids.filtered(lambda a: a.is_active)
        if active_approvals and all(a.state == 'approved' for a in active_approvals):
            self.state = 'approved'
            
    def action_reject_wizard(self):
        """Buka wizard reject dengan popup untuk isi notes dan upload file"""
        self.ensure_one()
        return {
            'name': 'Reject Request',
            'type': 'ir.actions.act_window',
            'res_model': 'rental.asset.request.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_request_id': self.id,
                'active_id': self.id,
                'active_model': 'rental.asset.request.header',
            },
        }

    def action_reject(self):
        approval = self.approval_line_ids.filtered(
            lambda x: x.user_id == self.env.user and x.state == 'waiting' and x.is_active
        )
        if not approval:
            raise ValidationError("You have no pending approval to reject")
        previous_approval = self.approval_line_ids.filtered(
            lambda x: x.level < approval.level and x.is_active
        )
        if previous_approval.filtered(lambda x: x.state != 'approved' and x.is_active):
            raise ValidationError("Previous approval level is not approved")
        approval.state = 'rejected'
        approval.reject_date = fields.Datetime.now()
        user_level = approval.level
        if not previous_approval:
            all_approval = self.approval_line_ids.filtered(lambda x: x.state == 'waiting' and x.is_active)
            for approval in all_approval:
                approval.write({'state': 'rejected', 'reject_date': fields.Datetime.now()})
            self.state = 'rejected'
            return
        # Hanya 1 level di bawahnya yang dikembalikan ke waiting
        immediate_previous = previous_approval.filtered(
            lambda x: x.level == str(int(user_level) - 1)
        )
        if immediate_previous:
            immediate_previous.write({'state': 'waiting', 'approve_date': False})
        # Hanya jika semua reject, state baru rejected
        if all(a.state == 'rejected' and a.is_active for a in self.approval_line_ids):
            self.state = 'rejected'
    
    def _send_approval_reminder_email(self, requests):
        """Send approval reminder email to approvers with waiting status."""
        template = self.env.ref(
            'rental_apps.mail_template_approval_reminder',
            raise_if_not_found=False
        )
        if not template:
            return
        for rec in requests:
            waiting = rec.approval_line_ids.filtered(lambda x: x.state == 'waiting' and x.is_active)
            for approval in waiting:
                if approval.user_id.partner_id.email:
                    template.with_context(
                        approver_name=approval.user_id.name,
                    ).send_mail(
                        # dikirim ke template email.xml sebagai object rec.id ini berisi record/data dri data yg sedang di akses
                        rec.id,
                        force_send=True,
                        email_values={
                            'email_to': approval.user_id.partner_id.email,
                        },
                    )

    def action_send_approval_reminder(self):
        """Send reminder email for current record(s) only (button click)."""
        self._send_approval_reminder_email(self)

    def cron_send_approval_reminder(self):
        """Send reminder email to all waiting requests (scheduled action)."""
        requests = self.search([('state', '=', 'waiting') and ('is_active', '=', True)])
        self._send_approval_reminder_email(requests)
        
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
