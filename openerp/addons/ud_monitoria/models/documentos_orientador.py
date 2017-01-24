# coding: utf-8
from openerp.osv import osv, fields
from openerp import SUPERUSER_ID


class DocumentosOrientador(osv.Model):
    _name = "ud.monitoria.documentos.orientador"
    _description = u"Documentos de monitoria do orientador (UD)"

    _columns = {
        "disciplina_id": fields.many2one("ud.monitoria.disciplina", u"Disciplina", required=True, ondelete="restrict"),
        "orientador_id": fields.many2one("ud.monitoria.orientador", u"Orientador", readonly=True, ondelete="cascade"),
        "declaracao_nome": fields.char(u"Declaração (Nome)"),
        "declaracao": fields.binary(u"Declaração"),
        "certificado_nome": fields.char(u"Certificado (Nome)"),
        "certificado": fields.binary(u"Certificado"),
    }

    _sql_constraints = [
        ("doc_orientador_disc_unicos", "unique(disciplina_id,orientador_id)",
         u"Não é possível criar mais de um documento para o orientador de uma disciplina no semestre ")
    ]

    def name_get(self, cr, uid, ids, context=None):
        return [(doc["id"], doc["orientador_id"][1])
                for doc in self.read(cr, uid, ids, ["orientador_id"], context=context)]

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        pessoas = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("name", operator, name)], context=context)
        orientadores = self.pool.get("ud.monitoria.orientador").search(
            cr, SUPERUSER_ID, ['|', ("matricula", operator, name), ("pessoa_id", "in", pessoas)], context=context
        )
        args = [("orientador_id", "in", orientadores)] + (args or [])
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        context = context or {}
        if context.get("filtrar_orientador", False):
            employee = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)], limit=2)
            if not employee:
                return []
            orientadores = self.pool.get("ud.monitoria.orientador").search(cr, SUPERUSER_ID, [("pessoa_id", "in", employee)])
            if not orientadores:
                return []
            args = (args or []) + [("orientador_id", "=", orientadores[0])]
        return super(DocumentosOrientador, self).search(cr, uid, args, offset, limit, order, context, count)
