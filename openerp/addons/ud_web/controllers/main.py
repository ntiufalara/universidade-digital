# encoding: UTF-8
import logging
from openerp.addons.web import http
from openerp.addons.web.controllers import main
from os.path import dirname, join

import jinja2

_logger = logging.getLogger(__name__)


class HomePage(main.Home):
    _cp_path = '/'

    template_dir = join(dirname(dirname(__file__)), 'static', 'src', 'html')
    jinja2_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir)
    )

    @http.httprequest
    def index(self, req, s_action=None, db=None, **kw):
        if db:
            return super(HomePage, self).index(req, s_action, db, **kw)
        else:
            template = self.jinja2_env.get_template('index.html')
            # Autentica o usuário anônimo para buscar por avisos no banco de dados
            db, user, password = 'ud', 'anonymous', 'anonymous'
            main.Session().authenticate(req, db, user, password)
            try:
                # Busca os avisos no banco
                Aviso = req.session.model('ud.web.aviso')
                avisos = Aviso.read(
                    Aviso.search([('exibindo', '=', True)])
                )
                return template.render({
                    'avisos': avisos
                })
            except:
                return template.render()
