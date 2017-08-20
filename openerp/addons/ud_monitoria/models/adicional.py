# coding: utf-8
from datetime import datetime

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class Curso(osv.Model):
    _name = "ud.curso"
    _description = u"Extensão de Curso (UD)"
    _inherit = "ud.curso"

    _columns = {
        "coord_monitoria_id": fields.many2one("ud.employee", u"Coordenador de Monitoria"),
    }

    _sql_constraints = [
        ("coord_monitoria_unico", "unique(coord_monitoria_id)",
         u"Uma pessoa pode ser coordenador de monitoria de apenas 1 curso."),
    ]

    def create(self, cr, uid, vals, context=None):
        """
        === Extensão do método osv.Model.create
        Verifica se foi vinculado alguém como coordenador de monitoria de um curso para adicioná-lo ao grupo de segurança
        correspondente.
        """
        res = super(Curso, self).create(cr, uid, vals, context)
        if vals.get("coord_monitoria_id", False):
            group = self.pool.get("ir.model.data").get_object(
                cr, SUPERUSER_ID, "ud_monitoria", "group_ud_monitoria_coord_disciplina", context
            )
            usuario = self.pool.get("ud.employee").browse(cr, uid, vals["coord_monitoria_id"], context).user_id
            if usuario:
                group.write({"users": [(4, usuario.id)]})
        return res

    def write(self, cr, uid, ids, vals, context=None):
        """
        === Extensão do método osv.Model.write
        Verifica a alteração do coordenador de monitoria de um curso. Se adicionado, esse será inserido no grupo de
        segurança correspodente. Se modificado, o anterior e retirado do grupo de segurança e o novo é adicionado. Se
        o orientador é retirado, então também é removido do grupo de segurança.

        :attention: Antes de remover qualquer orientador do grupo de segurança, é verificado se esse não possui nenhum
        vínculo com outros cursos.
        """
        if "coord_monitoria_id" in vals:
            coordenadores_antigos = []
            for curso in self.browse(cr, uid, ids, context):
                if curso.coord_monitoria_id.user_id:
                    coordenadores_antigos.append(curso.coord_monitoria_id)
            super(Curso, self).write(cr, uid, ids, vals, context)
            group = self.pool.get("ir.model.data").get_object(
                cr, SUPERUSER_ID, "ud_monitoria", "group_ud_monitoria_coord_disciplina", context
            )
            if vals.get("coord_monitoria_id", False):
                user = self.pool.get("ud.employee").browse(cr, uid, vals["coord_monitoria_id"], context)
                if user.user_id:
                    user = user.user_id.id
                    group.write({"users": [(4, user)]})
                    for coord in coordenadores_antigos:
                        if coord.user_id:
                            if (coord.user_id.id != user and self.search_count(
                                    cr, uid, [("coord_monitoria_id", "=", coord.id)]) == 0):
                                group.write({"users": [(3, coord.user_id.id)]})
            else:
                for coord in coordenadores_antigos:
                    if coord.user_id:
                        if self.search_count(cr, uid, [("coord_monitoria_id", "=", coord.id)]) == 0:
                            group.write({"users": [(3, coord.user_id.id)]})
            return True
        return super(Curso, self).write(cr, uid, ids, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        """
        === Extensão do método osv.Model.unlink
        Virifica se o coordenador de monitoria do curso não possui vínculos com outras disciplinas para essa função e
        remove-o do grupo de segurança correspondente.
        """
        coordenadores = [curso.coord_monitoria_id for curso in self.browse(cr, uid, ids, context)]
        super(Curso, self).unlink(cr, uid, ids, context)
        group = self.pool.get("ir.model.data").get_object(
            cr, SUPERUSER_ID, "ud_monitoria", "group_ud_monitoria_coord_disciplina", context
        )
        for coordenador in coordenadores:
            if self.search_count(cr, uid, [("coord_monitoria_id", "=", coordenador.id)]) == 0:
                if coordenador.user_id:
                    group.write({"users": [(3, coordenador.user_id.id)]})
        return True


class Disciplina(osv.Model):
    _name = "ud.monitoria.disciplina"
    _description = u"Disciplinas de monitoria (UD)"
    
    def get_discentes(self, cr, uid, ids, campo, args, context=None):
        """
        Busca todos os discentes e separa-os em um dicionário de acordo com seu status e seu campo correspondente.
        """
        doc_model = self.pool.get("ud.monitoria.documentos.discente")
        res = {}
        for disc_id in ids:
            res[disc_id] = {
                "bolsista_ids": doc_model.search(cr, uid, [("disciplina_id", "=", disc_id), ("state", "=", "bolsista")], context=context),
                "n_bolsista_ids": doc_model.search(cr, uid, [("disciplina_id", "=", disc_id), ("state", "=", "n_bolsista")], context=context),
                "reserva_ids": doc_model.search(cr, uid, [("disciplina_id", "=", disc_id), ("state", "=", "reserva")], context=context),
                "desligado_ids": doc_model.search(cr, uid, [("disciplina_id", "=", disc_id), ("state", "=", "desligado")], context=context),
            }
        return res

    def valida_datas(self, cr, uid, ids, context=None):
        """
        Valida se a data inicial ocorre antes ou é igual a final.
        """
        for disc in self.browse(cr, uid, ids, context=context):
            if datetime.strptime(disc.data_inicial, DEFAULT_SERVER_DATE_FORMAT) >= datetime.strptime(disc.data_final, DEFAULT_SERVER_DATE_FORMAT):
                return False
        return True

    def valida_disciplina_ps(self, cr, uid, ids, context=None):
        """
        Verifica a validade para as disciplinas duplicadas em um processo seletivo.
        """
        for disc in self.browse(cr, uid, ids, context=context):
            args = [("curso_id", "=", disc.curso_id.id), ("disciplina_id", "=", disc.disciplina_id.id),
                    ("id", "!=", disc.id), ("processo_seletivo_id", "=", disc.processo_seletivo_id.id)]
            if self.search_count(cr, uid, args, context) > 0:
                return False
        return True

    _columns = {
        "id": fields.integer("ID", readonly=True, invisible=True),
        "curso_id": fields.many2one("ud.curso", u"Curso", required=True, ondelete="restrict",
                                    domain=[('is_active','=',True)]),
        "disciplina_id": fields.many2one("ud.disciplina", u"Disciplinas", required=True, ondelete="restrict",
                                         domain="[('ud_disc_id','=',curso_id)]"),
        "perfil_id": fields.many2one("ud.perfil", u"SIAPE", required=True, ondelete="restrict",
                                     domain="[('tipo', '=', 'p'), ('ud_cursos', '=', curso_id)]",
                                     help=u"SIAPE do professor Orientador"),
        "orientador_id": fields.related("perfil_id", "ud_papel_id", type="many2one", relation="ud.employee",
                                        string=u"Orientador", readonly=True),
        "data_inicial": fields.date(u"Data Inicial", required=True),
        "data_final": fields.date(u"Data Final", required=True),
        "bolsas": fields.integer(u"Bolsas disponíveis", help=u"Número de bolsas que serão disponibilizadas para a disciplina"),
        "monitor_s_bolsa": fields.integer(u"Vagas sem bolsa (Monitor)"),
        "tutor_s_bolsa": fields.integer(u"Vagas sem bolsa (Tutor)"),
        "processo_seletivo_id": fields.many2one("ud.monitoria.processo.seletivo", u"Processo Seletivo",
                                                ondelete="cascade"),
        "semestre_id": fields.related("processo_seletivo_id", "semestre_id", type="many2one", string=u"Semestre",
                                      relation="ud.monitoria.registro", readonly=True),
        "bolsista_ids": fields.function(get_discentes, type="many2many", relation="ud.monitoria.documentos.discente",
                                        string=u"Bolsistas", multi="_discentes"),
        "n_bolsista_ids": fields.function(get_discentes, type="many2many", relation="ud.monitoria.documentos.discente",
                                          string=u"Não Bolsistas", multi="_discentes"),
        "reserva_ids": fields.function(get_discentes, type="many2many", relation="ud.monitoria.documentos.discente",
                                       string=u"Cadastro de Reserva", multi="_discentes"),
        "desligado_ids": fields.function(get_discentes, type="many2many", relation="ud.monitoria.documentos.discente",
                                         string=u"Cadastro de Reserva", multi="_discentes"),
        "is_active": fields.boolean(u"Ativo", readonly=True),
    }

    _defaults = {
        "is_active": True,
    }
    
    _constraints = [
        (valida_datas, u"A data inicial da disciplina deve ocorrer antes da final", [u"Data Inicial e Data Final"]),
        (valida_disciplina_ps, u"Não é permitido duplicar disciplinas em um mesmo processo seletivo", [u"Disciplinas"]),
    ]

    _sql_constraints = [
        ("disciplina_processo_seletivo_unica", "unique(disciplina_id,processo_seletivo_id)",
         u"Essa disciplina já possui vínculo com o processo seletivo especificado."),
    ]
    
    def name_get(self, cr, uid, ids, context=None):
        """
        === Sobrescrita do método osv.Model.name_get
        As informações de visualização desse modelo em campos many2one será o nome da disciplina do núcleo.
        """
        return [(disc.id, disc.disciplina_id.name) for disc in self.browse(cr, uid, ids, context=context)]
    
    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        """
        === Sobrescrita do método osv.Model.name_search
        Ao realizar pesquisas em campos many2one para esse modelo, os dados inseridos serão utilizados para pesquisar a
        discplina no núcleo e fazer referência com o modelo atual.
        """
        if not isinstance(args, (list, tuple)):
            args = []
        if not (name == '' and operator == 'ilike'):
            disciplinas_ids = self.pool.get("ud.disciplina").search(cr, uid, [("name", operator, name)], context=context)
            args += [("disciplina_id", "in", disciplinas_ids)]
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def default_get(self, cr, uid, fields_list, context=None):
        """
        === Extensão do método osv.Model.default_get
        Adiciona um curso padrão no campo correspondente quando disciplina for criada por usando o filtro de coordenador
        de monitoria de algum curso.
        """
        context = context or {}
        res = super(Disciplina, self).default_get(cr, uid, fields_list, context)
        if context.get("filtro_coord_disciplina", False):
            if not context.get("semestre_id", False):
                return res
            pessoas = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)], context=context)
            if pessoas:
                cs = self.pool.get("ud.curso").search(cr, uid, [("coord_monitoria_id", "in", pessoas)], context=context)
                if not cs:
                    return res
                cs = cs[0]
                registro = self.pool.get("ud.monitoria.registro").browse(cr, uid, context["semestre_id"], context)
                for dist in registro.distribuicao_bolsas_ids:
                    if dist.curso_id.id == cs:
                        res["curso_id"] = cs
                        break
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        """
        === Extensão do método osv.Model.fields_view_get
        Define o filtro de cursos com de acordo com os que estão listados nas configurações do semestre para definir
        quantas bolsas cada um possui. Caso seja definido para filtrar pelo coordenador do curso de monitoria usando
        o marcador em context, essa lista, já filtrada, será limitada aos cursos que o usuário logado é o coordenador
        de monitoria.
        """
        context = context or {}
        res = super(Disciplina, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        domain_temp = res["fields"]["curso_id"].get("domain", [])
        if isinstance(domain_temp, str):
            domain_temp = list(eval(domain_temp))
        domain = []
        for d in domain_temp:
            if d[0] != "id":
                domain.append(d)
        del domain_temp
        cursos = []
        if context.get("semestre_id", None):
            bolsas_distribuidas = self.pool.get("ud.monitoria.registro").browse(
                cr, SUPERUSER_ID, context.get("semestre_id", None), context
            ).distribuicao_bolsas_ids
            for dist in bolsas_distribuidas:
                cursos.append(dist.curso_id.id)
            if context.get("filtro_coord_disciplina", False):
                pessoas = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)],
                                                              context=context)
                if pessoas:
                    cursos = self.pool.get("ud.curso").search(
                        cr, uid, [("id", "=", cursos), ("coord_monitoria_id", "in", pessoas)], context=context
                    )
        domain += [("id", "in", cursos)]
        res["fields"]["curso_id"]["domain"] = domain
        return res

    def create(self, cr, uid, vals, context=None):
        """
        === Extensão do método osv.Model.create
        Adiciona orientador ao grupo de segurança correspondente.

        :raise osv.except_osv: Caso o perfil de orientador não esteja vinculado a um usuário.
        """
        res = super(Disciplina, self).create(cr, uid, vals, context)
        disciplina = self.browse(cr, uid, res, context)
        group = self.pool.get("ir.model.data").get_object(
            cr, SUPERUSER_ID, "ud_monitoria", "group_ud_monitoria_orientador", context
        )
        if not disciplina.orientador_id.user_id:
            raise osv.except_osv("Usuário não encontrado",
                                 "O registro de \"%s\" no núcle o não está vinculado a um usuário (login)." % disciplina.orientador_id.name)
        group.write({"users": [(4, disciplina.orientador_id.user_id.id)]})
        return res

    def write(self, cr, uid, ids, vals, context=None):
        """
        === Extensão do método osv.Model.write
        Se orientador for modificado, adiciona-o ao grupo de segurança correspondente.

        :raise osv.except_osv: Caso o perfil de orientador não esteja vinculado a um usuário.
        """
        super(Disciplina, self).write(cr, uid, ids, vals, context)
        if "orientador_id" in vals or "siape" in vals:
            group = self.pool.get("ir.model.data").get_object(
                cr, SUPERUSER_ID, "ud_monitoria", "group_ud_monitoria_orientador", context
            )
            add = []
            for disciplina in self.browse(cr, uid, ids if isinstance(ids, (list, tuple)) else [ids], context):
                if not disciplina.orientador_id.user_id:
                    raise osv.except_osv("Usuário não encontrado",
                                         "O registro de \"%s\" no núcle o não está vinculado a um usuário (login)." % disciplina.orientador_id.name)
                add.append((4, disciplina.orientador_id.user_id.id))
            group.write({"users": add})
        return True

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        """
        === Extensão do método osv.Model.search
        Foi adicionado a opção de filtrar as disciplinas em que o usuário logado esteja vinculado como coordenador de
        monitoria do curso correspondente.
        """
        if (context or {}).get("filtro_coord_disciplina", False):
            pessoas = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)], context=context)
            if not pessoas:
                return []
            cursos = self.pool.get("ud.curso").search(cr, SUPERUSER_ID, [("coord_monitoria_id", "in", pessoas)])
            args = (args or []) + [("curso_id", "in", cursos)]
        return super(Disciplina, self).search(cr, uid, args, offset, limit, order, context, count)

    def atualiza_status_cron(self, cr, uid, context=None):
        """
        Método de atualização do status da disciplina caso essa tenha sua data de finalização tenha sido ultrapassada
        usando o modelo "ir.cron".
        """
        disc = self.search(cr, uid, [("data_final", "<", datetime.utcnow().strftime("%Y-%m-%d")),
                                     ("is_active", "=", True)])
        if disc:
            self.write(cr, SUPERUSER_ID, disc, {"is_active": False}, context)
        return True

    def onchange_perfil(self, cr, uid, ids, perfil_id, context=None):
        """
        Método usado para atualizar os dados do campo "orientador_id" caso "perfil_id" seja modificado.
        """
        if perfil_id:
            return {"value": {"orientador_id": self.pool.get("ud.perfil").read(
                cr, SUPERUSER_ID, perfil_id, ["ud_papel_id"], context=context
            ).get("ud_papel_id")}}
        return {"value": {"orientador_id": False}}
