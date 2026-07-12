from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from odoo import fields
from datetime import date, timedelta


class TestTransitOps(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create helper test records
        cls.vehicle_van = cls.env['transit.vehicle'].create({
            'name': 'Test Van',
            'registration_number': 'TEST-VAN-01',
            'vehicle_type': 'van',
            'max_load_capacity': 500.0,
            'odometer': 1000.0,
            'acquisition_cost': 500000.0,
            'status': 'available',
        })

        cls.driver_alex = cls.env['transit.driver'].create({
            'name': 'Alex Test',
            'license_number': 'LIC-12345',
            'license_category': 'lmv',
            'license_expiry': fields.Date.today() + timedelta(days=365),
            'status': 'available',
            'safety_score': 90.0,
        })

    def test_01_vehicle_registration_uniqueness(self):
        """Rule 1: The vehicle registration number must be unique."""
        with self.assertRaises(Exception):
            # Attempting to create a vehicle with the same registration number should raise an error
            self.env['transit.vehicle'].create({
                'name': 'Duplicate Van',
                'registration_number': 'TEST-VAN-01',
                'vehicle_type': 'van',
                'max_load_capacity': 400.0,
            })
            self.env.flush_all()

    def test_02_retired_in_shop_vehicle_dispatch(self):
        """Rule 2: Retired or In Shop vehicles must never be dispatched."""
        # 1. Test In Shop vehicle
        self.vehicle_van.status = 'in_shop'
        trip = self.env['transit.trip'].create({
            'source': 'Depot A',
            'destination': 'Hub B',
            'vehicle_id': self.vehicle_van.id,
            'driver_id': self.driver_alex.id,
            'cargo_weight': 100.0,
            'planned_distance': 50.0,
        })
        with self.assertRaises(UserError, msg="Should block dispatching an 'In Shop' vehicle"):
            trip.action_dispatch()

        # 2. Test Retired vehicle
        self.vehicle_van.status = 'retired'
        with self.assertRaises(UserError, msg="Should block dispatching a 'Retired' vehicle"):
            trip.action_dispatch()

    def test_03_driver_eligibility_checks(self):
        """Rule 3: Drivers with expired licenses or Suspended status cannot be assigned to trips."""
        # 1. Test Expired License
        self.vehicle_van.status = 'available'
        self.driver_alex.license_expiry = fields.Date.today() - timedelta(days=1)
        # Flush/recompute computed fields if needed, Odoo does it automatically in transaction
        self.driver_alex._compute_license_status()

        trip = self.env['transit.trip'].create({
            'source': 'Depot A',
            'destination': 'Hub B',
            'vehicle_id': self.vehicle_van.id,
            'driver_id': self.driver_alex.id,
            'cargo_weight': 100.0,
            'planned_distance': 50.0,
        })
        with self.assertRaises(UserError, msg="Should block dispatching an expired-license driver"):
            trip.action_dispatch()

        # 2. Test Suspended Driver
        self.driver_alex.license_expiry = fields.Date.today() + timedelta(days=365)
        self.driver_alex.status = 'suspended'
        with self.assertRaises(UserError, msg="Should block dispatching a suspended driver"):
            trip.action_dispatch()

    def test_04_double_booking_prevention(self):
        """Rule 4: A driver or vehicle already marked On Trip cannot be assigned to another trip."""
        # 1. Test Vehicle On Trip
        self.vehicle_van.status = 'on_trip'
        self.driver_alex.status = 'available'
        trip = self.env['transit.trip'].create({
            'source': 'Depot A',
            'destination': 'Hub B',
            'vehicle_id': self.vehicle_van.id,
            'driver_id': self.driver_alex.id,
            'cargo_weight': 100.0,
            'planned_distance': 50.0,
        })
        with self.assertRaises(UserError, msg="Should block dispatching an already On Trip vehicle"):
            trip.action_dispatch()

        # 2. Test Driver On Trip
        self.vehicle_van.status = 'available'
        self.driver_alex.status = 'on_trip'
        with self.assertRaises(UserError, msg="Should block dispatching an already On Trip driver"):
            trip.action_dispatch()

    def test_05_cargo_capacity_overflow(self):
        """Rule 5: Cargo Weight must not exceed the vehicle's maximum load capacity."""
        self.vehicle_van.status = 'available'
        self.driver_alex.status = 'available'

        with self.assertRaises(Exception):
            self.env['transit.trip'].create({
                'source': 'Depot A',
                'destination': 'Hub B',
                'vehicle_id': self.vehicle_van.id,
                'driver_id': self.driver_alex.id,
                'cargo_weight': 600.0,  # Exceeds 500.0 max capacity
                'planned_distance': 50.0,
            })

    def test_06_dispatch_status_transitions(self):
        """Rule 6: Dispatching a trip automatically changes both vehicle and driver to On Trip."""
        self.vehicle_van.status = 'available'
        self.driver_alex.status = 'available'

        trip = self.env['transit.trip'].create({
            'source': 'Depot A',
            'destination': 'Hub B',
            'vehicle_id': self.vehicle_van.id,
            'driver_id': self.driver_alex.id,
            'cargo_weight': 300.0,
            'planned_distance': 50.0,
        })
        trip.action_dispatch()

        self.assertEqual(trip.state, 'dispatched')
        self.assertEqual(self.vehicle_van.status, 'on_trip')
        self.assertEqual(self.driver_alex.status, 'on_trip')

    def test_07_complete_status_transitions(self):
        """Rule 7: Completing a trip automatically changes vehicle and driver back to Available,
        updates vehicle odometer, and logs fuel and expenses."""
        self.vehicle_van.status = 'available'
        self.driver_alex.status = 'available'

        trip = self.env['transit.trip'].create({
            'source': 'Depot A',
            'destination': 'Hub B',
            'vehicle_id': self.vehicle_van.id,
            'driver_id': self.driver_alex.id,
            'cargo_weight': 300.0,
            'planned_distance': 50.0,
        })
        trip.action_dispatch()

        # Update trip with completion details
        trip.write({
            'final_odometer': 1100.0,  # +100 km from vehicle's 1000.0
            'fuel_consumed': 10.0,
            'fuel_cost': 950.0,
            'toll_cost': 150.0,
        })
        trip.action_complete()

        # Check state transitions
        self.assertEqual(trip.state, 'completed')
        self.assertEqual(self.vehicle_van.status, 'available')
        self.assertEqual(self.driver_alex.status, 'available')
        self.assertEqual(self.vehicle_van.odometer, 1100.0)

        # Check auto-generated fuel log
        fuel_logs = self.env['transit.fuel.log'].search([('trip_id', '=', trip.id)])
        self.assertEqual(len(fuel_logs), 1)
        self.assertEqual(fuel_logs.liters, 10.0)
        self.assertEqual(fuel_logs.cost, 950.0)

        # Check auto-generated expense
        expenses = self.env['transit.expense'].search([('trip_id', '=', trip.id)])
        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses.fuel_cost, 950.0)
        self.assertEqual(expenses.toll_cost, 150.0)

    def test_08_cancel_dispatched_trip(self):
        """Rule 8: Cancelling a dispatched trip restores the vehicle and driver to Available."""
        self.vehicle_van.status = 'available'
        self.driver_alex.status = 'available'

        trip = self.env['transit.trip'].create({
            'source': 'Depot A',
            'destination': 'Hub B',
            'vehicle_id': self.vehicle_van.id,
            'driver_id': self.driver_alex.id,
            'cargo_weight': 300.0,
            'planned_distance': 50.0,
        })
        trip.action_dispatch()
        trip.action_cancel()

        self.assertEqual(trip.state, 'cancelled')
        self.assertEqual(self.vehicle_van.status, 'available')
        self.assertEqual(self.driver_alex.status, 'available')

    def test_09_maintenance_in_shop_transition(self):
        """Rule 9: Creating an active maintenance record automatically changes vehicle status to In Shop."""
        self.vehicle_van.status = 'available'

        maintenance = self.env['transit.maintenance'].create({
            'vehicle_id': self.vehicle_van.id,
            'service_type': 'Oil Change',
            'cost': 1500.0,
            'state': 'active',
        })

        self.assertEqual(maintenance.state, 'active')
        self.assertEqual(self.vehicle_van.status, 'in_shop')

    def test_10_maintenance_close_transition(self):
        """Rule 10: Closing maintenance restores the vehicle to Available (unless retired)."""
        self.vehicle_van.status = 'available'
        maintenance = self.env['transit.maintenance'].create({
            'vehicle_id': self.vehicle_van.id,
            'service_type': 'Oil Change',
            'cost': 1500.0,
            'state': 'active',
        })
        self.assertEqual(self.vehicle_van.status, 'in_shop')

        maintenance.action_close()

        self.assertEqual(maintenance.state, 'closed')
        self.assertEqual(self.vehicle_van.status, 'available')

        # Check that closing maintenance does not restore retired vehicles
        self.vehicle_van.status = 'retired'
        maintenance.action_reopen()
        self.assertEqual(self.vehicle_van.status, 'in_shop')
        maintenance.action_close()
        self.assertEqual(self.vehicle_van.status, 'retired')
