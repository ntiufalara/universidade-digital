# coding: utf-8
import re

from openerp import SUPERUSER_ID
from openerp.osv import osv, fields
from openerp.tools.safe_eval import safe_eval


class ConfiguracaoUsuarioUD(osv.Model):
    _inherit = "base.config.settings"

    _columns = {
        "criar_login_cpf": fields.boolean(
            u"Vincula um usuário com pessoa ao adicionar seu CPF",
            help=u"Ao adicionar um CPF, um usuário com login correspondente (sem pontos e traço) ao mesmo será buscado,"
                 u" se não existir, um novo será criado e vinculado, caso contrário, será verificado se não possui "
                 u"vínculo com outra pessoa e mostrado um erro se vínculo existir."
        ),
        "criar_pessoa_usuario": fields.boolean(u"Cria um registro de pessoa se login de usuário for um CPF"),
        "atualizar_login_cpf": fields.boolean(
            u"Atualiza login de usuários vinculados ao alterar o CPF de uma pessoa",
            help=u"Modificar o CPF de uma pessoa fará com que o login do usuário vinculado seja atualizado para o CPF "
            u"correspondente, sem pontos e traço."
        ),
        "atualizar_pessoa_usuario_name": fields.boolean(
            u"Atualiza o nome do usuário ao alterar nome da pessoa",
            help=u"Atualiza o nome do usuário caso o nome da pessoa seja alterado."
        ),
        "exclusao_cascata": fields.boolean(u"Exclusão em cascata de usuário junto com pessoa",
                                           help=u"Ao excluir uma pessoa no núcleo, seu usuário será excluído junto."),
    }

    # Criação de usuário pelo CPF
    def get_default_criar_login_cpf(self, cr, uid, fields, context=None):
        return {
            "criar_login_cpf": ConfiguracaoUsuarioUD.get_criar_login_cpf(self, cr, uid, context)
        }

    @staticmethod
    def get_criar_login_cpf(cls, cr, uid, context=None):
        config_parameters = cls.pool.get('ir.config_parameter')
        return safe_eval(config_parameters.get_param(cr, uid, 'ud.usuario_criar_login_cpf', 'True', context=context))

    def set_criar_login_cpf(self, cr, uid, ids, context=None):
        config_parameters = self.pool.get("ir.config_parameter")
        for config in self.browse(cr, uid, ids, context=context):
            config_parameters.set_param(cr, uid, 'ud.usuario_criar_login_cpf', repr(config.criar_login_cpf))

    # Criação de pessoa a partir de login com CPF válido
    def get_default_criar_pessoa_usuario(self, cr, uid, fields, context=None):
        return {
            "criar_pessoa_usuario": ConfiguracaoUsuarioUD.get_criar_pessoa_usuario(self, cr, uid, context)
        }

    @staticmethod
    def get_criar_pessoa_usuario(cls, cr, uid, context=None):
        config_parameters = cls.pool.get('ir.config_parameter')
        return safe_eval(
            config_parameters.get_param(cr, uid, 'ud.usuario_criar_pessoa_usuario', 'False', context=context))

    def set_criar_pessoa_usuario(self, cr, uid, ids, context=None):
        config_parameters = self.pool.get("ir.config_parameter")
        for config in self.browse(cr, uid, ids, context=context):
            config_parameters.set_param(cr, uid, 'ud.usuario_criar_pessoa_usuario', repr(config.criar_pessoa_usuario))

    # Atualização de Login de usuário pelo CPF
    def get_default_atualizar_login_cpf(self, cr, uid, fields, context=None):
        return {
            "atualizar_login_cpf": ConfiguracaoUsuarioUD.get_atualizar_login_cpf(self, cr, uid, context)
        }

    @staticmethod
    def get_atualizar_login_cpf(cls, cr, uid, context=None):
        config_parameters = cls.pool.get('ir.config_parameter')
        return safe_eval(config_parameters.get_param(cr, uid, 'ud.usuario_atualizar_login_cpf', 'True', context=context))

    def set_atualizar_login_cpf(self, cr, uid, ids, context=None):
        config_parameters = self.pool.get("ir.config_parameter")
        for config in self.browse(cr, uid, ids, context=context):
            config_parameters.set_param(cr, uid, 'ud.usuario_atualizar_login_cpf', repr(config.atualizar_login_cpf))

    # Atualizar nome de usuário ao alterar nome da pessoa
    def get_default_atualizar_pessoa_usuario_name(self, cr, uid, fields, context=None):
        return {
            "atualizar_pessoa_usuario_name": ConfiguracaoUsuarioUD.get_atualizar_pessoa_usuario_name(self, cr, uid, context)
        }

    @staticmethod
    def get_atualizar_pessoa_usuario_name(cls, cr, uid, context=None):
        config_parameters = cls.pool.get('ir.config_parameter')
        return safe_eval(config_parameters.get_param(cr, uid, 'ud.usuario_atualizar_pessoa_usuario_name', 'True', context=context))

    def set_atualizar_pessoa_usuario_name(self, cr, uid, ids, context=None):
        config_parameters = self.pool.get("ir.config_parameter")
        for config in self.browse(cr, uid, ids, context=context):
            config_parameters.set_param(cr, uid, 'ud.usuario_atualizar_pessoa_usuario_name', repr(config.atualizar_pessoa_usuario_name))

    # Exclusão de usuário junto com pessoa
    def get_default_exclusao_cascata(self, cr, uid, fields, context=None):
        return {
            "exclusao_cascata": ConfiguracaoUsuarioUD.get_exclusao_cascata(self, cr, uid, context)
        }

    @staticmethod
    def get_exclusao_cascata(cls, cr, uid, context=None):
        config_parameters = cls.pool.get('ir.config_parameter')
        return safe_eval(config_parameters.get_param(cr, uid, 'ud.usuario_exclusao_cascata', 'True', context=context))

    def set_exclusao_cascata(self, cr, uid, ids, context=None):
        config_parameters = self.pool.get("ir.config_parameter")
        for config in self.browse(cr, uid, ids, context=context):
            config_parameters.set_param(cr, uid, 'ud.usuario_exclusao_cascata', repr(config.exclusao_cascata))


class UsuarioUD(osv.Model):
    _inherit = "res.users"

    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if not context.get("usuario_ud", False):
            return super(UsuarioUD, self).create(cr, uid, vals, context)
        vals["tz"] = vals.get("tz", "America/Maceio")
        pessoa_model = self.pool.get("ud.employee")
        cpf = vals.get("login", False)
        combinacao = self.combinacao_cpf(cpf)
        pessoa = None
        if cpf and combinacao:
            vals["login"] = cpf.replace(".", "").replace("-", "")
            combinacao = combinacao.groups()
            cpf = ".".join(combinacao[:-1]) + "-" + combinacao[-1]
            pessoa = pessoa_model.search(cr, SUPERUSER_ID, [("cpf", "=", cpf)])
            if pessoa:
                pessoa = pessoa_model.browse(cr, SUPERUSER_ID, pessoa[0], context)
                if pessoa.user_id:
                    raise osv.except_osv(u"Usuário existente",
                                         u"Existe uma uma pessoa com o CPF informado com vínculo com outro usuário.")
        res = super(UsuarioUD, self).create(cr, uid, vals, context)
        if combinacao:
            context["nao_criar_usuario"] = True
            if pessoa:
                dados = {}
                if not getattr(pessoa, "user_id", None):
                    dados = {"user_id": res}
                if "name" in vals:
                    dados["name"] = vals["name"]
                if dados:
                    pessoa.write(dados)
                    group = self.pool.get("ir.model.data").get_object(
                        cr, SUPERUSER_ID, "base", "usuario_ud", context
                    )
                    group.write({"users": [(4, res)]})
            elif ConfiguracaoUsuarioUD.get_criar_pessoa_usuario(self, cr, uid, context):
                dados = {
                    "name": vals.get("name", False), "cpf": cpf, "work_email": vals.get("email", False), "user_id": res,
                }
                pessoa_model.create(cr, SUPERUSER_ID, dados, context)
                group = self.pool.get("ir.model.data").get_object(
                    cr, SUPERUSER_ID, "base", "usuario_ud", context
                )
                group.write({"users": [(4, res)]})
        return res

    def write(self, cr, uid, ids, vals, context=None):
        context = context or {}
        if not context.get("usuario_ud", False):
            return super(UsuarioUD, self).write(cr, uid, ids, vals, context)
        if isinstance(ids, (int, long)):
            ids = [ids]
        pessoa_model = self.pool.get("ud.employee")
        cpf = vals.get("login", False)
        res = False
        if cpf:
            combinacao = self.combinacao_cpf(cpf)
            if combinacao:
                vals["login"] = cpf.replace(".", "").replace("-", "")
                res = super(UsuarioUD, self).write(cr, uid, ids, vals, context)
                context["nao_criar_usuario"] = True
                pessoa_atual = pessoa_model.search(cr, SUPERUSER_ID, [("user_id", "in", ids)], context=context)
                if len(pessoa_atual) > 1:
                    raise osv.except_osv(u"Multiplos usuários", u"Há multiplas pessoas vinculadas ao mesmo usuário.")
                pessoa_atual = pessoa_atual and pessoa_atual[0] or False
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
                        group = self.pool.get("ir.model.data").get_object(
                            cr, SUPERUSER_ID, "base", "usuario_ud", context
                        )
                        group.write({"users": [(4, ids[0])]})
                    elif pessoa_atual == pessoa.id and dados:
                        pessoa.write(dados)
                    elif pessoa_atual:
                        raise osv.except_osv(
                            u"Conflito", u"O CPF digitado está vinculado a um usuário de outra pessoa."
                        )
                elif pessoa_atual:
                    pessoa_atual = pessoa_model.browse(cr, SUPERUSER_ID, pessoa_atual, context)
                    dados = {}
                    if "name" in vals:
                        dados["name"] = vals["name"]
                    if pessoa_atual.cpf != cpf and dados:
                        dados["cpf"] = cpf
                        pessoa_atual.write(dados)
                elif ConfiguracaoUsuarioUD.get_criar_pessoa_usuario(self, cr, uid, context):
                    usuario = self.browse(cr, uid, ids[0], context)
                    dados = {
                        "name": usuario.name, "cpf": cpf, "work_email": usuario.email, "user_id": ids[0],
                    }
                    pessoa_model.create(cr, SUPERUSER_ID, dados, context)
                    group = self.pool.get("ir.model.data").get_object(
                        cr, SUPERUSER_ID, "base", "usuario_ud", context
                    )
                    group.write({"users": [(4, ids[0])]})
        return res or super(UsuarioUD, self).write(cr, uid, ids, vals, context)

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

