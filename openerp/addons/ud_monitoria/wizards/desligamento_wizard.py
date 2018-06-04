# coding: utf-8
from openerp import SUPERUSER_ID
from openerp.osv import osv, fields
from openerp.osv.orm import except_orm


class DesligamentoWizard(osv.TransientModel):
    _name = "ud_monitoria.desligamento_wizard"
    _description = u"Desligamento de discentes (UD)"

    _columns = {
        "doc_discente_id": fields.many2one("ud_monitoria.documentos_discente", u"Discente", required=True, ondelete="cascade"),
        "justificativa": fields.text(u"Justificativa", required=True),
    }

    def default_get(self, cr, uid, fields_list, context=None):
        context = context or {}
        res = super(DesligamentoWizard, self).default_get(cr, uid, fields_list, context)
        if context.get("active_id", False) and context.get("active_model", False) == "ud_monitoria.documentos_discente":
            res["doc_discente_id"] = context["active_id"]
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        context = context or {}
        if context.get("active_id", False) and context.get("active_model", False) == "ud_monitoria.documentos_discente":
            doc = self.pool.get("ud_monitoria.documentos_discente").read(cr, uid, context["active_id"], ['disciplina_id'], context, '_classic_write')
            grupos = "ud_monitoria.group_ud_monitoria_coordenador,ud_monitoria.group_ud_monitoria_administrador"
            cr.execute('''
            SELECT EXISTS(
                SELECT
                    doc_o.id
                FROM
                    %(doc_o)s doc_o INNER JOIN %(disc)s disc ON (doc_o.disciplina_id = disc.id)
                        INNER JOIN %(per)s per ON (doc_o.perfil_id = per.id)
                            INNER JOIN %(pes)s pes ON (per.ud_papel_id = pes.id)
                                INNER JOIN %(res)s res ON (pes.resource_id = res.id)
                WHERE
                    res.user_id = %(uid)s AND disc.id = %(id)s
            );''' % {
                'doc_o': self.pool.get('ud_monitoria.documentos_orientador')._table,
                'disc': self.pool.get('ud_monitoria.disciplina')._table,
                'per': self.pool.get('ud.perfil')._table,
                'pes': self.pool.get('ud.employee')._table,
                'res': self.pool.get('resource.resource')._table,
                'uid': '%d' % uid,
                'id': '%d' % doc['disciplina_id']
            })
            if not cr.fetchone()[0] and not self.user_has_groups(cr, uid, grupos):
                raise except_orm(u"Acesso Negado",
                                 u"Você precisa ser orientador do discente atual ou ser Coordenador de Monitoria.")
        return super(DesligamentoWizard, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)

    def desligar(self, cr, uid, ids, context=None):
        pessoa_model = self.pool.get("ud.employee")
        for desligamento in self.browse(cr, uid, ids, context):
            responsavel = pessoa_model.search(cr, uid, [("user_id", "=", uid)], limit=2)
            if not responsavel:
                raise osv.except_osv(
                    u"Registro Inexistente",
                    u"Não é possível realizar essa alteração enquanto seu login não estiver vinculado ao núcleo"
                )
            if len(responsavel) > 1:
                raise osv.except_osv(
                    u"Multiplos vínculos",
                    u"Não é possível realizar essa alteração enquanto seu login possuir multiplos vínculos no núcleo"
                )
            if desligamento.doc_discente_id.state == "bolsista":
                perfil_model = self.pool.get("ud.perfil")
                perfis = perfil_model.search(cr, SUPERUSER_ID, [
                    ("matricula", "=", desligamento.doc_discente_id.perfil_id.matricula), ("tipo", "=", "a")
                ])
                if perfis:
                    perfil_model.write(cr, SUPERUSER_ID, perfis, {
                        'is_bolsista': False, 'tipo_bolsa': False, 'valor_bolsa': False
                    })
            desligamento.doc_discente_id.write({"state": "desligado", "is_active": False})
            self.pool.get("ud_monitoria.ocorrencia").create(cr, uid, {
                "responsavel_id": responsavel[0],
                "name": u"Desligamento do discente \"%s\"" % desligamento.doc_discente_id.discente_id.name,
                "envolvidos_ids": [(4, desligamento.doc_discente_id.discente_id.id)],
                "descricao": desligamento.justificativa,
                "semestre_id": desligamento.doc_discente_id.semestre_id.id,
            }, context)
        return True
