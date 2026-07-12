from odoo import models, fields


class TransitFuelLog(models.Model):
    """Fuel Logs — PS §3.7
    
    Records fuel consumption per vehicle per trip.
    Auto-created on trip completion.
    """
    _name = 'transit.fuel.log'
    _description = 'Fuel Log'
    _order = 'date desc'

    vehicle_id = fields.Many2one(
        'transit.vehicle', string='Vehicle',
        required=True, index=True,
    )
    trip_id = fields.Many2one(
        'transit.trip', string='Trip',
        help='Linked trip (auto-set on trip completion)',
    )
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    liters = fields.Float(string='Liters', required=True)
    cost = fields.Float(string='Fuel Cost (₹)', required=True)

    # For easy display
    vehicle_name = fields.Char(related='vehicle_id.name', store=True, string='Vehicle Name')
