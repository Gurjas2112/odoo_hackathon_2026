from odoo import http
from odoo.http import request
import json


class TransitOpsController(http.Controller):
    """REST API endpoints for TransitOps."""

    @http.route('/api/transit/vehicles', type='jsonrpc', auth='user', methods=['POST'])
    def get_vehicles(self, **kwargs):
        """List all vehicles with status counts."""
        vehicles = request.env['transit.vehicle'].search([])
        return {
            'total': len(vehicles),
            'by_status': {
                'available': len(vehicles.filtered(lambda v: v.status == 'available')),
                'on_trip': len(vehicles.filtered(lambda v: v.status == 'on_trip')),
                'in_shop': len(vehicles.filtered(lambda v: v.status == 'in_shop')),
                'retired': len(vehicles.filtered(lambda v: v.status == 'retired')),
            },
            'vehicles': [{
                'id': v.id,
                'name': v.name,
                'registration': v.registration_number,
                'type': v.vehicle_type,
                'capacity': v.max_load_capacity,
                'odometer': v.odometer,
                'status': v.status,
            } for v in vehicles],
        }

    @http.route('/api/transit/dashboard', type='jsonrpc', auth='user', methods=['POST'])
    def get_dashboard(self, **kwargs):
        """Dashboard KPIs — PS §3.2."""
        Vehicle = request.env['transit.vehicle']
        Driver = request.env['transit.driver']
        Trip = request.env['transit.trip']

        all_vehicles = Vehicle.search([('status', '!=', 'retired')])
        active_vehicles = len(all_vehicles)
        available = len(all_vehicles.filtered(lambda v: v.status == 'available'))
        in_maint = len(all_vehicles.filtered(lambda v: v.status == 'in_shop'))
        on_trip_v = len(all_vehicles.filtered(lambda v: v.status == 'on_trip'))

        active_trips = Trip.search_count([('state', '=', 'dispatched')])
        pending_trips = Trip.search_count([('state', '=', 'draft')])
        drivers_on_duty = Driver.search_count([('status', '=', 'on_trip')])

        utilisation = (on_trip_v / active_vehicles * 100) if active_vehicles else 0

        return {
            'active_vehicles': active_vehicles,
            'available_vehicles': available,
            'in_maintenance': in_maint,
            'active_trips': active_trips,
            'pending_trips': pending_trips,
            'drivers_on_duty': drivers_on_duty,
            'fleet_utilisation': round(utilisation, 1),
        }
