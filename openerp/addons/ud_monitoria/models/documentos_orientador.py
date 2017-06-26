# coding: utf-8
from openerp.osv import osv, fields
from openerp import SUPERUSER_ID


class DocumentosOrientador(osv.Model):
    _name = "ud.monitoria.documentos.orientador"
    _description = u"Documentos de monitoria do orientador (UD)"
    _order = "is_active desc"

    def valida_disciplina(self, cr, uid, ids, context=None):
        for doc in self.browse(cr, uid, ids, context):
            if doc.is_active and doc.disciplina_id.perfil_id != doc.perfil_id:
                return False
        return True

    def valida_disciplina_ativa(self, cr, uid, ids, context=None):
        for doc in self.browse(cr, uid, ids, context):
            if doc.is_active and self.search_count(cr, uid, [("disciplina_id", "=", doc.disciplina_id.id)]) > 1:
                return False
        return True

    _columns = {
        "disciplina_id": fields.many2one("ud.monitoria.disciplina", u"Disciplinas", required=True, ondelete="restrict"),
        "perfil_id": fields.many2one("ud.perfil", u"Perfil", required=True, ondelete="restrict"),
        "orientador_id": fields.related("perfil_id", "ud_papel_id", type="many2one", relation="ud.employee",
                                        readonly=True, string=u"Orientador"),
        "semestre_id": fields.related("disciplina_id", "processo_seletivo_id", "semestre_id", type="many2one", relation="ud.monitoria.registro",
                                      readonly=True, string=u"Semestre"),
        "declaracao_nome": fields.char(u"Declaração (Nome)"),
        "declaracao": fields.binary(u"Declaração", help=u"Declaração de Participação de Banca"),
        "certificado_nome": fields.char(u"Certificado (Nome)"),
        "certificado": fields.binary(u"Certificado", help=u"Certidão de Participação de Orientação"),
        "is_active": fields.boolean(u"Ativo?", readonly=True),
    }

    _constraints = [
        (valida_disciplina, u"O orientador da disciplina deve ser o mesmo que o proprietário documento enquanto este estiver ativo.", [u"Ativo"])
    ]

    _defaults = {
        "is_active": True,
    }

    def name_get(self, cr, uid, ids, context=None):
        return [(doc["id"], doc["orientador_id"][1])
                for doc in self.read(cr, uid, ids, ["orientador_id"], context=context)]

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        pessoas = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("name", operator, name)], context=context)
        perfis = self.pool.get("ud.perfil").search(cr, SUPERUSER_ID, ['|', ("matricula", operator, name), ("ud_papel_id", "in", pessoas)], context=context)
        discipinas = self.pool.get("ud.monitoria.disciplina").search(cr, uid, [("perfil_id", "=", perfis)], context=context)
        args = [("disciplina_id", "in", discipinas)] + (args or [])
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def create(self, cr, uid, vals, context=None):
        if "perfil_id" not in vals and vals.get("disciplina_id", None):
            vals["perfil_id"] = self.pool.get("ud.monitoria.disciplina").browse(cr, uid, vals.get("disciplina_id")).perfil_id.id
        res = super(DocumentosOrientador, self).create(cr, uid, vals, context)
        self.add_grupo_orientador(cr, uid, res, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        super(DocumentosOrientador, self).write(cr, uid, ids, vals, context)
        if "disciplina_id" in vals:
            self.add_grupo_orientador(cr, uid, ids, context)

    def unlink(self, cr, uid, ids, context=None):
        self.remove_grupo_orientador(cr, uid, ids, context)
        return super(DocumentosOrientador, self).unlink(cr, uid, ids, context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        context = context or {}
        if context.get("filtrar_orientador", False):
            employee = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)], limit=2)
            if not employee:
                return []
            perfis = self.pool.get("ud.perfil").search(cr, SUPERUSER_ID, [("ud_papel_id", "=", employee[0])], context=context)
            args = (args or []) + [("perfil_id", "in", perfis)]
        return super(DocumentosOrientador, self).search(cr, uid, args, offset, limit, order, context, count)

    def add_grupo_orientador(self, cr, uid, ids, context=None):
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

    def remove_grupo_orientador(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        group = self.pool.get("ir.model.data").get_object(
            cr, SUPERUSER_ID, "ud_monitoria", "group_ud_monitoria_orientador", context
        )
        disciplina_model = self.pool.get("ud.monitoria.disciplina")
        continua = []
        for doc in self.browse(cr, uid, ids, context):
            if doc.orientador_id.id not in continua:
                perfis = [p.id for p in doc.orientador_id.papel_ids]
                if disciplina_model.search_count(cr, uid, [("perfil_id", "in", perfis)], context) > 1:
                    continua.append(doc.orientador_id.id)
                else:
                    if not doc.orientador_id.user_id:
                        raise osv.except_osv(
                            "Usuário não encontrado",
                            "O registro no núcleo do atual orientador não possui login de usuário.")
                    group.write({"users": [(3, doc.orientador_id.user_id.id)]})
