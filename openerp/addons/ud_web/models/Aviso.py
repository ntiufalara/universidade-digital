# encoding: UTF-8
import datetime
import logging

from openerp import SUPERUSER_ID
from openerp.osv import osv, fields

_logger = logging.getLogger(__name__)


class Aviso(osv.Model):
    """
    Mostra avisos no site principal
    """
    _name = 'ud.web.aviso'
    _description = "Aviso"

    _columns = {
        'name': fields.char(u'Título', required=True),
        'imagem': fields.binary(u'Ícone PNG (128x128px)'),
        'mensagem': fields.text(u'Mensagem'),
        'link': fields.char(u'Link'),
        'inicio_exibicao': fields.datetime(u'A partir'),
        'fim_exibicao': fields.datetime(u'Até'),
        'exibindo': fields.boolean(u'Em exibição'),
    }

    def atualiza_exibicao_cron(self, cr, uid, context=None):
        _logger.info(u"Rodando tarefa agendada de avisos do site...")

        aviso_ids = self.search(cr, uid, [('inicio_exibicao', '!=', False), ('fim_exibicao', '!=', False)])
        aviso_objs = self.browse(cr, uid, aviso_ids)

        hoje = datetime.datetime.now()

        for aviso in aviso_objs:
            inicio = datetime.datetime.strptime(aviso.inicio_exibicao, '%Y-%m-%d %H:%M:%S')
            fim = datetime.datetime.strptime(aviso.fim_exibicao, '%Y-%m-%d %H:%M:%S')

            if inicio <= hoje <= fim:
                _logger.info(u'Aviso: {}; ativado'.format(aviso.name))
                self.write(cr, SUPERUSER_ID, [aviso.id], {'exibindo': True})
            else:
                _logger.info(u'Aviso: {}; desativado'.format(aviso.name))
                self.write(cr, SUPERUSER_ID, [aviso.id], {'exibindo': False})
