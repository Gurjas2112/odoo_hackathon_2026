from odoo import models, fields, api
from odoo.exceptions import UserError


class TransitMaintenance(models.Model):
    """Maintenance — PS §3.6
    
    Mandatory rules enforced:
    - Rule 9:  Active maintenance → vehicle status = In Shop
    - Rule 10: Close maintenance → vehicle status = Available (unless Retired)
    """
    _name = 'transit.maintenance'
    _description = 'Maintenance Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char(
        string='Reference', required=True, readonly=True,
        default='New', copy=False,
    )
    vehicle_id = fields.Many2one(
        'transit.vehicle', string='Vehicle',
        required=True, tracking=True,
    )
    service_type = fields.Char(
        string='Service Type', required=True, tracking=True,
        help='e.g. Oil Change, Tyre Replace, Engine Repair',
    )
    cost = fields.Float(string='Cost (₹)', tracking=True)
    date = fields.Date(string='Date', default=fields.Date.today, required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('closed', 'Closed'),
    ], string='Status', default='active', required=True, tracking=True)
    notes = fields.Text(string='Notes')

    # ── Display name ──
    vehicle_name = fields.Char(related='vehicle_id.name', string='Vehicle Name', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Rule 9: Creating an active maintenance record → vehicle In Shop."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('transit.maintenance') or 'New'
        records = super().create(vals_list)
        for rec in records:
            if rec.state == 'active':
                rec.vehicle_id.write({'status': 'in_shop'})
                rec.message_post(
                    body=f"<b>{rec.vehicle_id.name}</b> moved to <em>In Shop</em> "
                         f"and removed from dispatch pool.",
                    message_type='notification',
                )
        return records

    def action_close(self):
        """Rule 10: Close → vehicle Available (unless Retired)."""
        for rec in self:
            if rec.state != 'active':
                raise UserError("Only Active maintenance records can be closed.")
            rec.write({'state': 'closed'})
            if rec.vehicle_id.status == 'retired':
                rec.message_post(
                    body=f"Maintenance closed. <b>{rec.vehicle_id.name}</b> remains "
                         f"<em>Retired</em> — cannot return to service.",
                    message_type='notification',
                )
            else:
                rec.vehicle_id.write({'status': 'available'})
                rec.message_post(
                    body=f"Maintenance closed. <b>{rec.vehicle_id.name}</b> returned "
                         f"to <em>Available</em>.",
                    message_type='notification',
                )

    def action_reopen(self):
        """Reopen a closed maintenance record."""
        for rec in self:
            rec.write({'state': 'active'})
            rec.vehicle_id.write({'status': 'in_shop'})
