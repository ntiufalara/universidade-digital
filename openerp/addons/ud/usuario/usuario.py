# coding: utf-8
import re

from openerp import SUPERUSER_ID
from openerp.osv import osv, fields
from openerp.tools.safe_eval import safe_eval


class ConfiguracaoUsuarioUD(osv.Model):
    _inherit = "base.config.settings"

    _columns = {
        "exclusao_unica": fields.boolean(u"Exclusão em cascata (Pessoa/Usuário)",
                                         help=u"Se uma pessoa no núcleo for excluída, seu usuário será excluído junto.")
    }

    def get_default_exclusao_unica(self, cr, uid, fields, context=None):
        return {
            'exclusao_unica': ConfiguracaoUsuarioUD.get_exclusao_unica(self, cr, uid, context)
        }

    @staticmethod
    def get_exclusao_unica(cls, cr, uid, context=None):
        config_parameters = cls.pool.get('ir.config_parameter')
        return safe_eval(config_parameters.get_param(cr, uid, 'ud.pessoa_usuario', 'True', context=context))


    def set_exclusao_unica(self, cr, uid, ids, context=None):
        config_parameters = self.pool.get("ir.config_parameter")
        for config in self.browse(cr, uid, ids, context=context):
            config_parameters.set_param(cr, uid, 'ud.pessoa_usuario', repr(config.exclusao_unica))


class UsuarioUD(osv.Model):
    _inherit = "res.users"

    def create(self, cr, uid, vals, context=None):
        if (context or {}).get("usuario_ud", False):
            vals["tz"] = vals.get("tz", "America/Maceio")
            pessoa_model = self.pool.get("ud.employee")
            cpf = vals.get("login", False)
            combinacao = self.combinacao_cpf(cpf)
            if cpf and combinacao:
                vals["login"] = cpf.replace(".", "").replace("-", "")
                combinacao = combinacao.groups()
                cpf = ".".join(combinacao[:-1]) + "-" + combinacao[-1]
                pessoa = pessoa_model.search(cr, SUPERUSER_ID, [("cpf", "=", cpf)])
                if pessoa:
                    pessoa = pessoa_model.browse(cr, SUPERUSER_ID, pessoa[0], context)
                    if pessoa.user_id:
                        raise osv.except_osv(u"Usuário existente", u"Existe outro usuário cadastrado com seu CPF.")
            res = super(UsuarioUD, self).create(cr, uid, vals, context)
            if combinacao:
                if pessoa:
                    dados = {}
                    if not getattr(pessoa, "user_id", None):
                        dados = {"user_id": res}
                    if "name" in vals:
                        dados["name"] = vals["name"]
                    if dados:
                        pessoa.write(dados)
                else:
                    dados = {
                        "name": vals.get("name", False), "cpf": cpf, "work_email": vals.get("email", False), "user_id": res,
                    }
                    pessoa_model.create(cr, SUPERUSER_ID, dados, context)
                group = self.pool.get("ir.model.data").get_object(
                    cr, SUPERUSER_ID, "base", "usuario_ud", context
                )
                group.write({"users": [(4, res)]})
            return res
        return super(UsuarioUD, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if (context or {}).get("usuario_ud", False):
            pessoa_model = self.pool.get("ud.employee")
            cpf = vals.get("login", False)
            if cpf:
                combinacao = self.combinacao_cpf(cpf)
                if combinacao:
                    if len(ids) > 1:
                        raise osv.except_osv(u"Repetição de Login",
                                             u"Não é permitido repetir o mesmo login para múltiplos usuários.")
                    pessoa_atual = pessoa_model.search(cr, SUPERUSER_ID, [("user_id", "in", ids)], context=context)
                    if len(pessoa_atual) > 1:
                        raise osv.except_osv(u"Multiplos usuários",
                                             u"Há multiplos registros de pessoa vinculado ao mesmo usuário.")
                    pessoa_atual = pessoa_atual and pessoa_atual[0] or False
                    vals["login"] = cpf.replace(".", "").replace("-", "")
                    combinacao = combinacao.groups()
                    cpf = ".".join(combinacao[:-1]) + "-" + combinacao[-1]
                    pessoa = pessoa_model.search(cr, SUPERUSER_ID, [("cpf", "=", cpf)], context=context)
                    if pessoa:
                        pessoa = pessoa_model.browse(cr, SUPERUSER_ID, pessoa[0], context)
                        dados = {}
                        if "name" in vals:
                            dados["name"] = vals["name"]
                        if not pessoa.user_id:
                            dados["user_id"] = ids[0]
                            pessoa.write(dados)
                        elif pessoa_atual == pessoa.id:
                            pessoa.write(dados)
                        elif pessoa_atual:
                            raise osv.except_osv(
                                u"Conflito", u"O CPF digitado está vinculado a um registro de pessoa de outro usuário."
                            )
                    elif pessoa_atual:
                        pessoa_atual = pessoa_model.browse(cr, SUPERUSER_ID, pessoa_atual, context)
                        dados = {}
                        if "name" in vals:
                            dados["name"] = vals["name"]
                        if pessoa_atual.cpf != cpf:
                            dados["cpf"] = cpf
                            pessoa_atual.write(dados)
                    else:
                        usuario = self.browse(cr, uid, ids[0], context)
                        dados = {
                            "name": usuario.name, "cpf": cpf, "work_email": usuario.email, "user_id": ids[0],
                        }
                        pessoa_model.create(cr, SUPERUSER_ID, dados, context)
                    group = self.pool.get("ir.model.data").get_object(
                        cr, SUPERUSER_ID, "base", "usuario_ud", context
                    )
                    group.write({"users": [(4, ids[0])]})
        return super(UsuarioUD, self).write(cr, uid, ids, vals, context)

    def combinacao_cpf(self, cpf):
        return re.match("(\d{3})\.?(\d{3})\.?(\d{3})-?(\d\d)", cpf or "")

    def valida_cpf(self, cpf):
        if not isinstance(cpf, str):
            combinacao = cpf
            cpf = cpf.string
        else:
            combinacao = self.combinacao_cpf(cpf)
        if not combinacao:
            return False
        elif cpf.count(cpf[0]) == 11:
            return False

        def calcula_dv(cpf, pos_dv=-2):
            dv = 0
            for i in range(len(cpf[:pos_dv])):
                dv += int(cpf[i]) * (11 - (i + (-(pos_dv + 1))))
            dv %= 11
            return 0 if dv < 2 else 11 - dv

        cpf_r = cpf.replace(".", "").replace("-", "")
        if int(cpf[-2]) != calcula_dv(cpf_r) or int(cpf[-1]) != calcula_dv(cpf_r, -1):
            return False
        return True

    def _valida_cpf(self, cr, uid, ids, context=None):
        for user in self.browse(cr, uid, ids, context):
            combinacao = self.combinacao_cpf(user.login)
            if combinacao:
                if not self.valida_cpf(combinacao):
                    return False
        return True

    _constraints = [
        (_valida_cpf, u"O CPF/login inserido não é válido.", [u"CPF/Login inválido"])
    ]

