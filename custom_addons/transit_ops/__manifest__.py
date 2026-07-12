{
    'name': 'TransitOps',
    'version': '19.0.1.0.0',
    'category': 'Operations/Fleet',
    'summary': 'Smart Transport Operations Platform — Odoo Hackathon 2026',
    'description': """
TransitOps — Smart Transport Operations Platform
=================================================
End-to-end transport operations management:
- Vehicle Registry with unique registration enforcement
- Driver Management with licence tracking & safety scores
- Trip Dispatcher with cargo validation & automatic status transitions
- Maintenance workflow (auto In Shop / Available)
- Fuel & Expense tracking with auto operational cost
- Dashboard KPIs & Analytics with CSV export
- Role-Based Access Control (4 roles)
    """,
    'author': 'Hackathon Team',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/vehicle_views.xml',
        'views/driver_views.xml',
        'views/trip_views.xml',
        'views/maintenance_views.xml',
        'views/fuel_views.xml',
        'views/expense_views.xml',
        'views/dashboard_action.xml',
        'views/menu.xml',
        'data/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'transit_ops/static/src/css/theme.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
