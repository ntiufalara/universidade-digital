# coding: utf-8
"""
Created on 29 de abr de 2016

@author: cloves
"""

from openerp import SUPERUSER_ID as SUPER_UID
from openerp.osv import osv, fields
from psycopg2 import ProgrammingError


class Pessoa(osv.AbstractModel):
    _name = "ud.monitoria.pessoa"
    _description = u"Modelo abstrado para Pessoa (UD)"

    _TIPOS = [('p', u'Docente'), ('a', u'Discente')]

    def get_pessoa(self, cr, uid, ids, campo, args, context=None):
        res = {}
        perfil_model = self.pool.get("ud.perfil")
        for pessoa in self.read(cr, uid, ids, ["matricula", "tipo"], load="_classic_write", context=context):
            p = self.busca_pessoa(cr, perfil_model, pessoa["matricula"], pessoa["tipo"], context=context)
            res[pessoa["id"]] = p
        return res

    def search_pessoa(self, cr, uid, modelo, campo, args, context=None):
        if not len(args):
            return []
        if not args[0][2]:
            return []
        args = [("ud_papel_id", arg[1], arg[2]) for arg in args]
        perfil_model = self.pool.get("ud.perfil")
        res = [("tipo", "in", []), ("matricula", "in", [])]
        for perfil in perfil_model.browse(cr, SUPER_UID, perfil_model.search(cr, SUPER_UID, args, context=context), context):
            res[0][2].append(perfil.tipo)
            res[1][2].append(perfil.matricula)
        return [("id", "in", self.search(cr, uid, res, context=context))]

    _columns = {
        "id": fields.integer("ID", readonly=True, invisible=True),
        "matricula": fields.char(u"Matrícula", required=True),
        "tipo": fields.selection(_TIPOS, u"Tipo", required=True),
        "pessoa_id": fields.function(get_pessoa, type="many2one", relation="ud.employee", fnct_search=search_pessoa,
                                     string=u"Pessoa"
        ),
        "email": fields.related("pessoa_id", "work_email", type="char", string=u"E-mail", readonly=True),
    }

    _constraints = [
        (lambda self, *args, **kwargs: self.valida_pessoa(*args, **kwargs),
         u"Não foi encontrada nenhuma pessoa com os dados informados", ["Pessoa"]),
    ]

    def name_get(self, cr, uid, ids, context=None):
        return [
            (pessoa["id"], pessoa["pessoa_id"][1])
            for pessoa in self.read(cr, uid, ids, ["matricula", "pessoa_id"], context=context)
            ]

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        pessoas = self.pool.get("ud.employee").search(cr, SUPER_UID, [("name", operator, name)], context=context)
        args = ['|', ("matricula", operator, name), ("pessoa_id", "in", pessoas)] + (args or [])
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def create(self, cr, uid, vals, context=None):
        res = super(Pessoa, self).create(cr, uid, vals, context)
        if context.get("res_group", False):
            try:
                pessoa = self.browse(cr, uid, res, context)
                group = self.pool.get("ir.model.data").get_object(
                    cr, SUPER_UID, "ud_monitoria", context["res_group"], context
                )
                group.write({"users": [(4, pessoa.pessoa_id.user_id.id)]})
            except ProgrammingError:
                raise osv.except_osv(u"Usuário não encontrado",
                                     u"O registro de \"%s\" no núcleo não está vinculado a um usuário (login)." % pessoa.pessoa_id.name)
            except ValueError:
                pass
        return res

    def unlink(self, cr, uid, ids, context=None):
        if context.get("res_group", False):
            try:
                group = self.pool.get("ir.model.data").get_object(
                    cr, SUPER_UID, "ud_monitoria", context["res_group"], context
                )
                for pessoa_id in ids:
                    group.write({"users": [(3, self.browse(cr, uid, pessoa_id, context).pessoa_id.user_id.id)]})
            except ValueError:
                pass
        return super(Pessoa, self).unlink(cr, uid, ids, context)

    def valida_pessoa(self, cr, uid, ids, context=None):
        perfil_model = self.pool.get("ud.perfil")
        for pessoa in self.browse(cr, uid, ids, context):
            if not self.busca_pessoa(cr, perfil_model, pessoa.matricula, pessoa.tipo, context=context):
                return False
        return True

    def busca_pessoa(self, cr, perfil_model, matricula, tipo, args=None, context=None):
        args = [("matricula", "=", matricula), ("tipo", "=", tipo)] + (args or [])
        perfil = perfil_model.search(cr, SUPER_UID, args, context=context)
        if perfil:
            perfil = perfil_model.browse(cr, SUPER_UID, perfil[0], context=context)
            return perfil.ud_papel_id.id
        return False

    def update_pessoa(self, cr, uid, ids, context=None):
        res = []
        perfil_model = self.pool.get("ud.perfil")
        for pessoa in self.browse(cr, uid, ids, context=context):
            employee = self.busca_pessoa(cr, perfil_model, pessoa.matricula, pessoa.tipo,
                                         [("ud_papel_id", "=", pessoa.pessoa_id.id)], context)
            if not employee:
                res.append(pessoa.id)
        return res

    def onchange_matricula_tipo(self, cr, uid, ids, matricula, tipo, context=None):
        if matricula and tipo:
            perfil_model = self.pool.get("ud.perfil")
            pessoa = self.busca_pessoa(cr, perfil_model, matricula, tipo, context=context)
            if pessoa:
                return {"value": {"pessoa_id": pessoa}}
            return {"value": {"pessoa_id": False},
                    "warning": {"title": u"Dados Inválidos",
                                "message": u"Nehuma pessoa cadastrada com os dados informados"}}
        return {"value": {"pessoa_id": False}}


class Discente(osv.Model):
    _name = "ud.monitoria.discente"
    _description = u"Modelo para dados de Discente (UD)"
    _inherit = "ud.monitoria.pessoa"

    _columns = {
        "documentos_ids": fields.one2many("ud.monitoria.documentos.discente", "discente_id", u"Documentos"),
    }

    _sql_constraints = [
        ("discente_unico", "unique(matricula,tipo)", u"Já existe um registro para essa Pessoa."),
    ]

    _defaults = {
        "tipo": "a",
    }

    def create(self, cr, uid, vals, context=None):
        context = context or {}
        context["res_group"] = "group_ud_monitoria_monitor"
        return super(Discente, self).create(cr, uid, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        perfil_model = self.pool.get("ud.perfil")
        for disc in self.browse(cr, uid, ids, context):
            args = [("matricula", "=", disc.matricula), ("tipo", "=", disc.tipo), ("is_bolsista", "=", True),
                    ("tipo_bolsa", "=", "m")]
            perfis = perfil_model.search(cr, SUPER_UID, args, context=context)
            if perfis:
                perfil_model.write(cr, SUPER_UID, perfis, {"is_bolsista": False, "tipo_bolsa": False, "valor_bolsa": False}, context)
        context = context or {}
        context["res_group"] = "group_ud_monitoria_monitor"
        return super(Discente, self).unlink(cr, uid, ids, context)


class Orientador(osv.Model):
    _name = "ud.monitoria.orientador"
    _description = u"Modelo para dados de Orientador (UD)."
    _inherit = "ud.monitoria.pessoa"

    _columns = {
        "documentos_ids": fields.one2many("ud.monitoria.documentos.orientador", "orientador_id", u"Documentos")
    }

    _sql_constraints = [
        ("orientador_unico", "unique(matricula,tipo)", u"Já existe um registro para essa Pessoa."),
    ]

    _defaults = {
        "tipo": "p",
    }

    def create(self, cr, uid, vals, context=None):
        context = context or {}
        context["res_group"] = "group_ud_monitoria_orientador"
        return super(Orientador, self).create(cr, uid, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        context = context or {}
        context["res_group"] = "group_ud_monitoria_orientador"
        return super(Orientador, self).unlink(cr, uid, ids, context)
