from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class RentalAmortizationHeader(models.Model):
    _name = 'rental.amortization.header'
    _description = 'Rental Amortization Header'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, default='New')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self._default_currency_id(),
    )
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    rental_asset_Id = fields.Many2one(
        'rental.asset.request.header',
        string='Rental Request',
        required=True,
    )
    amount = fields.Float(string='Amount', required=True)
    annual_rate = fields.Float(string='Annual Rate', required=True, digits=(16, 9))
    term = fields.Integer(string='Term in Years', required=True)
    total_month = fields.Integer(
        string='Number of Months',
        compute='_compute_total_month',
        store=True,
    )
    monthly_rate = fields.Float(
        string='Monthly Rate',
        compute='_compute_monthly_rate',
        store=True,
        digits=(16, 9),
    )
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(
        string='End Date',
        compute='_compute_end_date',
        store=True,
    )
    status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        required=True,
    )
    notes = fields.Text(string='Notes')
    monthly_payment = fields.Float(
        string='Monthly Payment',
        compute='_compute_monthly_payment',
        store=True,
    )
    created_at = fields.Date(
        string='Created At',
        default=fields.Date.context_today,
        readonly=True,
    )

    rental_amortization_detail_ids = fields.One2many(
        'rental.amortization.detail',
        'rental_amortization_header_id',
        string='Amortization Lines',
    )

    journal_id = fields.Many2one(
        'account.journal',
        string='Vendor Bill Journal',
        domain="[('type', 'in', ('purchase', 'purchase_refund'))]",
        required=True,
    )

    lease_payable_account_id = fields.Many2one(
        'account.account',
        string='Lease Payable Account',
        required=True,
    )

    interest_expense_account_id = fields.Many2one(
        'account.account',
        string='Interest Expense Account',
        required=True,
    )

    lease_ap_account_id = fields.Many2one(
        'account.account',
        string='Lease Account Payable',
        required=True,
    )

    @api.model
    def _default_currency_id(self):
        usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        return usd or self.env.company.currency_id

    @api.depends('term')
    def _compute_total_month(self):
        for rec in self:
            if rec.term:
                rec.total_month = 12 * rec.term
            else:
                rec.total_month = 0

    @api.depends('annual_rate')
    def _compute_monthly_rate(self):
        for rec in self:
            if rec.annual_rate:
                rec.monthly_rate = rec.annual_rate / 12
            else:
                rec.monthly_rate = 0.0

    @api.depends('start_date', 'total_month')
    def _compute_end_date(self):
        for rec in self:
            if rec.start_date and rec.total_month:
                rec.end_date = rec.start_date + relativedelta(months=rec.total_month)
            else:
                rec.end_date = False

    @api.depends('amount', 'monthly_rate', 'total_month')
    def _compute_monthly_payment(self):
        for rec in self:
            if rec.amount and rec.monthly_rate and rec.total_month:
                # Standard annuity formula:
                # A = P * [ r * (1 + r)^n ] / [ (1 + r)^n - 1 ]
                # rec.monthly_payment = rec.amount * (rec.monthly_rate * (1 + rec.monthly_rate) ** rec.total_month) / ((1 + rec.monthly_rate) ** rec.total_month - 1)
                r = rec.monthly_rate
                n = rec.total_month
                factor = (1 + r) ** n
                rec.monthly_payment = rec.amount * (r * factor) / (factor - 1)
            else:
                rec.monthly_payment = 0.0

    def _generate_amortization_lines(self):
        for rec in self:
            rec.rental_amortization_detail_ids.unlink()

            if not (
                rec.amount
                and rec.monthly_rate
                and rec.total_month
                and rec.monthly_payment
                and rec.start_date
            ):
                continue

            balance = rec.amount
            payment_date = rec.start_date

            for idx in range(1, rec.total_month + 1):
                interest_amount = balance * rec.monthly_rate
                principal_amount = rec.monthly_payment - interest_amount
                remaining_balance = balance - principal_amount

                self.env['rental.amortization.detail'].create({
                    'rental_amortization_header_id': rec.id,
                    'payment_date': payment_date,
                    'payment_amount': rec.monthly_payment,
                    'interest_rate': rec.monthly_rate,
                    'interest_amount': interest_amount,
                    'principal_amount': principal_amount,
                    'net_depreciation_amount': principal_amount,
                    'remaining_balance': max(remaining_balance, 0.0),
                    'installment_number': idx,
                    'installment_total': rec.total_month,
                })

                balance = remaining_balance
                payment_date = payment_date + relativedelta(months=1)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = 'New'
        records = super(RentalAmortizationHeader, self).create(vals_list)
        for record in records:
            if record.name == 'New':
                year = fields.Date.today().strftime('%Y')
                record.name = f"AMORT/{year}/{record.id}"
            record._generate_amortization_lines()
        return records

    def write(self, vals):
        res = super(RentalAmortizationHeader, self).write(vals)
        self._generate_amortization_lines()
        return res


    def action_confirm(self):
        for rec in self:
            rec.status = 'confirmed'
            rec._generate_amortization_lines()
        return True

    def action_generate_schedule(self):
        for rec in self:
            rec._generate_amortization_lines()
        return True

    def action_done(self):
        for rec in self:
            rec.status = 'done'
        return True

    def action_create_vendor_bills(self):
        """Create draft Vendor Bills (with invoice lines) for unpaid monthly amortization lines."""
        Move = self.env['account.move']
        for rec in self:
            if not (rec.journal_id and rec.lease_payable_account_id and rec.interest_expense_account_id):
                continue

            # ensure installments have numbers
            for idx, line in enumerate(rec.rental_amortization_detail_ids.sorted('payment_date'), start=1):
                if not line.installment_number or line.installment_total != rec.total_month:
                    line.write({
                        'installment_number': idx,
                        'installment_total': rec.total_month,
                    })

            for line in rec.rental_amortization_detail_ids:
                if line.move_id:
                    continue

                currency = rec.currency_id or rec.company_id.currency_id
                principal = currency.round(line.principal_amount)
                interest = currency.round(line.interest_amount)
                total = currency.round(principal + interest)
                ref = f"{rec.name} - {line.installment_number}/{line.installment_total}"

                move_vals = {
                    'move_type': 'in_invoice',
                    'partner_id': rec.partner_id.id,
                    'invoice_date': line.payment_date or fields.Date.context_today(self),
                    'journal_id': rec.journal_id.id,
                    'ref': ref,
                    'currency_id': rec.currency_id.id,
                    'invoice_line_ids': [
                        # Principal portion
                        (0, 0, {
                            'name': ref,
                            'account_id': rec.lease_payable_account_id.id,
                            'quantity': 1.0,
                            'price_unit': principal,
                        }),
                        # Interest portion
                        (0, 0, {
                            'name': ref,
                            'account_id': rec.interest_expense_account_id.id,
                            'quantity': 1.0,
                            'price_unit': interest,
                        }),
                    ],
                }
                move = Move.create(move_vals)
                # Keep as draft (do not post automatically)
                line.move_id = move.id

    def cron_create_vendor_bills(self):
        """Scheduler: create draft Journal Entries for due amortization lines."""
        today = fields.Date.today()
        headers = self.search([('status', 'in', ('confirmed', 'done'))])
        for rec in headers:
            # Only process lines up to today
            due_lines = rec.rental_amortization_detail_ids.filtered(
                lambda l: l.payment_date and l.payment_date <= today and not l.move_id
            )
            if not due_lines:
                continue

            rec.action_create_vendor_bills()
