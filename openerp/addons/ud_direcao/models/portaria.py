# encoding: UTF-8
import datetime

from openerp.osv import osv, fields


# noinspection PyAbstractClass
class Portaria(osv.Model):
    """
    Representa um documento (Portaria) emitido por algum setor dentro da universidade
    """
    _name = 'ud.direcao.portaria'

    _columns = {
        'nro_portaria': fields.char(u'Número', required=True),
        'descricao': fields.text(u'Descrição', required=True),
        'data': fields.date('Data', required=True),
        'file_name': fields.char('Nome do arquivo', ),
        'anexo': fields.binary('Anexo', required=True),
        'campus_id': fields.many2one('ud.campus', "Campus", required=True),
        'polo_id': fields.many2one('ud.polo', 'Polo', required=True),
        'setor_id': fields.many2one('ud.setor', 'Emissor', required=True),
        'responsavel_id': fields.many2one('ud.employee', u'Responsável', required=True),
        'setor_destino_id': fields.many2one('ud.setor', "Destino", required=False),
    }

    _rec_name = 'nro_portaria'

    def create_or_write(self, vals):
        if hasattr(self, 'responsavel_cache') and self.responsavel_cache:
            vals['responsavel_id'] = self.responsavel_cache
        return vals

    def create(self, cr, user, vals, context=None):
        vals = self.create_or_write(vals)
        return super(Portaria, self).create(cr, user, vals, context)

    def write(self, cr, user, ids, vals, context=None):
        vals = self.create_or_write(vals)
        return super(Portaria, self).write(cr, user, ids, vals, context)

    def name_get(self, cr, user, ids, context=None):
        objs = self.browse(cr, user, ids, context)
        return [(obj.id, "Portaria nº: {}; Data: {}".format(obj.nro_portaria,
                                                            datetime.datetime.strptime(obj.data, '%Y-%m-%d').strftime(
                                                                '%d/%m/%Y'))) for obj in objs]

    def onchange_setor_id(self, cr, uid, ids, setor_id, context=None):
        setor_model = self.pool.get('ud.setor')
        setor_obj = setor_model.browse(cr, uid, setor_id)
        self.responsavel_cache = setor_obj.responsavel_id.id
        return {
            'value': {
                'responsavel_id': setor_obj.responsavel_id.id
            }
        }

