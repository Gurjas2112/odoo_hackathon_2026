{
    'name': 'Hackathon Module',
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Hackathon 2026 — [Replace with your solution title]',
    'description': """
        Built for Odoo Hackathon 2026.
        
        Features:
        - [Feature 1]
        - [Feature 2]
        - [Feature 3]
    """,
    'author': 'Hackathon Team',
    'website': 'https://github.com/yourteam',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/main_views.xml',
        'views/menu.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
