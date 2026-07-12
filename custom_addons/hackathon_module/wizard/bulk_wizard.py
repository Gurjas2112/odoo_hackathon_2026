from odoo import models, fields


class HackathonBulkWizard(models.TransientModel):
    """Wizard for bulk actions on selected records."""
    _name = 'hackathon.bulk.wizard'
    _description = 'Bulk Action Wizard'

    target_state = fields.Selection([
        ('confirmed', 'Confirm'),
        ('in_progress', 'Start'),
        ('done', 'Mark Done'),
        ('cancelled', 'Cancel'),
    ], required=True, default='confirmed', string='Target Status')
    note = fields.Text(string='Note (optional)')

    def action_apply(self):
        """Apply the selected state to all active records."""
        active_ids = self.env.context.get('active_ids', [])
        records = self.env['hackathon.record'].browse(active_ids)
        for record in records:
            record.state = self.target_state
            if self.note:
                record.message_post(body=f"Bulk action: {self.note}")
        return {'type': 'ir.actions.act_window_close'}
