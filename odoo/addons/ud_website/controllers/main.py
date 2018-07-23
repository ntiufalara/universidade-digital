from odoo import http

from odoo.addons.web.controllers import main


class UdHome(main.Home):
    @http.route('/', type='http', auth="public")
    def index(self, s_action=None, db=None, **kw):
        return http.request.render('ud_website.home')

