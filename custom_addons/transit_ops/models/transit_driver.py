from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class TransitDriver(models.Model):
    """Driver Management — PS §3.4
    
    Mandatory rules enforced:
    - Rule 3: Expired licence / Suspended → blocked from trip assignment
    - Computed licence_status for expiring-soon alerts
    """
    _name = 'transit.driver'
    _description = 'Driver'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # ── Core Fields (PS §3.4) ──
    name = fields.Char(string='Driver Name', required=True, tracking=True)
    license_number = fields.Char(
        string='License Number', required=True, tracking=True,
        help='Driving licence number',
    )
    license_category = fields.Selection([
        ('lmv', 'LMV — Light Motor Vehicle'),
        ('hmv', 'HMV — Heavy Motor Vehicle'),
        ('mcwg', 'MCWG — Motorcycle With Gear'),
        ('trans', 'TRANS — Transport'),
    ], string='License Category', required=True)
    license_expiry = fields.Date(
        string='License Expiry Date',
        required=True, tracking=True,
    )
    contact_number = fields.Char(string='Contact Number')
    safety_score = fields.Float(
        string='Safety Score',
        default=100.0,
        help='Driver safety rating 0-100',
    )
    status = fields.Selection([
        ('available', 'Available'),
        ('on_trip', 'On Trip'),
        ('off_duty', 'Off Duty'),
        ('suspended', 'Suspended'),
    ], string='Status', default='available', required=True, tracking=True)

    # ── Computed Fields ──
    license_status = fields.Selection([
        ('valid', 'Valid'),
        ('expiring', 'Expiring Soon'),
        ('expired', 'Expired'),
    ], string='License Status', compute='_compute_license_status', store=True)

    is_eligible = fields.Boolean(
        string='Eligible for Dispatch',
        compute='_compute_is_eligible', store=True,
        help='Available + valid licence = eligible',
    )

    trip_count = fields.Integer(compute='_compute_trip_count', string='Completed Trips')

    # ── Relational ──
    trip_ids = fields.One2many('transit.trip', 'driver_id', string='Trips')

    @api.depends('license_expiry')
    def _compute_license_status(self):
        today = fields.Date.today()
        for rec in self:
            if not rec.license_expiry:
                rec.license_status = 'expired'
            elif rec.license_expiry < today:
                rec.license_status = 'expired'
            elif rec.license_expiry < today + relativedelta(days=30):
                rec.license_status = 'expiring'
            else:
                rec.license_status = 'valid'

    @api.depends('status', 'license_status')
    def _compute_is_eligible(self):
        for rec in self:
            rec.is_eligible = (
                rec.status == 'available'
                and rec.license_status != 'expired'
            )

    def _compute_trip_count(self):
        for rec in self:
            rec.trip_count = self.env['transit.trip'].search_count([
                ('driver_id', '=', rec.id),
                ('state', '=', 'completed'),
            ])

    # ── Status Actions ──
    def action_set_available(self):
        for rec in self:
            rec.status = 'available'

    def action_set_off_duty(self):
        for rec in self:
            rec.status = 'off_duty'

    def action_suspend(self):
        for rec in self:
            rec.status = 'suspended'

    # ── Smart Button ──
    def action_view_trips(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Trips — {self.name}',
            'res_model': 'transit.trip',
            'view_mode': 'list,form',
            'domain': [('driver_id', '=', self.id)],
            'context': {'default_driver_id': self.id},
        }
    @api.model
    def _cron_check_license_expiry(self):
        today = fields.Date.today()
        warning_date = today + relativedelta(days=30)
        expiring = self.search([('license_expiry', '<=', warning_date), ('license_status', '!=', 'expired')])
        for driver in expiring:
            driver.message_post(body='CRITICAL: Driver license is expiring soon or has already expired!', subject='License Expiry Alert')
        # Force recompute
        self.search([])._compute_license_status()
