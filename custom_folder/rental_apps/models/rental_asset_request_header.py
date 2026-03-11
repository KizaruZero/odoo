from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class RentalAssetRequestHeader(models.Model):
    _name = 'rental.asset.request.header'
    _description = 'Rental Asset Request Header'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    request_number = fields.Char(
        string="Request Number",
        required=True,
        copy=False,
        readonly=True,
        default="/"
    )
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
    
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if not rec.request_number or rec.request_number == "/":
                year = (rec.date and rec.date.year) or fields.Date.today().year
                rec.request_number = f"RENT/{year}/{rec.id}"
        return records

    @api.depends('approval_line_ids', 'approval_line_ids.state', 'approval_line_ids.user_id', 'state')
    def _compute_can_approve(self):
        for rec in self:
            rec.can_approve = False
            if rec.state != 'waiting':
                continue
            Delegation = rec.env['rental.delegate.approval']
            delegator_delegations = Delegation.search([
                ('approval_id.user_id', '=', rec.env.user.id),
                ('delegate_date', '<=', fields.Date.today()),
                ('delegate_maximum_date', '>=', fields.Date.today()),
            ])

            delegate_delegations = Delegation.search([
                ('delegate_id', '=', rec.env.user.id),
                ('delegate_date', '<=', fields.Date.today()),
                ('delegate_maximum_date', '>=', fields.Date.today()),
            ])
            # User harus punya approval line dengan state waiting
            waiting_for_user = rec.approval_line_ids.filtered(
                lambda x: x.user_id == rec.env.user and x.state == 'waiting' and x.is_active
            )
            if not waiting_for_user and delegate_delegations:
                original_users = delegate_delegations.mapped('approval_id.user_id')
                waiting_for_user = rec.approval_line_ids.filtered(
                    lambda x: x.user_id in original_users and x.state == 'waiting' and x.is_active
                )
            if not waiting_for_user:
                continue
            # Cek jika level sebelumnya belum di approve maka tidak bisa approve
            user_level = waiting_for_user[:1].level
            previous_approval = rec.approval_line_ids.filtered(
                lambda x: x.level < user_level and x.is_active
            )
            if previous_approval.filtered(lambda x: x.state != 'approved'):
                continue
            
            if delegator_delegations:
                rec.can_approve = False
            else:
                rec.can_approve = True

    @api.depends('approval_line_ids', 'approval_line_ids.state', 'approval_line_ids.user_id', 'state')
    def _compute_can_reject(self):
        for rec in self:
            rec.can_reject = False
            if rec.state != 'waiting':
                continue
            Delegation = rec.env['rental.delegate.approval']
            delegator_delegations = Delegation.search([
                ('approval_id.user_id', '=', rec.env.user.id),
                ('delegate_date', '<=', fields.Date.today()),
                ('delegate_maximum_date', '>=', fields.Date.today()),
            ])

            delegate_delegations = Delegation.search([
                ('delegate_id', '=', rec.env.user.id),
                ('delegate_date', '<=', fields.Date.today()),
                ('delegate_maximum_date', '>=', fields.Date.today()),
            ])

            waiting_for_user = rec.approval_line_ids.filtered(
                lambda x: x.user_id == rec.env.user and x.state == 'waiting' and x.is_active
            )

            if not waiting_for_user and delegate_delegations:
                original_users = delegate_delegations.mapped('approval_id.user_id')
                waiting_for_user = rec.approval_line_ids.filtered(
                    lambda x: x.user_id in original_users and x.state == 'waiting' and x.is_active
                )

            if not waiting_for_user:
                continue

            user_level = waiting_for_user[:1].level
            previous_approval = rec.approval_line_ids.filtered(
                lambda x: x.level < user_level and x.is_active
            )
            if previous_approval.filtered(lambda x: x.state != 'approved'):
                continue

            if delegator_delegations:
                rec.can_reject = False
            else:
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
    # Nonaktifkan approval lama (riwayat tetap)
        self.approval_line_ids.write({'is_active': False})

        for rec in self:
            brands = rec.line_ids.mapped('brand_id')
            total_qty = rec.total_qty

            if not brands or not total_qty:
                continue

            rules = self.env['rental.asset.approval.config'].search([
                ('brand_ids', 'in', brands.ids),
                ('min_qty', '<=', total_qty),
                '|',
                    ('max_qty', '>=', total_qty),
                    ('max_qty', '=', 0),  # 0 = unlimited
            ])

            if not rules:
                rec._create_approval('1')
                continue

            # Ambil semua level dari rules, urutkan berdasarkan field level ('1','2','3',...)
            level_configs = rules.mapped('level_ids')
            level_configs = level_configs.sorted(key=lambda l: int(l.level))

            # Hilangkan duplikat level kalau rule-nya overlap
            seen_levels = set()
            for cfg in level_configs:
                if cfg.level in seen_levels:
                    continue
                seen_levels.add(cfg.level)
                rec._create_approval(cfg.level)


    def _create_approval(self, level):

        config = self.env['rental.approval.config'].search([
            ('level', '=', level)
        ], limit=1)

        if not config:
            return

        # Jika ada delegasi aktif untuk config ini, assign ke delegate;
        # kalau tidak ada, assign ke user asli di config.
        Delegation = self.env['rental.delegate.approval']
        delegation = Delegation.search([
            ('approval_id', '=', config.id),
            ('delegate_date', '<=', fields.Date.today()),
            ('delegate_maximum_date', '>=', fields.Date.today()),
        ], limit=1)

        target_user = delegation.delegate_id or config.user_id

        approval = self.env['rental.asset.request.approval'].create({
            'request_id': self.id,
            'level': level,
            'user_id': target_user.id,
        })

        # Notifikasi Odoo ke user yang ditugaskan approval: chatter + bell (inbox)
        if target_user.partner_id:
            partner_id = target_user.partner_id.id
            self.message_subscribe(partner_ids=[partner_id])
            body = (
                f"Approval Level {level} has been assigned to <b>%s</b>. Your action is required."
                % target_user.name
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
        # Cari approval line untuk user yang login
        approval = self.approval_line_ids.filtered(
            lambda x: x.user_id == self.env.user and x.state == 'waiting' and x.is_active
        )

        # Jika tidak ada, cek apakah user adalah delegate aktif dari approver asli
        if not approval:
            Delegation = self.env['rental.delegate.approval']
            delegate_delegations = Delegation.search([
                ('delegate_id', '=', self.env.user.id),
                ('delegate_date', '<=', fields.Date.today()),
                ('delegate_maximum_date', '>=', fields.Date.today()),
            ])
            if delegate_delegations:
                original_users = delegate_delegations.mapped('approval_id.user_id')
                approval = self.approval_line_ids.filtered(
                    lambda x: x.user_id in original_users and x.state == 'waiting' and x.is_active
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
        # Cari approval line untuk user yang login
        approval = self.approval_line_ids.filtered(
            lambda x: x.user_id == self.env.user and x.state == 'waiting' and x.is_active
        )

        # Jika tidak ada, cek apakah user adalah delegate aktif dari approver asli
        if not approval:
            Delegation = self.env['rental.delegate.approval']
            delegate_delegations = Delegation.search([
                ('delegate_id', '=', self.env.user.id),
                ('delegate_date', '<=', fields.Date.today()),
                ('delegate_maximum_date', '>=', fields.Date.today()),
            ])
            if delegate_delegations:
                original_users = delegate_delegations.mapped('approval_id.user_id')
                approval = self.approval_line_ids.filtered(
                    lambda x: x.user_id in original_users and x.state == 'waiting' and x.is_active
                )

        if not approval:
            raise ValidationError("You have no pending approval to reject")

        approval = approval[:1]
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
