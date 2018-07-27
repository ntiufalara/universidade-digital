# coding: utf-8
from datetime import datetime
import logging
from openerp.osv import osv, fields
from openerp import SUPERUSER_ID

from util import data_hoje, DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger('ud_monitoria')


class DocumentosOrientador(osv.Model):
    _name = "ud_monitoria.documentos_orientador"
    _description = u"Documentos de monitoria do orientador (UD)"
    _order = "is_active desc"

    def get_doc_discentes(self, cr, uid, ids, campos, args, context=None):
        res = {}
        doc_discente = self.pool.get('ud_monitoria.documentos_discente')
        for doc in self.browse(cr, uid, ids, context):
            if doc.disciplina_id.perfil_id.id == doc.perfil_id.id:
                res[doc.id] = doc_discente.search(cr, uid, [('disciplina_id', '=', doc.disciplina_id.id)])
            else:
                res[doc.id] = []
        return res

    def get_is_active(self, cr, uid, ids, campos, args, context=None):
        res = {}
        hoje = data_hoje(self, cr, uid)
        for doc in self.browse(cr, uid, ids, context):
            res[doc.id] = (
                    doc.disciplina_id.perfil_id.id == doc.perfil_id.id
                    and hoje <= datetime.strptime(doc.disciplina_id.data_final, DEFAULT_SERVER_DATE_FORMAT).date()
            )
        return res

    def update_is_active(self, cr, uid, ids, context=None):
        if self._name == 'ud_monitoria.disciplina':
            cr.execute('''
            SELECT
                doc.id
            FROM
                "%(doc)s" doc INNER JOIN "%(disc)s" disc ON (doc.disciplina_id = disc.id)
            WHERE
                (doc.perfil_id != disc.perfil_id OR disc.data_final < '%(hj)s') AND doc.is_active = true
                OR (doc.perfil_id = disc.perfil_id AND disc.data_final >= '%(hj)s') AND doc.is_active = false;
            ''' % {
                'doc': self.pool.get('ud_monitoria.documentos_orientador')._table,
                'disc': self.pool.get('ud_monitoria.disciplina')._table,
                'hj': data_hoje(self, cr, uid).strftime(DEFAULT_SERVER_DATE_FORMAT),
            })
            return [l[0] for l in cr.fetchall()]
        return []

    _columns = {
        "disciplina_id": fields.many2one('ud_monitoria.disciplina', u"Disciplina", ondelete="restrict"),
        "curso_id": fields.related("disciplina_id", "bolsas_curso_id", type="many2one", relation="ud_monitoria.bolsas_curso",
                                   readonly=True, string=u"Curso"),
        "semestre_id": fields.related("disciplina_id", "bolsas_curso_id", "semestre_id", type="many2one",
                                      relation="ud_monitoria.semestre", readonly=True, string=u"Semestre"),
        "perfil_id": fields.many2one("ud.perfil", u"SIAPE", required=True),
        "orientador_id": fields.related("perfil_id", "ud_papel_id", type="many2one", relation="ud.employee",
                                        readonly=True, string=u"Orientador"),
        'doc_discente_ids': fields.function(get_doc_discentes, type='one2many', relation='ud_monitoria.documentos_discente',
                                            string=u'Discentes'),

        "declaracao_nome": fields.char(u"Declaração (Nome)"),
        "declaracao": fields.binary(u"Declaração", help=u"Declaração de Participação de Banca"),
        "certificado_nome": fields.char(u"Certificado (Nome)"),
        "certificado": fields.binary(u"Certificado", help=u"Certidão de Participação de Orientação"),
        'is_active': fields.function(get_is_active, type='boolean', string=u'Ativo?', store={
            'ud_monitoria.disciplina': (update_is_active, ['perfil_id', 'data_final'], 10)
        })
    }
    _sql_constraints = [
        ("doc_perfil_disciplina_unique", "unique(disciplina_id,perfil_id)", u"Deve haver apenas um documento para um orientador e disciplina.")
    ]

    # Métodos sobrescritos
    def name_get(self, cr, uid, ids, context=None):
        """
        === Sobrescrita do método osv.Model.name_get
        Define a forma de visualização desse modelo em campos many2one.
        """
        return [(doc["id"], doc["orientador_id"][1])
                for doc in self.read(cr, uid, ids, ["orientador_id"], context=context)]

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        """
        === Sobrescrita do método osv.Model.name_search
        Define a forma de pesquisa desse modelo em campos many2one.
        """
        pessoas = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("name", operator, name)], context=context)
        perfis = self.pool.get("ud.perfil").search(cr, SUPERUSER_ID, ['|', ("matricula", operator, name), ("ud_papel_id", "in", pessoas)], context=context)
        args = [("perfil_id", "in", perfis)] + (args or [])
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        """
        === Extensão do método osv.Model.search
        Permite filtrar os documentos de orientador do usuário informado.
        """
        context = context or {}
        if context.get("filtrar_orientador", False):
            employee = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)], limit=2)
            if not employee:
                return []
            perfis = self.pool.get("ud.perfil").search(cr, SUPERUSER_ID, [("ud_papel_id", "=", employee[0])], context=context)
            args = (args or []) + [("perfil_id", "in", perfis)]
        return super(DocumentosOrientador, self).search(cr, uid, args, offset, limit, order, context, count)

    # Métodos para adição do grupo de segurança
    def add_grupo_orientador(self, cr, uid, ids, context=None):
        """
        Adiciona um orientandor no grupo de permissões

        :raise osv.except_osv: Se perfil do mesmo não tiver um usuário.
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        group = self.pool.get("ir.model.data").get_object(
            cr, SUPERUSER_ID, "ud_monitoria", "group_ud_monitoria_orientador", context
        )
        for doc in self.browse(cr, uid, ids, context):
            if not doc.orientador_id.user_id:
                raise osv.except_osv(
                    u"Usuário não encontrado",
                    u"O registro no núcleo do atual orientador não possui login de usuário.")
            group.write({"users": [(4, doc.orientador_id.user_id.id)]})

    # Método para execução agendada
    def atualiza_status_cron(self, cr, uid, context=None):
        """
        Atualiza o status dos orientadores.
        """
        _logger.info(u'Desativando documentos de orientadores de disciplinas vencidas ou sem vínculo com a mesma...')
        cr.execute('''
        UPDATE "%(doc)s" doc SET doc.is_active = False
        WHERE
          doc.id in (
              SELECT
                  doc.id
              FROM
                  "%(doc)s" doc2 INNER JOIN "%(disc)s" disc ON (doc2.disciplina_id = disc.id)
              WHERE
                  (doc2.perfil_id != disc.perfil_id OR disc.data_final < '%(hj)s') AND doc2.is_active = true
          );
        ''' % {
            'doc': self.pool.get('ud_monitoria.documentos_orientador')._table,
            'disc': self.pool.get('ud_monitoria.disciplina')._table,
            'hj': data_hoje(self, cr, uid).strftime(DEFAULT_SERVER_DATE_FORMAT),
        })
        return True

