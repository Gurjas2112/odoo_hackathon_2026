from odoo import models, fields, api
from odoo.exceptions import UserError


class TransitCompleteTripWizard(models.TransientModel):
    """Wizard for completing a trip — collects final odometer, fuel, and costs.
    
    Launched from the Trip form when clicking 'Complete Trip'.
    """
    _name = 'transit.complete.trip.wizard'
    _description = 'Complete Trip Wizard'

    trip_id = fields.Many2one('transit.trip', string='Trip', required=True)
    vehicle_name = fields.Char(related='trip_id.vehicle_id.name', readonly=True)
    driver_name = fields.Char(related='trip_id.driver_id.name', readonly=True)
    current_odometer = fields.Float(related='trip_id.vehicle_id.odometer', readonly=True)

    final_odometer = fields.Float(
        string='Final Odometer (km)', required=True,
        help='Must be greater than or equal to current odometer reading',
    )
    fuel_consumed = fields.Float(string='Fuel Consumed (L)', required=True)
    fuel_cost = fields.Float(string='Fuel Cost (₹)', required=True)
    toll_cost = fields.Float(string='Toll/Misc Cost (₹)')

    def action_complete(self):
        """Write completion data to trip and execute action_complete."""
        self.ensure_one()
        trip = self.trip_id

        if self.final_odometer < self.current_odometer:
            raise UserError(
                f"Final odometer ({self.final_odometer} km) cannot be less than "
                f"current reading ({self.current_odometer} km)."
            )

        trip.write({
            'final_odometer': self.final_odometer,
            'fuel_consumed': self.fuel_consumed,
            'fuel_cost': self.fuel_cost,
            'toll_cost': self.toll_cost,
        })
        trip.action_complete()

        return {'type': 'ir.actions.act_window_close'}
