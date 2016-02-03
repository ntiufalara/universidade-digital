# coding: utf-8
'''
Created on 12/05/2015

@author: Cloves Oliveira
'''

from openerp import SUPERUSER_ID
from openerp.modules.registry import RegistryManager
from openerp.osv import osv, fields
from re import compile
from os.path import join, dirname, exists

try:
    falta_dependencias = None
    from pdf_util import Pdf, TemplateError
except ImportError as e:
    falta_dependencias = e.message

class UnknownDocType(Exception):
    pass

class ud_documento_tipo_campo(osv.osv):
    _name = "ud.documento.tipo.campo"
    _description = u"Campo a ser utilizado para um determinado tipo de documento (UD)"
    
    def _valida_nome(self, cr, uid, ids, **kwargs):
        re = compile("^[a-z_][a-zA-Z0-9_]+$")
        for campo in self.browse(cr, uid, ids, **kwargs):
            res = re.match(campo.name)
            if not res:
                return False
        return True
    
    _columns = {
        "name": fields.char(u"Campo", required=True),
        "descricao": fields.text(u"Descrição"),
        "tipo_doc_id": fields.many2one("ud.documento.tipo", u"Tipo de documento", invisible=True),
    }
    
    _constraints = [
        (_valida_nome, u"É permitido utilizar somente letras não acentuadas, underlines e números. Também não é permitido iniciar com números. \
        Cuidado com espaços antes ou depois do nome!", [u"\nCampo"])
    ]
    
    _sql_constraints = [
        ("campo_tipo_doc_unique", "unique(name,tipo_doc_id)", u"Não é permitido campos repetidos no mesmo tipo de documento!")
    ]
    
    def create(self, cr, uid, vals, context={}):
        vals["name"] = vals.get("name").lower()
        return super(ud_documento_tipo_campo, self).create(cr, uid, vals, context)
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.has_key(("name")):
            vals["name"] = vals.get("name").lower()
        return super(ud_documento_tipo_campo, self).write(cr, uid, ids, vals, context=context)

ud_documento_tipo_campo()

class ud_documento_tipo(osv.osv):
    _name = "ud.documento.tipo"
    _description = u"Tipo de documento (UD)"
    _order = "name asc"
    
    def _campos(self, cr, uid, ids, campo, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}.fromkeys(ids, False)
        texto = u"Simples substituição:\n{tags}\n"\
                u"Mako:\n{mako}"
        for tipo in self.browse(cr, uid, ids, context=context):
            if tipo.modulo_externo:
                if tipo.campos_ids:
                    mako = tipo.campos_ids[0].name
                    tags = u"{{%s}}" % tipo.campos_ids[0].name.upper()
                    for campo in tipo.campos_ids[1:]:
                        mako += u", " + campo.name
                        tags += (u", {{%s}}" % campo.name.upper())
                    res[tipo.id] = texto.format(tags=tags, mako=mako)
            else:
                tags = u""
                mako = u""
                if tipo.numero:
                    tags += u"{{NUMERO}}, "
                    mako += u"numero, "
                if tipo.destinatario:
                    tags += u"{{DESTINATARIO}}, "
                    mako += u"destinatario, "
                if tipo.data:
                    tags += u"{{DATA}}, "
                    mako += u"data, "
                if tipo.cabecalho:
                    tags += u"{{CABECALHO}}, "
                    mako += u"cabecalho, "
                if tipo.assunto:
                    tags += u"{{ASSUNTO}}, "
                    mako += u"assunto, "
                if tipo.conteudo:
                    tags += u"{{CONTEUDO}}, "
                    mako += u"conteudo, "
                if tipo.rodape:
                    tags += u"{{RODAPE}}, "
                    mako += u"rodape, "
                res[tipo.id] = texto.format(tags=tags[:-2], mako=mako[:-2])
        return res
    
    _ARQS_HTML = [("circular.html", u"Circular"),
                  ("ci.html", u"Comunicação Interna"),
                  ("memorando.html", u"Memorando"),
                  ("oficio.html", u"Ofício"),
                  ("portaria.html", u"Portaria")]
    
    _ARQS_HTML_CONFIG = {
        "circular.html": {"nome": "Circular", "cabecalho": True, "numero": True, "data": True, "destinatario": True, "assunto": True, "conteudo": True, "rodape": True, "anexos": True},
        "ci.html": {"nome": "Comunicação Interna", "cabecalho": True, "numero": True, "data": True, "destinatario": True, "assunto": True, "conteudo": True, "rodape": True, "anexos": True},
        "memorando.html": {"nome": "Memorando", "cabecalho": True, "numero": True, "data": True, "destinatario": True, "assunto": True, "conteudo": True, "rodape": True, "anexos": True},
        "oficio.html": {"nome": "Ofício", "cabecalho": True, "numero": True, "data": True, "destinatario": True, "assunto": True, "conteudo": True, "rodape": True, "anexos": True},
        "portaria.html": {"nome": "Portaria", "cabecalho": True, "numero": True, "data": True, "conteudo": True, "rodape": True, "anexos": True},
    }
    
    _columns = {
        "name": fields.char(u"Nome", required=True, help=u"Nome do tipo do documento"),
        # Campos
        "numero": fields.boolean(u"Número", readonly=True),
        "destinatario": fields.boolean(u"Destinatário(s)"),
        "data": fields.boolean(u"Data", readonly=True),
        "cabecalho": fields.boolean(u"Cabeçalho"),
        "assunto": fields.boolean(u"Assunto"),
        "conteudo": fields.boolean(u"Conteúdo"),
        "rodape": fields.boolean(u"Rodape"),
        "anexos": fields.boolean(u"Anexos", help=u"Permite anexar vários PDFs"),
        # Configurações
        "template_padrao": fields.selection(_ARQS_HTML, u"Template padrão"),
        "template": fields.text(u"Template", required=True, help=u"Modelo em HTML5 do tipo do documento"),
        "modulo_externo": fields.boolean(u"Módulo externo", help=u"Define se esse tipo de documento será utilizado pelo módulo de documentos ou não."),
#         "email_server": fields.many2one("ir.mail_server", u"Servidor SMTP", ondelete="restrict", help=u"Servidor SMTP para envio de e-mails"),
        "modelo_id": fields.many2one("ir.model", u"Modelo", domain=[("model", "not in", ["ud.documento",
                                                                                         "ud.documento.anexo",
                                                                                         "ud.documento.tipo", 
                                                                                         "ud.documento.tipo.campo",
                                                                                         "ud.documento.enviado",
                                                                                         "ud.documento.recebido",])]),
        "campos_ids": fields.one2many("ud.documento.tipo.campo", "tipo_doc_id", u"Campos", required=True),
        "ajuda_campos": fields.function(_campos, type="text", method=True, string=u"Tags e Variáveis", store=False),
    }
    
    _defaults = {
        "numero": True,
        "data": True,
        "cabecalho": True,
        "conteudo": True,
        "rodape": True,
        "ajuda_campos": u"Simples substituição:\n{{NUMERO}}, {{DATA}}, {{CABECALHO}}, {{CONTEUDO}}, {{RODAPE}}\n"\
                        u"Mako:\nnumero, data, cabecalho, conteudo, rodape"
    }
    
    _sql_constraints = [
        ("name_uniq", "unique (name)", u"Já existe outro documento com mesmo nome!"),
    ]
    
    def create(self, cr, uid, vals, context={}):
        vals["name"] = vals.get("name").upper()
        vals["template_padrao"] = False
        return super(ud_documento_tipo, self).create(cr, uid, vals, context)
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.has_key(("name")):
            vals["name"] = vals.get("name").upper()
        vals["template_padrao"] = False
        return super(ud_documento_tipo, self).write(cr, uid, ids, vals, context=context)
    
    def botao_adicionar_campos(self, cr, uid, ids, context=None):
        tipo_doc = self.browse(cr, uid, ids[0], context=context)
        add = lambda nome, descricao: (0, 0, {"name": nome, "descricao": descricao})
        res = []
        if tipo_doc.modelo_id:
            for campo in tipo_doc.modelo_id.field_id:
                descricao = u"Tipo: {tipo}{relacao}{obrigatorio}{readonly}".format(tipo=campo.ttype,
                                                   relacao= u"\nRelação de objetos: {}".format(campo.relation) if campo.relation else u"",
                                                   obrigatorio=u"\nObrigatório: sim" if campo.required else u"",
                                                   readonly=u"\nSomente leitura: sim" if campo.readonly else u"")
                res.append(add(campo.name, descricao))
            return self.write(cr, uid, ids, {"campos_ids": res}, context=context)
        return False
    
    def botao_remover_campos(self, cr, uid, ids, context=None):
        tipo_doc = self.browse(cr, uid, ids[0], context=context)
        rem = lambda r_id: (2, r_id)
        res = []
        for campo in tipo_doc.campos_ids:
            res.append(rem(campo.id))
        return self.write(cr, uid, ids, {"campos_ids": res, "modelo_id": False}, context=context)

    def onchange_template(self, cr, uid, ids, template, context=None):
        local = join(dirname(__file__), "templates", template if template else "\b")
        if exists(local):
            with open(local) as arq:
                valor = arq.read()
            result = {"template": valor}
            config = self._ARQS_HTML_CONFIG.get(template, {})
            result.update(config)
            texto = u"Simples substituição:\n{tags}\n"\
                u"Mako:\n{mako}"
            tags, mako = u"", u""
            if "numero" in result:
                tags += u"{{NUMERO}}, "
                mako += u"numero, "
            if "destinatario" in result:
                tags += u"{{DESTINATARIO}}, "
                mako += u"destinatario, "
            if "data" in result:
                tags += u"{{DATA}}, "
                mako += u"data, "
            if "cabecalho" in result:
                tags += u"{{CABECALHO}}, "
                mako += u"cabecalho, "
            if "assunto" in result:
                tags += u"{{ASSUNTO}}, "
                mako += u"assunto, "
            if "conteudo" in result:
                tags += u"{{CONTEUDO}}, "
                mako += u"conteudo, "
            if "rodape" in result:
                tags += u"{{RODAPE}}, "
                mako += u"rodape, "
            result["ajuda_campos"] = texto.format(tags=tags[:-2], mako=mako[:-2])
            result["name"] = config.get("nome")
            return {"value": result}
        else:
            return {"value": {"template": False}}
    
    def onchange_campo(self, cr, uid, ids, numero, destinatario, data, cabecalho, assunto, conteudo, rodape, modulo_externo, campos):
        texto = u"Simples substituição:\n{tags}\n"\
                u"Mako:\n{mako}"
        if modulo_externo:
            if campos:
                def nome_campo(valor):
                    if valor[0] == 0: # Adicionando valor
                        return valor[2]["name"]
                    if valor[0] == 1: # Atualizando valor
                        return valor[2].get("name", self.pool.get("ud.documento.tipo.campo").browse(cr, uid, valor[1]).name)
                    if valor[0] == 4: # Valor existente
                        return self.pool.get("ud.documento.tipo.campo").browse(cr, uid, valor[1]).name
                nome = nome_campo(campos[0])
                mako = nome
                tags = u"{{%s}}" % nome.upper()
                for campo in campos[1:]:
                    nome = nome_campo(campo)
                    mako += u", " + nome
                    tags += (u", {{%s}}" % nome.upper())
                return {"value": {"ajuda_campos": texto.format(tags=tags, mako=mako)}}
        else:
            tags = u""
            mako = u""
            if numero:
                tags += u"{{NUMERO}}, "
                mako += u"numero, "
            if destinatario:
                tags += u"{{DESTINATARIO}}, "
                mako += u"destinatario, "
            if data:
                tags += u"{{DATA}}, "
                mako += u"data, "
            if cabecalho:
                tags += u"{{CABECALHO}}, "
                mako += u"cabecalho, "
            if assunto:
                tags += u"{{ASSUNTO}}, "
                mako += u"assunto, "
            if conteudo:
                tags += u"{{CONTEUDO}}, "
                mako += u"conteudo, "
            if rodape:
                tags += u"{{RODAPE}}, "
                mako += u"rodape, "
            return {"value": {"ajuda_campos": texto.format(tags=tags[:-2], mako=mako[:-2])}}
        return {"value": {"ajuda_campos": False}}
    
    @staticmethod
    def gerar_pdf(cr, tipo, dados, abs_path=None, base64=True):
        """
        Gera um pdf condificado, ou não, em base64.
        
        :param cr: Cursos da base de dados
        :param dados: Dados a serem inseridos no template
        :type dados: Dicionário com no nome do campo e valor do mesmo.
        :param tipo: Nome ou ID do tipo de documento
        :type tipo: String ou inteiro
        :param abs_path: Local absoluto a ser inserido caso necessite inserir imagens presentes
               no sistema de arquivos, tal como o local do módulo.
        :type abs_path: String com o local configurado apropriadamente.
        :param base64: Define se o Pdf deverá ser condificado ou não para base 64.
        
        :raise UnknownDocType: Caso o tipo de documento não seja encontrado.
        :raise osv.except_osv: Se existir código inválido no template do tipo de documento especificado.
        
        :return: Uma instância da classe Pdf.
        """
        global falta_dependencias
        if falta_dependencias:
            raise osv.except_osv(u"Requisitos não atendidos",
                                 u"Os requisitos do módulo de documentos não foram atendidos.\n"\
                                 u"Erro: %s" %falta_dependencias)
        pool = RegistryManager.get(cr.dbname)
        doc_tipo = pool.get("ud.documento.tipo")
        if isinstance(tipo, str):
            tipo = doc_tipo.search(cr, SUPERUSER_ID, [("name", "=", tipo)])
            if not tipo:
                return False
            tipo = tipo[0]
        if not isinstance(tipo, (int, long)):
            raise UnknownDocType(u"Tipo de documento não encontrado: %s" % str(tipo))
        template = doc_tipo.read(cr, SUPERUSER_ID, tipo, ["template"], load="_classic_write")
        if template:
            template = template.get("template")
        else:
            raise UnknownDocType(u"Tipo de documento não encontrado: %s" % str(tipo))
        try:
            return Pdf(template, dados, abs_path, base64)
        except TemplateError:
            raise osv.except_osv(u"Template Inválido",
                                 u"O template definido para o tipo de documento atual é inválido.")

ud_documento_tipo()

class ud_documento_anexo(osv.osv):
    _name = "ud.documento.anexo"
    _description = u"Anexo de Documentos (UD)"
    _order = "name asc"
    
    def _valida_tipo_arquivo(self, cr, uid, ids, **kwargs):
        """
        Verifica se o anexo é um PDF
        """
        global falta_dependencias
        if falta_dependencias:
            raise osv.except_osv(u"Requisitos não atendidos",
                                 u"Os requisitos do módulo de documentos não foram atendidos.\n"\
                                 u"Erro: %s" %falta_dependencias)
        for doc in self.browse(cr, uid, ids, **kwargs):
            return Pdf.is_pdf(doc.anexo)
    
    _columns = {
        "name": fields.char(u"Nome"),
        "anexo": fields.binary(u"Arquivo", required=True),
        "documento_id": fields.many2one("ud.documento", u"Documento", readonly=True, ondelete="cascade"),
    }
    
    _constraints = [
        (_valida_tipo_arquivo, u"Apenas arquivos PDF são aceitos!", [u"\nArquivo inválido"]),
    ]
    
#     _rec_name = "nome_arquivo"

ud_documento_anexo()

class ud_documento(osv.osv):
    _name = "ud.documento"
    _description = u"Dados do documento (UD)"
    _order = "tipo_id asc"
    
    def _visibilidade(self, cr, uid, ids, field, arg, context=None):
        """
        Busca no tipo dos documentos os campos que devem permanecer visíveis e obrigatórios.
        
        :param cr: Cursor do Banco de dados
        :param uid: ID do Usuário
        :type uid: Inteiro
        :param ids: ID ou lista de IDs de documentos
        :type ids: Inteiro, lista ou tupla
        :param field: Nome do campo alvo
        
        :return: Retorna um dicionário tendo como chave o id do documento e valor True ou False
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        result = {}.fromkeys(ids, False)
        field = field[:-5]
        docs = self.browse(cr, uid, ids, context=context)
        doc_tipo_model = self.pool.get("ud.documento.tipo")
        for doc in docs:
            doc_tipo = doc_tipo_model.read(cr, uid, doc.tipo_id.id, [field], context=context, load="_classic_write")
            result[doc.id] = doc_tipo.get(field)
        return result
    
    def _criador(self, cr, uid, context=None):
        """
        Busca qual pessoa no núcleo está vinculada ao usuário atualmente logado.
         
        :param cr: Cursor do Banco de dados
        :param uid: ID do Usuário logado
        :type uid: Inteiro
         
        :return: Retorna o id de um registro de ud_employee
         
        :raise osv.except_osv: Caso o número de registros de ud_employee seja diferente de 1.
        """
        ud_usuario_id = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)], limit=2)
        if not ud_usuario_id:
            raise osv.except_osv(u"Vinculo Pessoa-Usuário",
                             u"Não existen nenhuma pessoa cadastrada no núcleo vinculada ao usuário informado.")
        if len(ud_usuario_id) > 1:
            raise osv.except_osv(u"Vinculo Pessoa-Usuário",
                             u"O mesmo login está vinculado à multiplas pessoas no núcleo.")
        return ud_usuario_id[0]
    
    def _setores(self, cr, uid, context=None):
        pessoa = self.pool.get("ud.employee").browse(cr, SUPERUSER_ID, self._criador(cr, uid, context), context=context)
        res = []
        for perfil in pessoa.papel_ids:
            if perfil.ud_setores:
                res.append((perfil.ud_setores.id, perfil.ud_setores.name))
        return res
    
    _columns = {
        "tipo_id": fields.many2one("ud.documento.tipo", u"Tipo", required=True, domain=[("modulo_externo", "=", False)], ondelete="restrict"),
        "numero": fields.char(u"Número", required=True),
        "data": fields.date(u"Data", required=True),
        "cabecalho": fields.text(u"Cabeçalho"),
        "destinatario": fields.text(u"Destinatário(s)"),
        "assunto": fields.char(u"Assunto"),
        "conteudo": fields.text(u"Conteúdo"),
        "rodape": fields.text(u"Rodapé"),
        "anexos": fields.one2many("ud.documento.anexo", "documento_id", string=u"Anexos", ondelete="restrict",
                                  help=u"Faça o upload somente de arquivos em PDF."),
        "nome_pdf": fields.char(u"PDF"),
        "pdf": fields.binary(u"Versão em PDF", readonly=True, help=u"Ultima versão em PDF salva do documento"),
        "criador_id": fields.many2one("ud.employee", u"Criador", ondelete="restrict", readonly=True, required=True),
        "setores": fields.selection(_setores, u"Setor Proprietário", help=u"Setor que o documento pertence"),
        "setor_id": fields.many2one("ud.setor", u"Setor Proprietário", readonly=True, ondelete="restrict", help=u"Setor que o documento pertence"),
        
        # Campos de controle
        "numero_func": fields.function(_visibilidade, type="boolean", store=False, method=True, invisible=True),
        "data_func": fields.function(_visibilidade, type="boolean", store=False, method=True, invisible=True),
        "cabecalho_func": fields.function(_visibilidade, type="boolean", store=False, method=True, invisible=True),
        "destinatario_func": fields.function(_visibilidade, type="boolean", store=False, method=True, invisible=True),
        "assunto_func": fields.function(_visibilidade, type="boolean", store=False, method=True, invisible=True),
        "conteudo_func": fields.function(_visibilidade, type="boolean", store=False, method=True, invisible=True),
        "rodape_func": fields.function(_visibilidade, type="boolean", store=False, method=True, invisible=True),
        "anexos_func": fields.function(_visibilidade, type="boolean", store=False, method=True, invisible=True),
    }
    
    _sql_constraints = [
         ("doc_uniq", "unique (tipo_id, numero, setor_id)", u"Já existe um documento com esse numero para esse tipo nesse setor"),
    ]
    
    _defaults = {
        "criador_id": lambda self, cr, uid, context=None: self._criador(cr, uid, context),
        "nome_pdf": u"documento.pdf"
    }
    
    def create(self, cr, uid, vals, context=None):
        """
        Gera um PDF com as informações dadas e cria um novo registro.
        
        :see: osv.osv.create
        
        :raise osv.except_osv: Se tipo de documento for inválido ou não tenha sido selecionado.
        """
        valores = vals.copy()
        anexos = []
        for anexo in valores.get("anexos"):
            anexos.append(anexo[2].get("anexo"))
        valores["anexos"] = anexos
        doc_tipo_model = self.pool.get("ud.documento.tipo")
        try:
            pdf = doc_tipo_model.gerar_pdf(cr, valores.pop("tipo_id"), valores, dirname(__file__))
        except UnknownDocType:
            raise osv.except_osv(u"Tipo de documento",
                                 u"Não foi possível definir o tipo de documento. Possivelmente ele não tenha sido criado "\
                                 u"ou selecionado")
        vals["pdf"] =  pdf.pdf
        vals["nome_pdf"] =  u"{} - Nº {}.pdf".format(self.pool.get("ud.documento.tipo").browse(cr, uid, vals["tipo_id"]).name, vals["numero"])
        vals["setor_id"] = vals.get("setores")
        return super(ud_documento, self).create(cr, uid, vals, context=context)
    
    def write(self, cr, uid, ids, vals, context={}):
        """
        Edita os valores do registro atual gerando junto um novo PDF de acordo com as novas alterações.
        
        :see: osv.osv.write
        
        :raise osv.except_osv: Se tipo de documento for inválido ou não tenha sido selecionado.
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = super(ud_documento, self).write(cr, uid, ids, vals, context=context)
        doc_tipo_model = self.pool.get("ud.documento.tipo")
        doc_anexo_model = self.pool.get("ud.documento.anexo")
        docs = self.read(cr, uid, ids, ["tipo_id", "numero", "data", "cabecalho", "destinatario", "assunto", "conteudo",
                                                 "rodape", "anexos"], context=context, load="_classic_write")
        for doc in docs:
            if doc.has_key("anexos"):
                doc["anexos"] =  map(lambda anexo: anexo["anexo"],
                                 doc_anexo_model.read(cr, uid, doc.get("anexos"), ["anexo"], context=context, load="_classic_write"))
            try:
                pdf = doc_tipo_model.gerar_pdf(cr, doc.get("tipo_id"), doc, dirname(__file__))
            except UnknownDocType:
                raise osv.except_osv(u"Tipo de documento",
                                 u"Não foi possível definir o tipo de documento. Possivelmente ele não tenha sido criado "\
                                 u"ou selecionado")
            nome_pdf = u"{} - Nº {}.pdf".format(self.pool.get("ud.documento.tipo").browse(cr, uid, doc["tipo_id"]).name, doc["numero"])
            super(ud_documento, self).write(cr, uid, doc.get("id"), {"pdf": pdf.pdf, "nome_pdf": nome_pdf}, context=context)
        return res
    
    def name_get(self, cr, uid, ids, context=None):
        """
        Processa no nome do registro que será visualizado na interface.
        
        :see: osv.osv.name_get
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        docs = self.read(cr, uid, ids, ["tipo_id", "numero"], context, load='_classic_write')
        doc_tipo_model = self.pool.get("ud.documento.tipo")
        result = []
        for doc in docs:
            tipo_doc = doc_tipo_model.read(cr, uid, doc.get("tipo_id"), ["name"], context=context)
            result.append((doc.get("id"), u"%s - Nº %s" % (tipo_doc.get("name"), doc.get("numero"))))
        return result 
    
    def onchange_tipo(self, cr, uid, ids, v_field, context=None):
        """
        Altera os valores dos campos funcionais para permitir que fiquem invisíveis, ou não, de acordo
        com o tipo de documento selecionado.
        """
        context = context if isinstance(context, dict) else {}
        if not v_field:
            return {"value":{"campos": False, "cabecalho_func": False, "destinatario_func": False, "assunto_func": False,
                             "conteudo_func": False, "rodape_func": False, "anexo_func": False,
                             "cabecalho": None, "destinatario": None, "assunto": None,
                             "conteudo": None, "rodape": None, "anexos": False},
                "context": {}}
        tipo = self.pool.get("ud.documento.tipo").browse(cr, uid, v_field, context=context)
        for campo in tipo.campos_ids:
            context[campo.name] = True
        return {"value":{"campos": ";".join(map(lambda campo: campo.name, tipo.campos_ids)),
                         "cabecalho_func": tipo.cabecalho, "destinatario_func": tipo.destinatario, "assunto_func": tipo.assunto,
                         "conteudo_func": tipo.conteudo, "rodape_func": tipo.rodape, "anexos_func": tipo.anexos},
                "context": context}

ud_documento()

class ud_documento_enviado(osv.osv):
    _name = "ud.documento.enviado"
    _description = u"Envio de documento (UD)"
    _order = "documento_id"
    
    _columns = {
        "recebido_por": fields.many2one("ud.employee", u"Recebido por", readonly=True, ondelete="restrict"),
        "setor_destino_id": fields.many2one("ud.setor", u"Setor destino", required=True, ondelete="restrict"),
        "documento_id": fields.many2one("ud.documento", u"Documento", required=True, ondelete="restrict"),
        "nome_pdf": fields.char(u"PDF"),
        "pdf": fields.binary(u"PDF Enviado", readonly=True),
        "info": fields.text(u"Informações adicionais", required=True),
        "state": fields.selection([
                    ("n_recebido", u"Não recebido"),
                    ("recebido", u"Recebido"),
                    ], u"Status", readonly=True,
                    help=u"Indica se o documento foi lido pelo destinatário."),
        "create_date": fields.datetime(u"Data de Envio", readonly=True),
    }
    
    _defaults = {
        "info": u"Sem informação adicional.",
        "state": "n_recebido",
        "nome_pdf": u"documento.pdf",
    }
    
    def name_get(self, cr, uid, ids, context=None):
        """
        Processa no nome do registro que será visualizado na interface.
        
        :see: osv.osv.name_get
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        envios = self.read(cr, uid, ids, ["setor_destino_id", "documento_id"], context=context, load='_classic_write')
        setor_model = self.pool.get("ud.setor")
        doc_model = self.pool.get("ud.documento")
        result = []
        for envio in envios:
            setor = setor_model.read(cr, SUPERUSER_ID, envio.get("setor_destino_id"), ["name"], context=context, load="_classic_write")
            doc = doc_model.name_get(cr, uid, envio.get("documento_id"), context=context)
            result.append([envio.get("id"), "%s: %s" % (setor.get("name"), doc[0][1])])
        return result
    
    def create(self, cr, uid, vals, context=None):
        """
        Salva um registro de ud.documento.enviado no banco tendo como valor do campo "pdf" o mesmo valor pertencente ao pdf
        gerado em ud.documeto. Em seguida cria um registro de ud.documento.recebido apenas informando o nome e o id de
        ud.documento.enviado atual.
        
        :see: osv.osv.create
        """
        doc_id = vals.get("documento_id")
        sp = False
        if doc_id:
            doc = self.pool.get("ud.documento").browse(cr, uid, doc_id, context=context)
            vals["pdf"] = doc.pdf
            vals["nome_pdf"] = doc.nome_pdf
            sp = doc.setor_id.id
        res = osv.osv.create(self, cr, uid, vals, context=context)
        self.pool.get("ud.documento.recebido").create(cr, SUPERUSER_ID, {"name": self.name_get(cr, uid, res, context=context)[0][1],
                                                                         "doc_enviado_id": res,
                                                                         "setor_remetente_id": sp})
        return res
    
    def onchange_doc(self, cr, uid, ids, doc_id, context={}):
        """
        Altera o valor do campo PDF em ud.documento.enviado de acordo com o documento selecionado.
        Caso seja selecionado um documento, o PDF gerado deve ser seu valor, caso contrário, False
        será o valor do campo
        """
        if doc_id:
            doc = self.pool.get("ud.documento").browse(cr, uid, doc_id, context=context)
            return {"value": {"pdf": doc.pdf}}
        return {"value": {"pdf": False}}
    
    def enviar_email(self, cr, uid, ids):
        raise NotImplementedError

ud_documento_enviado()

class ud_documento_recebido(osv.osv):
    _name = "ud.documento.recebido"
    _description = u"Recebimento de documento (UD)"
    
    _STATUS = [("n_recebido", u"Não recebido"), ("recebido", u"Recebido"), ]
    
    _columns = {
        "name": fields.char(u"Título", readonly=True),
        "doc_enviado_id": fields.many2one("ud.documento.enviado", readonly=True, invisible=True, ondelete="cascade"),
        "nome_pdf": fields.related("doc_enviado_id", "nome_pdf", type="char", string=u"Nome PDF", readonly=True),
        "pdf": fields.related("doc_enviado_id", "pdf", type="binary", string=u"Documento", readonly=True),
        "info": fields.related("doc_enviado_id", "info", type="text", string=u"Informações adicionais", readonly=True),
        "state": fields.related("doc_enviado_id", "state", type="selection", selection=_STATUS, string=u"Status",
                                readonly=True, help=u"Indica se o documento foi lido pelo destinatário."),
        "remetente_id": fields.related("doc_enviado_id", "documento_id", "criador_id", type="many2one", relation="ud.employee",
                                       string=u"De", readonly=True),
        "setor_remetente_id": fields.many2one("ud.setor", u"Setor do Rementente", readonly=True),
        "setor_destino_id": fields.related("doc_enviado_id", "setor_destino_id", type="many2one", relation="ud.setor",
                                           string=u"Para", required=True, readonly=True),
        "recebido_por": fields.many2one("ud.employee", u"Recebido por", readonly=True),
        "create_date": fields.datetime(u"Data de Recebimento", readonly=True),
    }
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False, setor=True):
        """
        Busca os IDs dos documentos recebidos com base em um conjunto de condições inseridas, além de filtrar
        IDs por setor que o usuário esteja vinculado.
        
        :param setor: Define se a busca será filtrada por vínculo com o setor
        :see: osv.osv.search
        
        :raise osv.except_osv: Caso o número de registros de ud_employee seja diferente de 1.
        """
        if setor:
            ud_usuario_id = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)])
            if not ud_usuario_id:
                raise osv.except_osv(u"Vinculo Pessoa-Usuário",
                                 u"Não existen nenhuma pessoa cadastrada no núcleo vinculada ao usuário informado.")
            if len(ud_usuario_id) > 1:
                raise osv.except_osv(u"Vinculo Pessoa-Usuário",
                                 u"O mesmo login está vinculado à multiplas pessoas no núcleo.")
            cr.execute("""SELECT 
                                ud_documento_recebido.id
                          FROM 
                                ud_documento_recebido, ud_documento_enviado, ud_perfil
                          WHERE
                                ud_documento_enviado.setor_destino_id = ud_perfil.ud_setores
                                and 
                                ud_perfil.ud_papel_id = %i
                                and
                                ud_documento_enviado.id = ud_documento_recebido.doc_enviado_id;""" % ud_usuario_id[0])
            return map(lambda linha: linha[0], cr.fetchall())
        return super(ud_documento_recebido, self).search(self, cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)
    
    def botao_marcar_recebido(self, cr, uid, ids, context=None):
        """
        Marca o registro de ud.documento.enviado vinculado ao ud.documento.recebido com o status "recebido"
        
        :raise osv.except_osv: Caso o número de registros de ud_employee seja diferente de 1.
        """
        res = self.pool.get("ud.employee").search(cr, SUPERUSER_ID, [("user_id", "=", uid)])
        if not res:
            raise osv.except_osv(u"Vinculo Pessoa-Usuário",
                                 u"Não existen nenhuma pessoa cadastrada no núcleo vinculada ao usuário informado.")
        if len(res) > 1:
                raise osv.except_osv(u"Vinculo Pessoa-Usuário",
                                 u"O mesmo login está vinculado à multiplas pessoas no núcleo.")
        docs_enviados = self.read(cr, uid, ids, ["doc_enviado_id"], context=context, load="_classic_write")
        docs_enviados = map(lambda valor: valor.get("doc_enviado_id"), docs_enviados)
        self.pool.get("ud.documento.enviado").write(cr, uid, docs_enviados, {"state": "recebido", "recebido_por": res[0]}, context=context)
        return self.write(cr, uid, ids, {"state":"recebido", "recebido_por":res[0]}, context=context)

ud_documento_recebido()
