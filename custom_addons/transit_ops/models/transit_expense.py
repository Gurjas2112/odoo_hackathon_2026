from odoo import models, fields, api


class TransitExpense(models.Model):
    """Expenses — PS §3.7
    
    Tracks operational expenses per trip/vehicle.
    Auto-computes total = fuel + toll + other + linked maintenance.
    """
    _name = 'transit.expense'
    _description = 'Expense'
    _order = 'create_date desc'

    trip_id = fields.Many2one('transit.trip', string='Trip')
    vehicle_id = fields.Many2one(
        'transit.vehicle', string='Vehicle',
        required=True, index=True,
    )
    fuel_cost = fields.Float(string='Fuel Cost (₹)')
    toll_cost = fields.Float(string='Toll Cost (₹)')
    other_cost = fields.Float(string='Other Cost (₹)')
    maintenance_cost = fields.Float(
        string='Maintenance Cost (₹)',
        compute='_compute_maintenance_cost', store=True,
        help='Auto-linked from closed maintenance records for this vehicle',
    )
    total = fields.Float(
        string='Total (₹)',
        compute='_compute_total', store=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string='Status', default='draft')
    date = fields.Date(string='Date', default=fields.Date.today)

    # Display helpers
    vehicle_name = fields.Char(related='vehicle_id.name', store=True)
    trip_name = fields.Char(related='trip_id.name', store=True)

    @api.depends('vehicle_id', 'vehicle_id.maintenance_ids.cost', 'vehicle_id.maintenance_ids.state')
    def _compute_maintenance_cost(self):
        for rec in self:
            if rec.vehicle_id:
                closed = rec.vehicle_id.maintenance_ids.filtered(lambda m: m.state == 'closed')
                rec.maintenance_cost = sum(closed.mapped('cost'))
            else:
                rec.maintenance_cost = 0

    @api.depends('fuel_cost', 'toll_cost', 'other_cost', 'maintenance_cost')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.fuel_cost + rec.toll_cost + rec.other_cost

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'
