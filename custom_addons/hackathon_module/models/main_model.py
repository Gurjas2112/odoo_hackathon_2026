from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class HackathonRecord(models.Model):
    """Main model — RENAME this class and _name to match your problem domain.
    
    Quick rename guide:
        1. Change _name from 'hackathon.record' to 'your.domain.model'
        2. Change _description to match
        3. Update ir.model.access.csv (model_hackathon_record → model_your_domain_model)
        4. Update all XML refs
    """
    _name = 'hackathon.record'
    _description = 'Hackathon Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # =============================================
    # BASIC FIELDS
    # =============================================
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        help='The name or title of this record',
    )
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    date = fields.Date(
        string='Date',
        default=fields.Date.today,
        tracking=True,
    )
    amount = fields.Float(string='Amount', digits=(16, 2))
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], default='1', string='Priority')
    color = fields.Integer(string='Color Index')
    image = fields.Image(string='Image', max_width=256, max_height=256)

    # =============================================
    # STATE WORKFLOW
    # =============================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True, string='Status')

    # =============================================
    # RELATIONAL FIELDS
    # =============================================
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer/Contact',
        tracking=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='Responsible',
        default=lambda self: self.env.user,
        tracking=True,
    )
    tag_ids = fields.Many2many(
        'hackathon.tag',
        string='Tags',
    )
    line_ids = fields.One2many(
        'hackathon.record.line',
        'record_id',
        string='Lines',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )

    # =============================================
    # COMPUTED FIELDS
    # =============================================
    total_lines = fields.Integer(
        compute='_compute_total_lines',
        store=True,
        string='Total Lines',
    )
    total_amount = fields.Float(
        compute='_compute_total_amount',
        store=True,
        string='Total Amount',
    )

    @api.depends('line_ids')
    def _compute_total_lines(self):
        for record in self:
            record.total_lines = len(record.line_ids)

    @api.depends('line_ids.subtotal')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(record.line_ids.mapped('subtotal'))

    # =============================================
    # STATE TRANSITION METHODS
    # =============================================
    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError("Only draft records can be confirmed!")
            rec.state = 'confirmed'

    def action_start(self):
        for rec in self:
            rec.state = 'in_progress'

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    # =============================================
    # SMART BUTTON ACTIONS
    # =============================================
    def action_view_lines(self):
        """Smart button to view related lines."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lines',
            'res_model': 'hackathon.record.line',
            'view_mode': 'list,form',
            'domain': [('record_id', '=', self.id)],
            'context': {'default_record_id': self.id},
        }

    # =============================================
    # CONSTRAINTS
    # =============================================
    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount < 0:
                raise ValidationError("Amount cannot be negative!")

    # =============================================
    # ONCHANGE
    # =============================================
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Auto-fill fields when customer changes."""
        if self.partner_id:
            # Example: auto-assign the partner's salesperson
            if self.partner_id.user_id:
                self.user_id = self.partner_id.user_id


class HackathonRecordLine(models.Model):
    """Line model for One2many — RENAME to match your domain."""
    _name = 'hackathon.record.line'
    _description = 'Hackathon Record Line'
    _order = 'sequence, id'

    record_id = fields.Many2one(
        'hackathon.record',
        string='Parent Record',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Description', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_price = fields.Float(string='Unit Price')
    subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True,
    )

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price


class HackathonTag(models.Model):
    """Tag model for Many2many — RENAME to match your domain."""
    _name = 'hackathon.tag'
    _description = 'Tags'

    name = fields.Char(string='Tag Name', required=True)
    color = fields.Integer(string='Color')
