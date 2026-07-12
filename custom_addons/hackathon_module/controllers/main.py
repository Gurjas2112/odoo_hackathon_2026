from odoo import http
from odoo.http import request


class HackathonController(http.Controller):
    """REST API controller — ready to use for external integrations."""

    @http.route('/api/hackathon/records', type='json', auth='user', methods=['POST'])
    def get_records(self, **kwargs):
        """Get all records for the current user."""
        domain = kwargs.get('domain', [])
        limit = kwargs.get('limit', 100)
        records = request.env['hackathon.record'].search_read(
            domain=domain,
            fields=['name', 'state', 'amount', 'date', 'partner_id'],
            limit=limit,
            order='create_date desc',
        )
        return {'status': 'success', 'count': len(records), 'data': records}

    @http.route('/api/hackathon/records/create', type='json', auth='user', methods=['POST'])
    def create_record(self, **kwargs):
        """Create a new record via API."""
        vals = kwargs.get('vals', {})
        if not vals.get('name'):
            return {'status': 'error', 'message': 'Name is required'}
        record = request.env['hackathon.record'].create(vals)
        return {'status': 'success', 'id': record.id, 'name': record.name}

    @http.route('/api/hackathon/stats', type='json', auth='user', methods=['POST'])
    def get_stats(self, **kwargs):
        """Get summary statistics."""
        Model = request.env['hackathon.record']
        return {
            'status': 'success',
            'stats': {
                'total': Model.search_count([]),
                'draft': Model.search_count([('state', '=', 'draft')]),
                'confirmed': Model.search_count([('state', '=', 'confirmed')]),
                'in_progress': Model.search_count([('state', '=', 'in_progress')]),
                'done': Model.search_count([('state', '=', 'done')]),
            },
        }
