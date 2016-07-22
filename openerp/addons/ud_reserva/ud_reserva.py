# coding:utf-8
from datetime import datetime, timedelta, date
import copy
import itertools
from openerp.osv import fields, osv
from openerp.osv.orm import except_orm
from openerp import SUPERUSER_ID
from dateutil.relativedelta import relativedelta


class ud_reserva(osv.osv):
    _name = 'ud.reserva'
    status = (("nova", "Nova solicitação"), ("enviada", "Encaminhado p/ Análise"), ("aprovada", "Aprovada"),
              ("cancelada", "Cancelada"),)
    freq = (("0", "Diário"), ("1", "Semanal"), ("2", "Mensal"),)
    _columns = {
        'name': fields.char('Nome', size=50, required=True),
        'state': fields.selection(status, 'Status'),
        'solicitante_id': fields.many2one('ud.employee', 'Solicitante', required=True),
        'data_solicitacao_reserva': fields.char('Data da Solicitação', required=True, readonly=True),
        'descricao_evento': fields.text('Descrição'),
        'motivo': fields.text("Motivo ", ),
        "data_cancelamento": fields.date("Data de cancelamento"),
        'espaco_id': fields.many2one('ud.espaco', 'Espaço', required=True),
        'hora_entrada': fields.datetime('Entrada', required=True),
        'hora_saida': fields.datetime('Saída', required=True),
        'periodo_final': fields.datetime('Fim'),
        'frequencia': fields.selection(freq, 'Período'),
        'teste': fields.char('Data da Solicitação', required=True, readonly=True),
        'grupo_id': fields.many2one('ud.reserva.grupo', 'Grupo de reservas', ondelete='cascade')
    }
    _defaults = {
        'data_solicitacao_reserva': lambda self, cr, uid, c: self.data_reserva(cr, uid, c),
        'teste': lambda self, cr, uid, c: self.data_teste(cr, uid, c),
        'state': "nova",
    }

    def create(self, cr, uid, vals, **kwargs):
        super(ud_reserva, self).create(cr, uid, vals)

    def read(self, cr, user, ids, fields=None, context=None, load='_classic_read'):
        employee_id = self.pool.get('ud.employee').search(cr, user, [('resource_id.user_id.id', '=', user)])
        if not len(employee_id) or user == SUPERUSER_ID:
            return super(ud_reserva, self).read(cr, user, ids)

        if type(ids) == int:
            return super(ud_reserva, self).read(cr, user, ids)

        # Verifica os espaços pelo qual ele é responsável e mostra apenas esses
        employee_id = employee_id[0]
        responsavel_id = self.pool.get('ud.reserva.responsavel').search(cr, user,
                                                                        [('responsavel_id', '=', employee_id)])
        # Busca também as reservas do qual ele é solicitante
        solicitante_reserva_ids = self.search(cr, user, [('solicitante_id', '=', employee_id)])

        if responsavel_id:
            result = []
            responsavel = self.pool.get('ud.reserva.responsavel').browse(cr, user, responsavel_id)
            for resp in responsavel:
                reserva_ids = self.search(cr, user, [('espaco_id', '=', resp.espaco_id.id)])
                # print reserva_ids
                for id in ids:
                    if id in reserva_ids or id in solicitante_reserva_ids:
                        result.append(id)
            # Cria uma Flatlist
            # result = list(itertools.chain(*result))
            return super(ud_reserva, self).read(cr, user, result)

        # Caso não ache nada, retorne a lista vazia
        return super(ud_reserva, self).read(cr, user, solicitante_reserva_ids)

    def data_reserva(self, cr, uid, c):
        return fields.datetime.context_timestamp(cr, uid, datetime.now(), c).strftime('%d/%m/%Y')

    def data_teste(self, cr, uid, c):
        return fields.datetime.context_timestamp(cr, uid, datetime.now(), c)

    def obter_datetime(self, cr, uid, d, context):
        parte_data = d[:10].split("-")
        parte_hora = d[11:].split(":")

        data_entrada = datetime(int(parte_data[0]), int(parte_data[1]), int(parte_data[2]),
                                int(parte_hora[0]), int(parte_hora[1]), int(parte_hora[2]))

        data_entrada = data_entrada + relativedelta(hours=-3)
        return data_entrada

    def new_datetime_diario(self, cr, uid, data_fixa, n, context):
        data = self.obter_datetime(cr, uid, data_fixa, context)
        data = data + relativedelta(days=+n, hours=+3)
        nova_data = str(data)
        return nova_data

    def new_datetime_semanal(self, cr, uid, data_fixa, n, context):
        semana = 7
        dias = n * semana
        data = self.obter_datetime(cr, uid, data_fixa, context)
        data = data + relativedelta(days=+dias, hours=+3)
        nova_data = str(data)
        return nova_data

    def new_datetime_mensal(self, cr, uid, data_fixa, n, context):
        data = self.obter_datetime(cr, uid, data_fixa, context)
        data = data + relativedelta(months=+n, hours=+3)
        nova_data = str(data)
        return nova_data

    def replicar(self, cr, uid, ids, context=None):
        # Cria o nome baseando-se no nome da reserva e data em que foi criada
        obj = self.browse(cr, uid, ids)[0]
        name = obj.name + " : " + obj.hora_entrada
        # Cria e recupera o id
        grupo_obj = self.pool.get('ud.reserva.grupo')
        grupo = self.pool.get('ud.reserva.grupo').create(cr, uid, {u'name': name, u'reserva_ids': [(4, obj.id)]})

        def replicar_diario(n, h_entrada, h_saida):
            for i in range(1, n + 1):
                novos_valores = copy.copy(values)
                entrada = self.new_datetime_diario(cr, uid, h_entrada, i, context)
                saida = self.new_datetime_diario(cr, uid, h_saida, i, context)
                novos_valores["hora_entrada"] = entrada
                novos_valores["hora_saida"] = saida
                grupo_reserva = [(0,0, novos_valores)]
                # Cria e adiciona a rserva ao grupo
                grupo_obj.write(cr, uid, [grupo], {'reserva_ids': grupo_reserva})
                #result = self.create(cr, uid, novos_valores, context)

        def replicar_semanal(n, h_entrada, h_saida):
            for i in range(1, n + 1):
                novos_valores = copy.copy(values)
                entrada = self.new_datetime_semanal(cr, uid, h_entrada, i, context)
                saida = self.new_datetime_semanal(cr, uid, h_saida, i, context)
                novos_valores["hora_entrada"] = entrada
                novos_valores["hora_saida"] = saida
                grupo_reserva = [(0,0, novos_valores)]
                # Cria e adiciona a rserva ao grupo
                grupo_obj.write(cr, uid, [grupo], {'reserva_ids': grupo_reserva})
                #result = self.create(cr, uid, novos_valores, context)
               # print result

        def replicar_mes(n, h_entrada, h_saida):
            for i in range(1, n + 1):
                novos_valores = copy.copy(values)
                entrada = self.new_datetime_mensal(cr, uid, h_entrada, i, context)
                saida = self.new_datetime_mensal(cr, uid, h_saida, i, context)
                if saida <= values["periodo_final"]:
                    novos_valores["hora_entrada"] = entrada
                    novos_valores["hora_saida"] = saida
                    grupo_reserva = [(0,0, novos_valores)]
                    # Cria e adiciona a rserva ao grupo
                    grupo_obj.write(cr, uid, [grupo], {'reserva_ids': grupo_reserva})
                    #result = self.create(cr, uid, novos_valores, context)
                    #print result


        values = {
            "name": self.pool.get('ud.reserva').browse(cr, uid, ids)[0].name,
            "state": "aprovada",
            "solicitante_id": self.pool.get('ud.reserva').browse(cr, uid, ids)[0].solicitante_id.id,
            "data_solicitacao_reserva": self.pool.get('ud.reserva').browse(cr, uid, ids)[0].data_solicitacao_reserva,
            "descricao_evento": self.pool.get('ud.reserva').browse(cr, uid, ids)[0].descricao_evento,
            "motivo": self.pool.get('ud.reserva').browse(cr, uid, ids)[0].motivo,
            "data_cancelamento": self.pool.get('ud.reserva').browse(cr, uid, ids)[0].data_cancelamento,
            "espaco_id": self.pool.get('ud.reserva').browse(cr, uid, ids)[0].espaco_id.id,
            "hora_entrada": self.pool.get('ud.reserva').browse(cr, uid, ids)[0].hora_entrada,
            "hora_saida": self.pool.get('ud.reserva').browse(cr, uid, ids)[0].hora_saida,
            "periodo_final": self.pool.get('ud.reserva').browse(cr, uid, ids)[0].periodo_final,
            "frequencia": self.pool.get('ud.reserva').browse(cr, uid, ids)[0].frequencia,
        }

        h_entrada = values["hora_entrada"]
        h_saida = values["hora_saida"]
        p_final = values["periodo_final"]

        dias = self.total_dias(cr, uid, p_final, h_saida, context)
        if dias != 0:
            if values["frequencia"] == "0":
                n = int(dias) / 1
                replicar_diario(n, h_entrada, h_saida)
            elif values["frequencia"] == "1":
                n = int(dias) / 7
                replicar_semanal(n, h_entrada, h_saida)
            elif values["frequencia"] == "2":
                n = int(dias) / 30
                replicar_mes(n, h_entrada, h_saida)

    def aprovar(self, cr, uid, ids, context=None):
        slc = self.browse(cr, uid, ids, context)[0]
        if slc.state == "enviada":
            self.replicar(cr, uid, ids, context)
            return self.write(cr, uid, ids, {'state': 'aprovada'})

    def cancelar(self, cr, uid, ids, context=None):
        '''
        Grava o motivo e o status cancelado na solicitação atual.
        Acionado por um botão
        '''
        slc = self.browse(cr, uid, ids, context)[0]
        if slc.state == "enviada" or slc.state == "aprovada" and slc.motivo != "":
            return self.write(cr, uid, ids, {"motivo": slc.motivo, 'state': 'cancelada'})

    def envia_solicitacao(self, cr, uid, ids, c=None):
        status = self.browse(cr, uid, ids)[0].state
        if status == "nova":
            self.write(cr, uid, ids, {"state": "enviada"})
            return True
        return True

    def total_dias(self, cr, uid, data_final, data_inicial, context):
        #print "hora de saida"
        va = self.obter_datetime(cr, uid, data_inicial, context)
        try:
            #print "hora de fim de frequencia"
            vb = self.obter_datetime(cr, uid, data_final, context)
        except:
            #print "hora de saida"
            vb = self.obter_datetime(cr, uid, data_inicial, context)
        return (vb - va).days

    def periodo_final(self, cr, uid, ids, h_saida, freq=False, context=None):
        res = {"value": {}}
        if freq == "0":
            res["value"]["periodo_final"] = self.new_datetime_diario(cr, uid, h_saida, 1, context)
        elif freq == "1":
            res["value"]["periodo_final"] = self.new_datetime_semanal(cr, uid, h_saida, 1, context)
        elif freq == "2":
            res["value"]["periodo_final"] = self.new_datetime_mensal(cr, uid, h_saida, 1, context)
        return res

    def create(self, cr, uid, values, context=None):
        h_saida = values["hora_saida"]
        p_final = values["periodo_final"]
        dias = self.total_dias(cr, uid, p_final, h_saida, context)

        if int(dias) >= 0:
            return super(osv.osv, self).create(cr, uid, values, context)
        raise except_orm("Data Inválida.".decode("UTF-8"),
                         "O fim da frequencia nao pode ser inferior a data de entrada/saida".decode("UTF-8"))

    def _checar_data(self, cr, uid, ids, context=None):
        obj_data_reserva = self.pool.get('ud.reserva').browse(cr, uid, ids)

        for obj in obj_data_reserva:
            # depois colocar os dois 'if' em uma unica linha
            if datetime.strptime(obj.hora_entrada, "%Y-%m-%d %H:%M:%S") < datetime.now():
                return False
            if datetime.strptime(obj.hora_saida, "%Y-%m-%d %H:%M:%S") < datetime.now():
                return False
        return True

    def _checar_reserva(self, cr, uid, ids, context=None):
        # noinspection SqlNoDataSourceInspection
        cr.execute('''SELECT
                      hora_entrada, hora_saida, espaco_id, state, teste
                      FROM ud_reserva
                      ;''')
        reserva_lista = cr.fetchall()
        obj_data_reserva2 = self.pool.get('ud.reserva').browse(cr, uid, ids)[0]
        entrada_usuario = datetime.strptime(obj_data_reserva2.hora_entrada, "%Y-%m-%d %H:%M:%S")
        saida_usuario = datetime.strptime(obj_data_reserva2.hora_saida, "%Y-%m-%d %H:%M:%S")
        espaco_usuario = int(obj_data_reserva2.espaco_id)
        teste_usuario = obj_data_reserva2.teste

        for reserva in reserva_lista:
            entrada_banco = datetime.strptime(reserva[0], "%Y-%m-%d %H:%M:%S")
            saida_banco = datetime.strptime(reserva[1], "%Y-%m-%d %H:%M:%S")
            espaco_banco = int(reserva[2])
            estado_banco = reserva[3]
            teste_banco = reserva[4]

            #print("entrada_usuario", entrada_usuario, "entrada_banco", entrada_banco)

            if (espaco_usuario == espaco_banco and teste_usuario != teste_banco):
                if (entrada_usuario == entrada_banco or saida_usuario == saida_banco):
                    return False

                elif (entrada_usuario < entrada_banco and saida_usuario > entrada_banco):
                    return False

                elif (entrada_usuario > entrada_banco and entrada_usuario < saida_banco):
                    return False

        return True

    def _checar_dia_reserva(self, cr, uid, ids, context=None):
        obj_data_reserva2 = self.pool.get('ud.reserva').browse(cr, uid, ids)
        for obj in obj_data_reserva2:
            #print "checando o dia da reserva"
            data_e = self.obter_datetime(cr, uid, obj.hora_entrada, context)
            data_s = self.obter_datetime(cr, uid, obj.hora_saida, context)
            if data_e.date() != data_s.date():
                return False
        return True

    def _checar_horario(self, cr, uid, ids, context=None):
        obj_data_reserva = self.pool.get('ud.reserva').browse(cr, uid, ids)
        for obj in obj_data_reserva:
            if datetime.strptime(obj.hora_entrada, "%Y-%m-%d %H:%M:%S") >= datetime.strptime(obj.hora_saida,
                                                                                             "%Y-%m-%d %H:%M:%S"):
                return False
        return True

    _constraints = [(_checar_data, "Não é possível reservar em data ultrapassada!", ['Entrada', 'Saida']),
                    (_checar_dia_reserva, "Entrada e Saída devem ser na mesma data!", ['Entrada', 'Saida']),
                    (_checar_reserva, "Horário indisponível. Há uma reserva neste mesmo horário e espaço!",
                     ['Reserva e Espaço'.decode("UTF-8")]),
                    (_checar_horario, "Horário de Saída não pode ser menor ou igual ao Horário de Entrada!",
                     ['Entrada', 'Saída'.decode("UTF-8")]),
                    (envia_solicitacao, "Solicitação Enviada", ["Enviar"]), ]


ud_reserva()


class ud_reserva_responsavel(osv.Model):
    _name = 'ud.reserva.responsavel'

    _columns = {
        'name': fields.related('responsavel_id', 'resource_id', 'name', string="Nome", type='char'),
        'responsavel_id': fields.many2one('ud.employee', u"Responsável", required=True),
        'campus_id': fields.many2one('ud.campus', u'Campus', required=True),
        'polo_id': fields.many2one('ud.polo', u'Polo', required=True),
        'espaco_id': fields.many2one('ud.espaco', u'Espaço', required=True)
    }


class ud_reserva_grupo(osv.Model):
    _name = 'ud.reserva.grupo'

    _columns = {
        'name': fields.char('Nome', required=True),
        'reserva_ids': fields.one2many('ud.reserva', 'grupo_id', u"Reservas", required=True, ondelete='cascade')
    }
