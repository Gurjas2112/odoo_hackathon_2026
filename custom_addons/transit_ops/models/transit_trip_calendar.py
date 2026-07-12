from odoo import models, fields, api

class TransitTrip(models.Model):
    _inherit = 'transit.trip'

    date_start = fields.Date(
        string='Scheduled Date',
        default=fields.Date.today,
        tracking=True,
        help="Date when the trip is scheduled to start."
    )

    def action_open_complete_wizard(self):
        self.ensure_one()
        return {
            'name': 'Complete Trip',
            'type': 'ir.actions.act_window',
            'res_model': 'transit.complete.trip.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_trip_id': self.id,
                'default_final_odometer': self.vehicle_id.odometer,
            }
        }
