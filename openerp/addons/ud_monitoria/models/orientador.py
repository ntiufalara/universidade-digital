# coding: utf-8
from openerp.osv import osv, fields
from openerp import SUPERUSER_ID


class DocumentosOrientador(osv.Model):
    _name = "ud_monitoria.documentos_orientador"
    _description = u"Documentos de monitoria do orientador (UD)"
    _order = "is_active desc"

    _columns = {
        "disciplina_id": fields.many2one('ud_monitoria.disciplina', u"Disciplina", ondelete="cascade"),
        "curso_id": fields.related("disciplina_id", "bolsas_curso_id", type="many2one", relation="ud_monitoria.bolsas_curso",
                                   readonly=True, string=u"Curso"),
        "semestre_id": fields.related("disciplina_id", "bolsas_curso_id", "semestre_id", type="many2one",
                                      relation="ud_monitoria.semestre",
                                      readonly=True, string=u"Semestre"),
        "perfil_id": fields.many2one("ud.perfil", u"SIAPE", required=True, ondelete="restrict", domain="[('tipo', '=', 'p')]"),
        "orientador_id": fields.related("perfil_id", "ud_papel_id", type="many2one", relation="ud.employee",
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

    def create(self, cr, uid, vals, context=None):
        """
        === Extensão do método osv.Model.create
        Se perfil de orientador não for informado, esse é vinculado ao da disciplina do documento.
        """
        res = super(DocumentosOrientador, self).create(cr, uid, vals, context)
        self.add_grupo_orientador(cr, uid, res, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        """
        === Extensão do método osv.Model.write
        Adiciona orientador ao grupo de segurança se disciplina for modificada.
        """
        super(DocumentosOrientador, self).write(cr, uid, ids, vals, context)
        if "disciplina_id" in vals:
            self.add_grupo_orientador(cr, uid, ids, context)
        return True

    def unlink(self, cr, uid, ids, context=None):
        """
        === Extensão do método osv.Model.unlink
        Se orientador não tiver mais vínculos com outros documentos, remove-o do grupo de segurança.
        """
        try:
            self.remove_grupo_orientador(cr, uid, ids, context=None)
            return super(DocumentosOrientador, self).unlink(cr, uid, ids, context)
        except:
            self.add_grupo_orientador(cr, uid, ids, context)
            raise

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

    # Métodos para adição e remoção do grupo de segurança
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
                    "Usuário não encontrado",
                    "O registro no núcleo do atual orientador não possui login de usuário.")
            group.write({"users": [(4, doc.orientador_id.user_id.id)]})

    def remove_grupo_orientador(self, cr, uid, ids=None, perfis=None, context=None):
        """
        Remove um orientador de disciplina do grupo de permissões se não tiver mais nenhum vínculo com disciplinas.

        :raise osv.except_osv: Se perfil do mesmo não tiver um usuário.
        """
        group = self.pool.get("ir.model.data").get_object(
            cr, SUPERUSER_ID, "ud_monitoria", "group_ud_monitoria_orientador", context
        )
        perfil_model = self.pool.get('ud.perfil')
        if perfis:
            sql = '''
            SELECT
                usu.id
            FROM
                %(per)s per LEFT JOIN %(doc)s doc ON (doc.perfil_id = per.id)
                    INNER JOIN %(pes)s pes ON (per.ud_papel_id = pes.id)
                        INNER JOIN %(res)s res ON (pes.resource_id = res.id)
                            INNER JOIN %(usu)s usu ON (res.user_id = usu.id)
            WHERE
                per.id in (%(perfis)s) AND doc.id is null;
            ''' % {
                'doc': self._table,
                'per': perfil_model._table,
                'pes': self.pool.get('ud.employee')._table,
                'res': self.pool.get('resource.resource')._table,
                'usu': self.pool.get('res.users')._table,
                'perfis': str(perfis).lstrip('([').rstrip(']),').replace('L', '')
            }
            cr.execute(sql)
            res = cr.fetchall()
            if res:
                for usuario in res:
                    group.write({"users": [(3, usuario[0])]})
        if ids:
            for doc in self.browse(cr, uid, ids, context):
                perfis = perfil_model.search(cr, SUPERUSER_ID, [('ud_papel_id', '=', doc.orientador_id.id)])
                if not self.search_count(cr, SUPERUSER_ID, [('perfil_id', 'in', perfis)]):
                    group.write({"users": [(3, doc.orientador_id.user_id.id)]})

    # Métodos executados após mudança do valor de algum campo
    def onchange_perfil(self, cr, uid, ids, perfil_id, context=None):
        """
        Método usado para atualizar os dados do campo "orientador_id" caso "perfil_id" seja modificado.
        """
        if perfil_id:
            return {"value": {"orientador_id": self.pool.get("ud.perfil").read(
                cr, SUPERUSER_ID, perfil_id, ["ud_papel_id"], context=context
            ).get("ud_papel_id")}}
        return {"value": {"orientador_id": False}}

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
                  doc.id in (%(ids)s) AND disc.is_active = false
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
                    doc.id in (%(ids)s) AND disc.is_active = false
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
