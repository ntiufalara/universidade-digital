# -*- encoding: UTF-8 -*-
{
    "name": "Web (UD)",
    "version": "1.01",
    "depends": ["base"],
    "author": "LaPEC",
    "category": "Universidade Digital",
    "description": """
    O módulo possui alterações no template
    """,
    'css':[
           'static/lib/bootstrap/css/*.css',
           'static/src/css/*.css',
           ],
    'js' : [
            'static/lib/bootstrap/js/*.js',
            'static/lib/ga/js/*.js',
            'static/lib/mask/jquery.mask.min.js',
            "static/lib/mapquest/mqa.toolkit.js",
            'static/src/js/*.js',
    ],
    'qweb' : [
              'static/src/xml/*.xml',
              ],
    "init_xml": [],
    'update_xml': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
#    'certificate': 'certificate',
}