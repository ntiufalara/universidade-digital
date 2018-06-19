# coding: utf-8
from openerp.osv import osv, fields
from openerp import SUPERUSER_ID


class DocumentosOrientador(osv.Model):
    _name = "ud_monitoria.documentos_orientador"
    _description = u"Documentos de monitoria do orientador (UD)"
    _order = "is_active desc"

    _columns = {
        "disciplina_id": fields.many2one('ud_monitoria.disciplina', u"Disciplina", ondelete="restrict"),
        "curso_id": fields.related("disciplina_id", "bolsas_curso_id", type="many2one", relation="ud_monitoria.bolsas_curso",
                                   readonly=True, string=u"Curso"),
        "semestre_id": fields.related("disciplina_id", "bolsas_curso_id", "semestre_id", type="many2one",
                                      relation="ud_monitoria.semestre", readonly=True, string=u"Semestre"),
        "perfil_id": fields.many2one("ud.perfil", u"SIAPE", required=True),
        "orientador_id": fields.related('disciplina_id', "perfil_id", "ud_papel_id", type="many2one", relation="ud.employee",
                                        readonly=True, string=u"Orientador"),

        "declaracao_nome": fields.char(u"Declaração (Nome)"),
        "declaracao": fields.binary(u"Declaração", help=u"Declaração de Participação de Banca"),
        "certificado_nome": fields.char(u"Certificado (Nome)"),
        "certificado": fields.binary(u"Certificado", help=u"Certidão de Participação de Orientação"),
        "is_active": fields.boolean(u"Ativo?", readonly=True),
    }
    _sql_constraints = [
        ("doc_perfil_disciplina_unique", "unique(disciplina_id,perfil_id)", u"Deve haver apenas um documento para um orientador e disciplina.")
    ]
    _defaults = {
        "is_active": True,
    }

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

    # Método para botões na view
    def ativar(self, cr, uid, ids, context=None):
        cr.execute(
            '''
            SELECT EXISTS(
                SELECT
                    doc.id
                FROM
                  %(doc)s doc INNER JOIN %(disc)s disc ON (doc.disciplina_id = disc.id)
                WHERE
                  doc.id in (%(ids)s) AND (disc.data_inicial <= '%(hj)s' AND disc.data_final >= '%(hj)s') = true
            );
            ''' % {
                'ids': str(ids).lstrip('[(').rstrip(']),').replace('L', ''),
                'doc': self._table,
                'disc': self.pool.get('ud_monitoria.disciplina')._table,
                'hj': ''
            }
        )
        if cr.fetchone()[0]:
            raise osv.except_osv(
                u'Ação indisponível',
                u'Não é possível reativar o vínculo do orientador enquanto a disciplina estiver inativa.'
            )
        return self.write(cr, uid, ids, {'is_active': True}, context)

    def desativar(self, cr, uid, ids, context=None):
        cr.execute(
            '''
            SELECT EXISTS(
                SELECT
                    doc.id
                FROM
                    %(doc)s doc INNER JOIN %(disc)s disc ON (doc.disciplina_id = disc.id)
                WHERE
                    doc.id in (%(ids)s) AND (disc.data_inicial <= '%(hj)s' AND disc.data_final >= '%(hj)s') = true
            );
            ''' % {
                'ids': str(ids).lstrip('[(').rstrip(']),').replace('L', ''),
                'doc': self._table,
                'disc': self.pool.get('ud_monitoria.disciplina')._table
            }
        )
        if cr.fetchone()[0]:
            raise osv.except_osv(
                u'Ação indisponível',
                u'Não é possível desativar o vínculo do orientador enquanto a disciplina estiver inativa.'
            )
        return self.write(cr, uid, ids, {'is_active': False}, context)
