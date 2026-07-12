from odoo import models, fields, api
from odoo.exceptions import UserError

class TransitBatchDispatchWizard(models.TransientModel):
    _name = 'transit.batch.dispatch.wizard'
    _description = 'Batch Dispatch Wizard'

    trip_ids = fields.Many2many(
        'transit.trip', 
        string='Trips to Dispatch',
        domain="[('state', '=', 'draft')]"
    )
    dispatch_summary = fields.Text(string='Validation Details', readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids')
        if active_ids and self.env.context.get('active_model') == 'transit.trip':
            draft_trips = self.env['transit.trip'].browse(active_ids).filtered(lambda t: t.state == 'draft')
            res['trip_ids'] = [(6, 0, draft_trips.ids)]
            
            # Generate a summary
            lines = []
            for trip in draft_trips:
                issues = []
                if not trip.vehicle_id:
                    issues.append("No vehicle selected")
                elif trip.vehicle_id.status != 'available':
                    issues.append(f"Vehicle status '{trip.vehicle_id.status}' is not Available")
                if not trip.driver_id:
                    issues.append("No driver selected")
                else:
                    if trip.driver_id.license_status == 'expired':
                        issues.append("Driver license expired")
                    elif trip.driver_id.status == 'suspended':
                        issues.append("Driver suspended")
                    elif trip.driver_id.status != 'available':
                        issues.append(f"Driver status '{trip.driver_id.status}' is not Available")
                if trip.vehicle_id and trip.vehicle_id.max_load_capacity and trip.cargo_weight > trip.vehicle_id.max_load_capacity:
                    issues.append(f"Cargo {trip.cargo_weight} kg exceeds vehicle capacity ({trip.vehicle_id.max_load_capacity} kg)")
                
                status_str = "VALID (Ready to dispatch)" if not issues else f"INVALID: {', '.join(issues)}"
                lines.append(f"* {trip.name} ({trip.source} -> {trip.destination}): {status_str}")
            
            res['dispatch_summary'] = "\n".join(lines) if lines else "No draft trips selected."
        return res

    def action_batch_dispatch(self):
        self.ensure_one()
        if not self.trip_ids:
            raise UserError("No trips selected for dispatch.")
            
        success_count = 0
        error_messages = []
        
        for trip in self.trip_ids:
            try:
                # Use standard action_dispatch
                trip.action_dispatch()
                success_count += 1
            except Exception as e:
                error_messages.append(f"{trip.name}: {str(e)}")
                
        message = f"Successfully dispatched {success_count} trip(s)."
        if error_messages:
            message += f"\nFailed dispatches:\n" + "\n".join(error_messages)
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Batch Dispatch Completed',
                'message': message,
                'sticky': True,
                'type': 'warning' if error_messages else 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
