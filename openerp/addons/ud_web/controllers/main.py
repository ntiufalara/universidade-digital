# encoding: UTF-8


from openerp.addons.web import http
from openerp.addons.web.controllers import main
from os.path import dirname, join

template_dir = join(dirname(dirname(__file__)), 'static', 'src', 'html')
template_file = join(template_dir, 'index.html')
template = open(template_file, 'r').read()


class HomePage(main.Home):
    _cp_path = '/'

    @http.httprequest
    def index(self, req, s_action=None, db=None, **kw):
        if db:
            return super(HomePage, self).index(req, s_action, db, **kw)
        else:
            return template
