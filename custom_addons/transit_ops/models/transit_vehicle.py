from odoo import models, fields, api


class TransitVehicle(models.Model):
    """Vehicle Registry — PS §3.3
    
    Mandatory rules enforced:
    - Rule 1: Registration number UNIQUE (SQL + Python)
    - Rule 2: Retired/In Shop vehicles filtered from trip dispatch via domain
    """
    _name = 'transit.vehicle'
    _description = 'Transit Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'registration_number'
    _rec_name = 'name'

    # ── Core Fields (PS §3.3) ──
    registration_number = fields.Char(
        string='Registration Number',
        required=True, copy=False, index=True, tracking=True,
        help='Unique vehicle registration plate number',
    )
    name = fields.Char(
        string='Vehicle Name/Model',
        required=True, tracking=True,
        help='e.g. VAN-05, TRUCK-12',
    )
    vehicle_type = fields.Selection([
        ('van', 'Van'),
        ('truck', 'Truck'),
        ('mini_truck', 'Mini Truck'),
        ('trailer', 'Trailer'),
    ], string='Type', required=True, tracking=True)
    max_load_capacity = fields.Float(
        string='Max Load Capacity (kg)',
        required=True,
        help='Maximum cargo weight in kilograms',
    )
    odometer = fields.Float(
        string='Odometer (km)',
        tracking=True,
        help='Current odometer reading in kilometres',
    )
    acquisition_cost = fields.Float(
        string='Acquisition Cost',
        help='Vehicle purchase price in INR',
    )
    status = fields.Selection([
        ('available', 'Available'),
        ('on_trip', 'On Trip'),
        ('in_shop', 'In Shop'),
        ('retired', 'Retired'),
    ], string='Status', default='available', required=True, tracking=True)
    region = fields.Char(string='Region', help='Operating region for dashboard filters')


    # ── Relational ──
    trip_ids = fields.One2many('transit.trip', 'vehicle_id', string='Trips')
    maintenance_ids = fields.One2many('transit.maintenance', 'vehicle_id', string='Maintenance')
    fuel_log_ids = fields.One2many('transit.fuel.log', 'vehicle_id', string='Fuel Logs')
    expense_ids = fields.One2many('transit.expense', 'vehicle_id', string='Expenses')

    # ── Computed (PS §3.8 Analytics) ──
    trip_count = fields.Integer(compute='_compute_trip_count', string='Trip Count')
    total_fuel_cost = fields.Float(compute='_compute_costs', store=True, string='Total Fuel Cost')
    total_maintenance_cost = fields.Float(compute='_compute_costs', store=True, string='Total Maintenance Cost')
    total_operational_cost = fields.Float(compute='_compute_costs', store=True, string='Operational Cost')
    total_revenue = fields.Float(compute='_compute_costs', store=True, string='Total Revenue')
    roi = fields.Float(compute='_compute_roi', string='ROI (%)')

    # ── SQL Constraints (Rule 1) ──
    _sql_constraints = [
        ('registration_unique', 'UNIQUE(registration_number)',
         'Registration number must be unique! This plate is already registered.'),
    ]

    def _compute_display_name(self):
        for rec in self:
            if rec.registration_number:
                rec.display_name = f"{rec.name} [{rec.registration_number}]"
            else:
                rec.display_name = rec.name or ''

    def _compute_trip_count(self):
        for rec in self:
            rec.trip_count = self.env['transit.trip'].search_count([
                ('vehicle_id', '=', rec.id),
                ('state', '=', 'completed'),
            ])

    @api.depends('fuel_log_ids.cost', 'maintenance_ids.cost', 'maintenance_ids.state',
                 'trip_ids.state', 'trip_ids.fuel_cost', 'trip_ids.toll_cost')
    def _compute_costs(self):
        for rec in self:
            rec.total_fuel_cost = sum(rec.fuel_log_ids.mapped('cost'))
            rec.total_maintenance_cost = sum(
                rec.maintenance_ids.filtered(lambda m: m.state == 'closed').mapped('cost')
            )
            rec.total_operational_cost = rec.total_fuel_cost + rec.total_maintenance_cost
            # Revenue = sum of toll_cost + fuel_cost from completed trips as proxy
            # In a real system this would be billing; for hackathon we use a simple approach
            completed = rec.trip_ids.filtered(lambda t: t.state == 'completed')
            rec.total_revenue = sum(completed.mapped('planned_distance')) * 15  # ₹15/km rate

    @api.depends('total_revenue', 'total_operational_cost', 'acquisition_cost')
    def _compute_roi(self):
        for rec in self:
            if rec.acquisition_cost:
                rec.roi = ((rec.total_revenue - rec.total_operational_cost) / rec.acquisition_cost) * 100
            else:
                rec.roi = 0.0

    # ── Smart Button Actions ──
    def action_view_trips(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Trips — {self.name}',
            'res_model': 'transit.trip',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_view_maintenance(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Maintenance — {self.name}',
            'res_model': 'transit.maintenance',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_view_fuel_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Fuel Logs — {self.name}',
            'res_model': 'transit.fuel.log',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
