# -*- encoding: UTF-8 -*-
{
    "name": "Web (UD)",
    "version": "1.01",
    "depends": ["base", 'web', 'portal_anonymous'],
    "author": "NTI UFAL Arapiraca",
    "category": "Universidade Digital",
    "description": """
    O módulo possui alterações no template
    """,
    'data': [
        'data/ud_web_cron.xml',
        'security/ud_web_security.xml',
        'security/ir.model.access.csv',
        'views/aviso_view.xml',
        'views/menus.xml',
    ],
    'css': [
        'static/lib/bootstrap/css/*.css',
        'static/src/css/*.css',
    ],
    'js': [
        'static/lib/bootstrap/js/*.js',
        'static/lib/ga/js/*.js',
        'static/lib/mask/jquery.mask.min.js',
        "static/lib/mapquest/mqa.toolkit.js",
        'static/src/js/*.js',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    "init_xml": [],
    'update_xml': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
