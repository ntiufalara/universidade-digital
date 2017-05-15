# coding: utf-8
from __future__ import unicode_literals
from openerp.osv import fields, osv
from datetime import datetime
from openerp.addons.ud_almoxarifado import utils
from openerp.osv.orm import except_orm


class ud_almoxarifado_produto(osv.osv):
    _name = 'ud.almoxarifado.produto'
    _description = u'Cadastrar produto'
    _order = 'produto asc'
    _rec_name = 'produto'
    _columns = {
        'produto': fields.char(u'Produto', size=64, required=True),
        'observacao': fields.text(u'Observação'),
        'categoria_id': fields.many2one('ud.almoxarifado.categoria', u'Categoria', required=True, ondelete='restrict'),
        'fabricante_id': fields.many2one('ud.almoxarifado.fabricante', u'Fabricante', required=True),
    }

    _sql_constraints = [
        ('produto_unico', 'unique (produto,categoria_id)', u'Produto já cadastrado nessa categoria!'),
    ]

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        vals['produto'] = vals.get("produto").upper()
        res_id = super(ud_almoxarifado_produto, self).create(cr, uid, vals, context)
        self.pool.get('ud.almoxarifado.estoque').create(cr, uid, {'produto_id': res_id, 'estoque_min': 1})
        return res_id


class ud_almoxarifado_produto_qtd(osv.osv):
    _name = 'ud.almoxarifado.produto.qtd'
    _description = 'Associar produto a quantidade'

    def _valida_quantidade(self, cr, uid, ids, context=None):  # método usado para fazer a validação
        estoque_model = self.pool.get("ud.almoxarifado.estoque")
        for produto_qtd in self.browse(cr, uid, ids, context=context):
            if produto_qtd.quantidade < 1:
                return False
            estoque = estoque_model.search(cr, uid, [("produto_id", "=", produto_qtd.produto_id.id),
                                                     ("quantidade", "<=", produto_qtd.quantidade)], context=context)
            if (not estoque):
                return False
        return True

    def _estoque(self, cr, uid, ids, campo, args, context=None):
        res = {}.fromkeys(ids, 0)
        estoque_model = self.pool.get('ud.almoxarifado.estoque')
        for produto_qtd in self.read(cr, uid, ids, ['produto_id', 'id'], load='_classic_write', context=context):
            quantidade = estoque_model._calcula_quantidade(cr, uid, estoque_model.search(cr, uid, [
                ('produto_id', '=', produto_qtd.get('produto_id'))], context=context), None, None, context=context),
            res[produto_qtd.get('id')] = quantidade[0].values()[0]
        return res

    _columns = {

        'produto_id': fields.many2one('ud.almoxarifado.produto', u'Produto',
                                      domain="[('categoria_id','=', categoria_id)]", required=True, ondelete='cascade'),
        'quantidade': fields.integer(u'Quantidade', required=True),
        'categoria_id': fields.many2one('ud.almoxarifado.categoria', 'categoria', ondelete='restrict'),
        'estoque': fields.function(_estoque, type=str('integer'), string=u'Estoque', method=True),
        'solicitacao_id': fields.many2one('ud.almoxarifado.solicitacao', 'solicitacao', invisible=True),
    }

    _rec_name = 'produto_id'

    _sql_constraints = [
        ('produto_solicitacao_uniq', 'unique (solicitacao_id,produto_id)',
         u'Não pode solicitar o memo produto na mesma solicitação'),
    ]

    _constraints = [
        (_valida_quantidade, u'A quantidade não pode ser menor do que 1 ou ultrapassar o estoque', [u'\nQuantidade']),
    ]  # validar os dados

    def onchange_produto(self, cr, uid, ids, produto, context=None):
        estoque_model = self.pool.get('ud.almoxarifado.estoque')
        quantidade = estoque_model._calcula_quantidade(cr, uid,
                                                       estoque_model.search(cr, uid, [('produto_id', '=', produto)],
                                                                            context=context), None, None,
                                                       context=context),
        return {"value": {"estoque": quantidade[0].values()[0]}}

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        res_id = super(ud_almoxarifado_produto_qtd, self).create(cr, uid, vals, context)
        estoque_model = self.pool.get('ud.almoxarifado.estoque')
        estoque = estoque_model.search(cr, uid, [('produto_id', '=', vals['produto_id'])], context=context)
        estoque_model.write(cr, uid, estoque[0],
                            {'saida_ids': [(0, 0, {'data_saida': datetime.utcnow().strftime('%Y-%m-%d'),
                                                   'quantidade': vals['quantidade']})]}, context=context)
        return res_id

    def unlink(self, cr, uid, ids, context=None):
        # solicitacao_ids = self.read(cr, uid, ids, ["solicitacao_id"], context=context, load="_classic_write")
        res = super(ud_almoxarifado_produto_qtd, self).unlink(cr, uid, ids, context=context)
        # solicitacao_ids = [solicitacao.get("solicitacao_id") for solicitacao in solicitacao_ids]
        # self.pool.get("ud.almoxarifado.solicitacao").unlink(cr, uid, solicitacao_ids, context=context)
        return res

    def restaurar_produtos(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        estoque_model = self.pool.get('ud.almoxarifado.estoque')
        for produto in self.browse(cr, uid, ids, context=context):
            estoque = estoque_model.search(cr, uid, [('produto_id', '=', produto.produto_id.id)])
            estoque_model.write(cr, uid, estoque[0],
                                {'entrada_ids': [(0, 0, {'data_entrada': datetime.utcnow().strftime('%Y-%m-%d'),
                                                         'quantidade': produto.quantidade,
                                                         'tipo': 'estorno'})]})


class ud_almoxarifado_solicitacao(osv.osv):
    _name = 'ud.almoxarifado.solicitacao'
    _description = u'Solicitar Produtos'

    _get_name = lambda self, cr, uid, ids, field, args, context: self.get_name(cr, uid, ids, field, args, context)

    def _get_solicitante(self, cr, uid, ids, field, arg, context=None):
        if isinstance(ids, (
                int, long)):  # verifica se o id é um inteiro ou longo, se for ele colocará o inteiro em uma lista
            ids = [ids]
        domain = [('user_id', '=', uid)]
        pessoa_id = self.pool.get("ud.employee").search(cr, uid, domain)
        if not pessoa_id:
            raise osv.except_osv(u"Vinculo Pessoa-Usuário",
                                 u"Vínculo com pessoa e usuário inexistente")
        return {}.fromkeys(ids, pessoa_id[0])

    _STATE = [("aguardando", "Aguardando Retirada"),
              ("entregue", "Entregue"),
              ("cancelada", "Cancelada")]

    _columns = {
        'name': fields.function(_get_name, string=u'Nome', type=str('char')),
        'produtos_ids': fields.one2many('ud.almoxarifado.produto.qtd', 'solicitacao_id', string=u'Produtos',
                                        required=True),
        "solicitante_id": fields.many2one('ud.employee', 'Solicitante', ondelete='restrict'),
        'data_hora': fields.datetime(u'Data/hora'),
        'setor_id': fields.many2one('ud.setor', 'Setor', required=True),
        "state": fields.selection(_STATE, u"Status"),
    }

    _defaults = {
        'data_hora': fields.datetime.now(),
        'solicitante_id': lambda self, cr, uid, c: self.obter_solicitante(cr, uid, c),
        'setor_id': lambda self, cr, uid, c: self.obter_setor(cr, uid, c),
    }

    _rec_name = 'name'

    def obter_solicitante(self, cr, uid, c):
        '''
        Obtém o id da pessoa associada ao usuário logado e devolve para o campo relacional "solicitante_id"
        '''
        pessoa = self.pool.get("ud.employee").browse(
                cr, uid,
                self.pool.get("ud.employee").search(cr, uid, [('user_id', '=', uid)], 0)
        )
        if pessoa:
            return pessoa[0].id
        else:
            raise except_orm("Pessoa não localizada".decode("UTF-8"),
                             "Não há pessoa associada a esse usuário".decode("UTF-8"))

    def obter_setor(self, cr, uid, c):
        '''
        Obtém o id da pessoa associada ao usuário logado e devolve para o campo relacional "solicitante_id"
        '''
        pessoa = self.pool.get("ud.employee").browse(
                cr, uid,
                self.pool.get("ud.employee").search(cr, uid, [('user_id', '=', uid)], 0)
        )
        if pessoa[0].papel_ids:
            for papel in pessoa[0].papel_ids:
                if papel.ud_setores:
                    return papel.ud_setores.id
        else:
            raise except_orm("Perfil não localizado".decode("UTF-8"),
                             "É preciso ter papel em algum setor".decode("UTF-8"))

    def get_name(self, cr, uid, ids, field, args, context):
        dados = self.browse(cr, uid, ids, context)[0]
        data = datetime.now()
        if dados.data_hora:
            data = datetime.strptime(dados.data_hora, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        return {
            dados.id: 'Solicitante {}; Setor:{}; Data: {}'.format(dados.solicitante_id.name, dados.setor_id.name, data)}

    def create(self, cr, uid, vals, context=None):
        vals['state'] = "aguardando"
        res_id = super(ud_almoxarifado_solicitacao, self).create(cr, 1, vals, context)

        return res_id

    def write(self, cr, user, ids, vals, context=None):
        """
        (0, 0,  { values })    link to a new record that needs to be created with the given values dictionary
        (1, ID, { values })    update the linked record with id = ID (write *values* on it)
        (2, ID)                remove and delete the linked record with id = ID (calls unlink on ID, that will delete the object completely, and the link to it as well)
        (3, ID)                cut the link to the linked record with id = ID (delete the relationship between the two objects but does not delete the target object itself)
        (4, ID)                link to existing record with id = ID (adds a relationship)
        (5)                    unlink all (like using (3,ID) for all linked records)
        (6, 0, [IDs])          replace the list of linked IDs (like using (5) then (4,ID) for each ID in the list of IDs)
        :param cr:
        :param user:
        :param ids:
        :param vals:
        :param context:
        :return:
        """
        if vals.get('produtos_ids'):
            for i in vals.get('produtos_ids'):
                if i[0] in [2, 3]:
                    self.pool.get('ud.almoxarifado.produto.qtd').restaurar_produtos(cr, user, i[1])
        return super(ud_almoxarifado_solicitacao, self).write(cr, user, ids, vals, context)

    def botao_cancelar(self, cr, uid, ids, context=None):
        ids_produtos = self.read(cr, uid, ids, ['produtos_ids'], load='_classic_write')
        for ids_produto in ids_produtos:
            self.pool.get('ud.almoxarifado.produto.qtd').restaurar_produtos(cr, uid, ids_produto.get("produtos_ids"))
        return self.write(cr, uid, ids, {"state": "cancelada"}, context=context)

    def botao_entregue(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return self.write(cr, uid, ids, {"state": "entregue"}, context=context)


class ud_almoxarifado_fornecedor(osv.osv):
    _name = 'ud.almoxarifado.fornecedor'
    _description = u'Cadastrar Fornecedor'
    _order = 'name asc'

    _ESTADOS = [('ac', u'AC'), ('al', u'AL'), ('ap', u'AP'), ('am', u'AM'), ('ba', u'BA'), ('ce', u'CE'), ('df', u'DF'),
                ('es', u'ES'),
                ('go', u'GO'), ('ma', u'MA'), ('mg', u'MG'), ('ms', u'MS'), ('mt', u'MT'), ('pa', u'PA'), ('pe', u'PE'),
                ('pi', u'PI'),
                ('pr', u'PR'), ('rj', u'RJ'), ('rn', u'RN'), ('ro', u'RO'), ('rr', u'RR'), ('rs', u'RS'), ('sc', u'SC'),
                ('se', u'SE'),
                ('sp', u'SP'), ('to', u'TO')]

    _columns = {
        'name': fields.char(u'Fornecedor', size=64, required=True, readonly=False),
        'cpf_cnpj': fields.char(u'CPF/CNPJ'),
        'fixo': fields.char(u'Telefone'),
        'celular': fields.char(u'Celular'),
        'email': fields.char(u'E-mail'),
        'estado': fields.selection(_ESTADOS, u'Estado'),
        'cidade': fields.char(u'Cidade'),
        'bairro': fields.char(u'Bairro'),
        'numero': fields.char(u'Nº'),
        'cep': fields.char(u'CEP'),
    }

    _SQL_CONSTRAINTS = [('unique_name', 'unique(name)', u"Fornecedor já cadastrado!")]

    def valida_cpf_cnpj(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        dados = self.browse(cr, uid, ids, context)[0]
        valido = utils.validar_cpf_cnpj(dados.cpf_cnpj)
        if valido:
            return True

    _constraints = [
        (valida_cpf_cnpj,
         u"Inválido, verifique os dados e tente novamente",
         ["\nCPF/CNPJ"]),
    ]

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        vals['name'] = vals.get("name").upper()
        res_id = super(ud_almoxarifado_fornecedor, self).create(cr, uid, vals, context)
        return res_id


class ud_almoxarifado_categoria(osv.osv):
    _name = 'ud.almoxarifado.categoria'
    _description = u'Cadastrar Categoria'
    _order = 'name asc'

    _columns = {
        'name': fields.char(u'Categoria', size=64, required=True, readonly=False),
    }

    _SQL_CONSTRAINTS = [('unique_name', 'unique(name)', u"Categoria já cadastrada!")]

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        vals['name'] = vals.get("name").upper()
        res_id = super(ud_almoxarifado_categoria, self).create(cr, uid, vals, context)
        return res_id


class ud_almoxarifado_estoque(osv.osv):
    _name = 'ud.almoxarifado.estoque'
    _description = u'Controlar estoque'

    #     _order = 'name asc'

    def _valida_quantidade(self, cr, uid, ids, context=None):  # método usado para fazer a validação
        if isinstance(ids, (
                int, long)):  # verifica se o id é um inteiro ou longo, se for ele colocará o inteiro em uma lista
            ids = [ids]
        produtos = self._calcula_quantidade(cr, uid, ids, None, None, context=context)
        for produto in produtos.values():
            if (produto < 0):
                return False
        return True

    def _valida_estoque_min(self, cr, uid, ids):  # método usado para fazer a validação
        if isinstance(ids, (
                int, long)):  # verifica se o id é um inteiro ou longo, se for ele colocará o inteiro em uma lista
            ids = [ids]
        produtos = self.browse(cr, uid, ids)
        for produto in produtos:
            if (produto.estoque_min < 1):
                return False
        return True

    def _calcula_quantidade(self, cr, uid, ids, field, args, context=None):
        res = {}.fromkeys(ids, 0)
        for estoque in self.browse(cr, uid, ids, context=context):
            res[estoque.id] = sum([entrada.quantidade for entrada in estoque.entrada_ids])
            res[estoque.id] -= sum([saida.quantidade for saida in estoque.saida_ids])
        return res

    def _update_quantidade(self, cr, uid, ids, context=None):

        return ids

    _columns = {
        'produto_id': fields.many2one('ud.almoxarifado.produto', string=u'Produto', required=True, readonly=True,
                                      ondelete="restrict"),
        'observacao': fields.related('produto_id', 'observacao', string=u'Observação', type='text', readonly=True),
        'categoria_id': fields.related('produto_id', 'categoria_id', type='many2one',
                                       relation='ud.almoxarifado.categoria', string=u'Categoria', readonly=True),
        'estoque_min': fields.integer(u'Estoque Mínimo', required=True),
        'quantidade': fields.function(_calcula_quantidade, type=str("integer"), method=True, string=u'Quantidade',
                                      store=False),
        # atualiza o modelo "ud.almoxarifado.estoque' sempre que os campos dentro da lista forem atualizados ele retorna a lista de ids que precisam serem atualizados.
        'fornecedor_id': fields.many2one('ud.almoxarifado.fornecedor', u'Fornecedor', ondelete='restrict'),
        'entrada_ids': fields.one2many('ud.almoxarifado.entrada', 'estoque_id', string=u"Entrada"),
        'saida_ids': fields.one2many('ud.almoxarifado.saida', 'estoque_id', string=u"Saida")
    }

    _rec_name = 'produto_id'

    _sql_constraints = [
        ('produto_unico', 'unique (produto_id)', u'Produto já cadastrado!'),
    ]

    _constraints = [
        (
            _valida_quantidade,
            u'A quantidade está incorreta, precisa ser maior que 0 e menor que a quantidade em Estoque',
            ['\nQuantidade']),
        (_valida_estoque_min, u'A quantidade deve ser maior que 0', [u'\nEstoque Mínimo']),
    ]

    def unlink(self, cr, uid, ids, context=None):
        produto_ids = self.read(cr, uid, ids, ["produto_id"], context=context, load="_classic_write")
        res = super(ud_almoxarifado_estoque, self).unlink(cr, uid, ids, context=context)
        produto_ids = [produto.get("produto_id") for produto in produto_ids]
        self.pool.get("ud.almoxarifado.produto").unlink(cr, uid, produto_ids, context=context)
        return res

    def adicionar(self, cr, uid, ids, qtd):
        if isinstance(ids, (int, long)):
            ids = [ids]
        produtos = self.browse(cr, uid, ids)
        for produto in produtos:
            self.write(cr, uid, produto.id, {'quantidade': produto.quantidade + qtd})

    def remover(self, cr, uid, ids, qtd):
        if isinstance(ids, (int, long)):
            ids = [ids]
        produtos = self.browse(cr, uid, ids)
        for produto in produtos:
            self.write(cr, uid, produto.id, {'quantidade': produto.quantidade - qtd})


class ud_almoxarifado_entrada(osv.Model):
    _name = 'ud.almoxarifado.entrada'

    _columns = {
        'data_entrada': fields.date(u'Data de entrada', required=True),
        'quantidade': fields.integer(u'Quantidade', required=True),
        'tipo': fields.selection([("fornecedor", u"Fornecedor"), ("estorno", u"Estorno"), ("devolucao", u"Devolução")],
                                 u"Tipo"),
        'estoque_id': fields.many2one('ud.almoxarifado.estoque', u'Estoque', invisible=True, ondelete='cascade'),
        'fornecedor_id': fields.many2one('ud.almoxarifado.fornecedor', u'Fornecedor', readonly=True,
                                         ondelete='restrict')
    }

    _defaults = {
        "tipo": "fornecedor"
    }


class ud_almoxarifado_saida(osv.Model):
    _name = 'ud.almoxarifado.saida'

    _columns = {
        'data_saida': fields.date(u'Data de saída', required=True),
        'quantidade': fields.integer(u'Quantidade', required=True),
        'observacao': fields.text(u'Observação'),
        'estoque_id': fields.many2one('ud.almoxarifado.estoque', u'Estoque', invisible=True, ondelete='cascade'),

    }


class ud_almoxarifado_fabricante(osv.Model):
    _name = 'ud.almoxarifado.fabricante'

    _columns = {
        'name': fields.char(u'Nome', required=True),
    }
