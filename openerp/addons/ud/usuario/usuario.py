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
            if cpf:
                vals["login"] = cpf.replace(".", "").replace("-", "")
                combinacao = self.valida_cpf(cpf)
                if not combinacao:
                    raise osv.except_osv(u"CPF/Login inválido", u"O CPF/login inserido não é válido.")
                combinacao = combinacao.groups()
                cpf = ".".join(combinacao[:-1]) + "-" + combinacao[-1]
                pessoa = pessoa_model.search(cr, SUPERUSER_ID, [("cpf", "=", cpf)])
                if pessoa:
                    pessoa = pessoa_model.browse(cr, SUPERUSER_ID, pessoa[0], context)
                    if pessoa.user_id:
                        raise osv.except_osv(u"Usuário existente", u"Existe outro usuário cadastrado com seu CPF.")
            else:
                raise osv.except_osv(u"Dados inválidos", u"Não é possível criar um usuário sem informar um CPF/Login.")
            res = super(UsuarioUD, self).create(cr, uid, vals, context)
            if pessoa and not getattr(pessoa, "user_id", None):
                dados = {"user_id": res}
                if "name" in vals:
                    dados["name"] = vals["name"]
                pessoa.write(dados)
            else:
                dados = {
                    "name": vals.get("name", False), "cpf": cpf, "work_email": vals.get("email", False), "user_id": res,
                }
                pessoa_model.create(cr, SUPERUSER_ID, dados, context)
            try:
                group = self.pool.get("ir.model.data").get_object(
                    cr, SUPERUSER_ID, "base", "usuario_ud", context
                )
                group.write({"users": [(4, res)]})
            except ValueError:
                pass
            return res
        return super(UsuarioUD, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if (context or {}).get("usuario_ud", False):
            pessoa_model = self.pool.get("ud.employee")
            cpf = vals.get("login", False)
            if cpf:
                if len(ids) > 1:
                    raise osv.except_osv(u"Repetição de Login",
                                         u"Não é permitido repetir o mesmo login para múltiplos usuários.")
                p_atual = pessoa_model.search(cr, SUPERUSER_ID, [("user_id", "=", ids[0])], context=context)
                if len(p_atual) > 1:
                    raise osv.except_osv(u"Multiplos usuários",
                                         u"Há multiplos registros de pessoa vinculado ao mesmo usuário.")
                vals["login"] = cpf.replace(".", "").replace("-", "")
                combinacao = self.valida_cpf(cpf)
                if not combinacao:
                    raise osv.except_osv(u"CPF/Login inválido", u"O CPF/login inserido não é válido.")
                combinacao = combinacao.groups()
                cpf = ".".join(combinacao[:-1]) + "-" + combinacao[-1]
                pessoa = pessoa_model.search(cr, SUPERUSER_ID, [("cpf", "=", cpf)], context=context)
                if pessoa:
                    pessoa = pessoa_model.browse(cr, SUPERUSER_ID, pessoa[0], context)
                    p_atual = p_atual and p_atual[0] or False
                    if p_atual and p_atual != pessoa.id:
                        raise osv.except_osv("Conflito",
                                             u"O CPF digitado está vinculado a um registro de pessoa de outro usuário.")
                    elif not pessoa.user_id:
                        dados = {"user_id": ids[0]}
                        if "name" in vals:
                            dados["name"] = vals["name"]
                        pessoa.write(dados)
                elif p_atual:
                    p_atual = pessoa_model.browse(cr, SUPERUSER_ID, p_atual[0], context)
                    if p_atual.cpf != cpf:
                        p_atual.write({"cpf": cpf})
                else:
                    usuario = self.browse(cr, uid, ids[0], context)
                    dados = {
                        "name": usuario.name, "cpf": cpf, "work_email": usuario.email, "user_id": ids[0],
                    }
                    pessoa_model.create(cr, SUPERUSER_ID, dados, context)
                    try:
                        group = self.pool.get("ir.model.data").get_object(
                            cr, SUPERUSER_ID, "base", "usuario_ud", context
                        )
                        group.write({"users": [(4, ids[0])]})
                    except ValueError:
                        pass
            elif vals.get("name", False):
                pessoas = pessoa_model.search(cr, SUPERUSER_ID, [("user_id", "in", ids)], context=context)
                pessoa_model.write(cr, SUPERUSER_ID, pessoas, {"name": vals["name"]}, context)
        return super(UsuarioUD, self).write(cr, uid, ids, vals, context)

    def valida_cpf(self, cpf):
        combinacao = re.match("(\d{3})\.?(\d{3})\.?(\d{3})-?(\d\d)", cpf or "")
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
        return combinacao

