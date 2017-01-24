# coding: utf-8
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

from datetime import datetime


class Curso(osv.Model):
    _name = "ud.curso"
    _description = u"Extensão de Curso (UD)"
    _inherit = "ud.curso"

    _TURNO = [("d", u"Diurno"), ("m", u"Matutino"),
              ("v", u"Vespertino"), ("n", u"Noturno"),]
    _MODALIDADE = [("l", u"Licenciatura"), ("b", u"Bacharelado")]

    _columns = {
        'coord_monitoria_id': fields.many2one('ud.employee', u'Coordenador de Monitoria'),
        "turno": fields.selection(_TURNO, u"Turno", required=True),
        "modalidade": fields.selection(_MODALIDADE, u"Modalidade", required=True),
    }

    def create(self, cr, uid, vals, context=None):
        res = super(Curso, self).create(cr, uid, vals, context)
        if vals.get("coord_monitoria_id", False):
            try:
                group = self.pool.get("ir.model.data").get_object(
                    cr, SUPERUSER_ID, "ud_monitoria", "group_ud_monitoria_coord_disciplina", context
                )
                usuario = self.pool.get("ud.employee").browse(cr, uid, vals["coord_monitoria_id"], context).user_id.id
                group.write({"users": [(4, usuario)]})
            except ValueError:
                pass
        return res

    def write(self, cr, uid, ids, vals, context=None):
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
                        try:
                            if (coord.user_id.id != user and self.search_count(
                                    cr, uid, [("coord_monitoria_id", "=", coord.id)]) == 0):
                                group.write({"users": [(3, coord.user_id.id)]})
                        except ValueError:
                            pass
            else:
                for coord in coordenadores_antigos:
                    try:
                        if self.search_count(cr, uid, [("coord_monitoria_id", "=", coord.id)]) == 0:
                            group.write({"users": [(3, coord.user_id.id)]})
                    except ValueError:
                        pass
            return True
        return super(Curso, self).write(cr, uid, ids, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        coordenadores = [curso.coord_monitoria_id for curso in self.browse(cr, uid, ids, context)]
        super(Curso, self).unlink(cr, uid, ids, context)
        group = self.pool.get("ir.model.data").get_object(
            cr, SUPERUSER_ID, "ud_monitoria", "group_ud_monitoria_coord_disciplina", context
        )
        for coordenador in coordenadores:
            if self.search_count(cr, uid, [("coord_monitoria_id", "=", coordenador.id)]) == 0:
                try:
                    group.write({"users": [(3, coordenador.user_id.id)]})
                except ValueError:
                    pass
        return True


class InfoDisciplina(osv.AbstractModel):
    _name = "ud.monitoria.info.disciplina"
    _description = u"Disciplina de monitoria (UD)"
    
    def get_orientador(self, cr, uid, ids, campos, arg, context=None):
        perfil_model = self.pool.get("ud.perfil")
        res = {}
        for inf_disc in self.read(cr, uid, ids, ["siape"], context=context, load="_classic_write"):
            papel_id = perfil_model.search(cr, SUPERUSER_ID, [("matricula", "=", inf_disc["siape"]),
                                                                ("tipo", "=", "p")], context=context)
            if papel_id:
                res[inf_disc.get("id")] = perfil_model.read(cr, SUPERUSER_ID, papel_id[0], ["ud_papel_id"], context=context).get("ud_papel_id")
        return res

    def bolsas_disponiveis(self, cr, uid, ids, campo, args, context=None):
        oferta_model = self.pool.get("ud.monitoria.oferta.disciplina")
        res = {}
        for disciplina in self.read(cr, uid, ids, ["curso_id", "disciplina_id"], context=context, load="_classic_write"):
            ofertas_ids = oferta_model.search(cr, uid, [
                ("curso_id", "=", disciplina["curso_id"]),
                ("disciplina_id", "=", disciplina["disciplina_id"])
            ], context=context)
            if ofertas_ids:
                res[disciplina["id"]] = oferta_model.read(cr, uid, ofertas_ids[0], ["bolsas_disponiveis"],
                                                          context=context, load="_classic_write")["bolsas_disponiveis"]
            else:
                res[disciplina["id"]] = 0
        return res

    def valida_datas(self, cr, uid, ids, context=None):
        for disc in self.browse(cr, uid, ids, context=context):
            if datetime.strptime(disc.data_inicial, DEFAULT_SERVER_DATE_FORMAT) >= datetime.strptime(disc.data_final, DEFAULT_SERVER_DATE_FORMAT):
                return False
        return True

    _columns = {
        "curso_id": fields.many2one("ud.curso", u"Curso", required=True, ondelete="restrict",
                                    domain="[('modalidade','!=',False),('is_active','=',True)]"),
        "disciplina_id": fields.many2one("ud.disciplina", u"Disciplina", required=True, ondelete="restrict",
                                         domain="[('ud_disc_id','=',curso_id)]"),
        "siape": fields.char(u"SIAPE", required=True, help=u"SIAPE do professor Orientador"),
        "orientador_id": fields.many2one("ud.employee", u"Orientador", ondelete="restrict", readonly=True),
        "data_inicial": fields.date(u"Data Inicial", required=True),
        "data_final": fields.date(u"Data Final", required=True),
        "num_bolsas": fields.function(bolsas_disponiveis, type="integer", string=u"Bolsas disponíveis"),
        "is_active": fields.boolean(u"Ativo", readonly=True),
    }

    _defaults = {
        "is_active": True,
    }
    
    _constraints = [
        (valida_datas, u"A data inicial da disciplina deve ocorrer antes da final", [u"Data Inicial e Data Final"])
    ]
    
    def name_get(self, cr, uid, ids, context=None):
        return [(disc.id, disc.disciplina_id.name) for disc in self.browse(cr, uid, ids, context=context)]
    
    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        if not isinstance(args, (list, tuple)):
            args = []
        if not (name == '' and operator == 'ilike'):
            disciplinas_ids = self.pool.get("ud.disciplina").search(cr, uid, [("name", operator, name)], context=context)
            args += [("disciplina_id", "in", disciplinas_ids)]
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def create(self, cr, uid, vals, context=None):
        perfil_model = self.pool.get("ud.perfil")
        papel_id = perfil_model.search(cr, SUPERUSER_ID, [("matricula", "=", vals.get("siape", False)),
                                                          ("tipo", "=", "p")], context=context)
        if not papel_id:
            raise osv.except_osv(u"SIAPE inválido", u"Não foi encontrado ninguém com esse SIAPE.")
        vals["orientador_id"] = perfil_model.read(cr, SUPERUSER_ID, papel_id[0], ["ud_papel_id"], load="_classic_write",
                                                  context=context).get("ud_papel_id")
        return super(InfoDisciplina, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if "siape" in vals:
            perfil_model = self.pool.get("ud.perfil")
            papel_id = perfil_model.search(cr, SUPERUSER_ID, [("matricula", "=", vals.get("siape", False)),
                                                              ("tipo", "=", "p")], context=context)
            if not papel_id:
                raise osv.except_osv(u"SIAPE inválido", u"Não foi encontrado nenhum discente com esse SIAPE.")
            vals["orientador_id"] = perfil_model.read(cr, SUPERUSER_ID, papel_id[0], ["ud_papel_id"],
                                                      load="_classic_write", context=context).get("ud_papel_id")
        return super(InfoDisciplina, self).write(cr, uid, ids, vals, context)

    def onchange_siape(self, cr, uid, ids, siape, context=None):
        if siape:
            perfil_model = self.pool.get("ud.perfil")
            papel_id = perfil_model.search(cr, SUPERUSER_ID, [("matricula", "=", siape),
                                                              ("tipo", "=", "p")], context=context)
            if papel_id:
                return {"value": {"orientador_id": perfil_model.read(cr, SUPERUSER_ID, papel_id[0], ["ud_papel_id"], context=context).get("ud_papel_id")}}
        return {"value": {"orientador_id": False, "siape": False},
                "warning": {"title": u"Alerta",
                            "message": u"SIAPE informado inexistente."}}


class OfertaDisciplina(osv.Model):
    _name = "ud.monitoria.oferta.disciplina"
    _description = u"Oferta de disciplina (UD)"
    _order = "curso_id asc, disciplina_id asc"

    def disciplina_uso(self, cr, uid, ids, context=None):
        ps_model = self.pool.get("ud.monitoria.processo.seletivo")
        disc_ids = []
        for ps in ps_model.browse(cr, uid, ps_model.search(cr, uid, [("state", "in", ["novo", "andamento"])],
                                                           context=context), context):
            for disc in ps.disciplinas_ids:
                disc_ids.append(disc.disciplina_id.id)
        for disc in self.read(cr, uid, ids, ["disciplina_id"], load="_classic_write", context=context):
            if disc["disciplina_id"] in disc_ids:
                return True
        return False

    def get_em_oferta(self, cr, uid, ids, nome_campo, arg, context=None):
        res = {}
        for oferta in self.browse(cr, uid, ids, context=context):
            if oferta.curso_id.is_active:
                cr.execute("SELECT em_oferta FROM ud_monitoria_oferta_disciplina WHERE id = {};".format(oferta.id))
                res[oferta.id] = cr.fetchall()[0][0]
            else:
                if self.disciplina_uso(cr, uid, ids, context):
                    raise osv.except_osv(u"Disciplina em Uso",
                                         u"A disciplina não pode deixar de ser ofertada enquanto estiver em uso por "
                                         u"novos Processos Seletivos ou em andamento.")
                res[oferta.id] = False
        return res
    
    def set_em_oferta(self, cr, uid, ids, nome_campo, valor_campo, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if self.disciplina_uso(cr, uid, ids, context) and not valor_campo:
            raise osv.except_osv(u"Disciplina em Uso",
                                 u"A disciplina não pode deixar de ser ofertada enquanto estiver em uso por "
                                 u"novos Processos Seletivos ou em andamento.")
        sql = "UPDATE ud_monitoria_oferta_disciplina SET em_oferta = {} WHERE id = {};"
        for id_oferta in ids:
            cr.execute(sql.format(valor_campo, id_oferta))
        return True
    
    def update_em_oferta(self, cr, uid, ids, context=None):
        curso_ids = self.search(cr, uid, [("id", "in", ids), ("is_active", "=", False)], context=context)
        return self.pool.get("ud.monitoria.oferta.disciplina").search(
            cr, uid, [("em_oferta", "=", True), ("curso_id", "in", curso_ids)]
        )
    
    def valida_em_oferta(self, cr, uid, ids, context=None):
        for oferta in self.browse(cr, uid, ids, context=context):
            if oferta.curso_id.is_active==False and oferta.em_oferta == True:
                return False
        return True
    
    def valida_bolsas(self, cr, uid, ids, context=None):
        for oferta in self.browse(cr, uid, ids, context=context):
            if oferta.bolsas_disponiveis < 0:
                return False
        return True
    
    _columns = {
        "curso_id": fields.many2one("ud.curso", u"Curso", required=True, ondelete="restrict",
                                    domain="[('modalidade','!=',False),('is_active','=',True)]"),
        "disciplina_id": fields.many2one("ud.disciplina", u"Disciplina", required=True, ondelete="restrict",
                                         domain="[('ud_disc_id', '=', curso_id)]"),
        "em_oferta": fields.function(get_em_oferta, fnct_inv=set_em_oferta, type="boolean", string=u"Em oferta",
                                     method=True, help=u"Define se essa disciplina está em oferta.",
                                     store={"ud.curso": (update_em_oferta, ["is_active"], 10)}),
        "bolsas_disponiveis": fields.integer(u"Bolsas disponíveis", required=True),
    }
    
    _constraints = [
        (valida_em_oferta, u"Não é possível ofertar uma disciplina que pertence a um curso inativo!", [u"Em oferta"]),
        (valida_bolsas, u"Não é permitido valores negativos no número de bolsas!", [u"Bolsas disponíveis"]),
    ]
    
    _sql_constraints = [
        ("oferta_curso_disc_unique", "unique(curso_id, disciplina_id)",
         u"A oferta dessa disciplina já foi criada, faça uma busca para realizar suas alterações!"),
    ]
    
    def name_get(self, cr, uid, ids, context=None):
        return [(disc.id, disc.disciplina_id.name) for disc in self.browse(cr, uid, ids, context=context)]
    
    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        if not isinstance(args, (list, tuple)):
            args = []
        if not (name == '' and operator == 'ilike'):
            disciplinas_ids = self.pool.get("ud.disciplina").search(cr, uid, [("name", operator, name)], context=context)
            args += [("disciplina_id", "in", disciplinas_ids)]
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)
    
    def onchange_curso(self, cr, uid, ids, context=None):
        return {"value": {"disciplina_id": False}}


class Disciplina(osv.Model):
    _name = "ud.monitoria.disciplina"
    _inherit = "ud.monitoria.info.disciplina"
    _order = "is_active desc, semestre_id"

    def discentes(self, cr, uid, ids, campo, args, context=None):
        doc_model = self.pool.get("ud.monitoria.documentos.discente")
        res = {}
        for disc_id in ids:
            res[disc_id] = {
                "bolsista_ids": doc_model.search(cr, uid, [("disciplina_id", "=", disc_id), ("state", "=", "bolsista")], context=context),
                "n_bolsista_ids": doc_model.search(cr, uid, [("disciplina_id", "=", disc_id), ("state", "=", "n_bolsista")], context=context),
                "reserva_ids": doc_model.search(cr, uid, [("disciplina_id", "=", disc_id), ("state", "=", "reserva")], context=context),
            }
        return res

    def orientador(self, cr, uid, ids, campo, args, context=None):
        orientador_model = self.pool.get("ud.monitoria.orientador")
        res = {}
        for disc in self.browse(cr, uid, ids, context):
            orientador = orientador_model.search(cr, uid, [("matricula", "=", disc.siape), ("tipo", "=", "p")])
            if orientador:
                res[disc.id] = orientador[0]
        return res

    def _vagas(self, cr, uid, ids, campo, args, context=None):
        res = {}
        ps_model = self.pool.get("ud.monitoria.processo.seletivo")
        for disc in self.browse(cr, uid, ids, context):
            ps = ps_model.search(cr, uid, [("semestre_id", "=", disc.semestre_id.id)])
            res[disc.id] = {"tutor_s_bolsa": 0, "monitor_s_bolsa": 0}
            if ps:
                for ps in ps_model.browse(cr, uid, ps, context):
                    for disc_ps in ps.disciplinas_ids:
                        if disc_ps.disciplina_id.id == disc.disciplina_id.id:
                            res[disc.id]["tutor_s_bolsa"] += disc_ps.tutor_s_bolsa
                            res[disc.id]["monitor_s_bolsa"] += disc_ps.monitor_s_bolsa
                            break
        return res

    def _update_vagas(self, cr, uid, ids, context=None):
        if self._name == "ud.monitoria.processo.seletivo":
            semestres = [
                ps["semestre_id"]
                for ps in self.read(cr, uid, ids, ["semestre_id"], context, "_classic_write")
            ]
            return self.pool.get("ud.monitoria.disciplina").search(cr, uid, [("semestre_id", "in", semestres)], context=context)
        return []

    _columns = {
        "orientador_monitoria_id": fields.function(orientador, type="many2one", relation="ud.monitoria.orientador",
                                                   string=u"Orientador"),
        "semestre_id": fields.many2one("ud.monitoria.registro", u"Semestre", required=True, ondelete="restrict"),
        "monitor_s_bolsa": fields.function(_vagas, type="integer", multi="vagas", string=u"Vagas sem bolsa (Monitor)",
                                           store={"ud.monitoria.processo.seletivo": (_update_vagas, ["disciplinas_ids"], 10)}),
        "tutor_s_bolsa": fields.function(_vagas, type="integer", multi="vagas", string=u"Vagas sem bolsa (Tutor)",
                                         store={"ud.monitoria.processo.seletivo": (_update_vagas, ["disciplinas_ids"], 10)}),
        "bolsista_ids": fields.function(discentes, type="many2many", relation="ud.monitoria.documentos.discente",
                                        string=u"Bolsistas", multi="_discentes"),
        "n_bolsista_ids": fields.function(discentes, type="many2many", relation="ud.monitoria.documentos.discente",
                                        string=u"Não Bolsistas", multi="_discentes"),
        "reserva_ids": fields.function(discentes, type="many2many", relation="ud.monitoria.documentos.discente",
                                        string=u"Cadastro de Reserva", multi="_discentes"),
    }

    _sql_constraints = [
        ("disciplina_semestre_orientador_unica", "unique(disciplina_id,semestre_id,orientador_id)",
         u"Não é permitido criar a mesma disciplina vinculada a um orientador no mesmo semestre."),
    ]

    def create(self, cr, uid, vals, context=None):
        res = super(Disciplina, self).create(cr, uid, vals, context)
        self.atualiza_orientador(cr, uid, [res], context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(Disciplina, self).write(cr, uid, ids, vals, context)
        self.atualiza_orientador(cr, uid, ids, context)
        return res

    def atualiza_status_cron(self, cr, uid, context=None):
        disc = self.search(cr, uid, [("data_final", "<", datetime.utcnow().strftime("%Y-%m-%d")),
                                     ("is_active", "=", True)])
        if disc:
            sql = "UPDATE ud_monitoria_disciplina SET is_active=FALSE WHERE id in (%s);" % str(disc).strip("()[],")
            cr.execute(sql)
        return True

    def atualiza_orientador(self, cr, uid, ids, context=None):
        orientador_model = self.pool.get("ud.monitoria.orientador")
        doc_orientador_model = self.pool.get("ud.monitoria.documentos.orientador")
        for disciplina in self.browse(cr, uid, ids, context):
            orientador = orientador_model.search(cr, uid, [("matricula", "=", disciplina.siape), ("tipo", "=", "p")])
            if not orientador:
                orientador_model.create(cr, uid, {"matricula": disciplina.siape, "tipo": "p",
                                                  "documentos_ids": [(0, 0, {"disciplina_id": disciplina.id})]})
            else:
                try:
                    doc_orientador_model.write(cr, uid, orientador, {"documentos_ids": [(0, 0, {"disciplina_id": disciplina.id})]})
                except:
                    pass
