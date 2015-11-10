{
    'name': 'UD Web Calendar',
    'category': 'Hidden',
    'description':"""
OpenERP Web Calendar view.
==========================

""",
    'author': 'LaPEC',
    'version': '2.0',
    'depends': ['web'],
    'data' : [
#        'views/web_calendar.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    "css" : [
        "static/src/css/web_fullcalendar.css",
        "static/lib/fullcalendar/css/fullcalendar.css"
    ],
    "js" : [
        "static/lib/fullcalendar/js/fullcalendar.js",
        "static/src/js/web_calendar.js"
    ],
    'auto_install': True
    
}
