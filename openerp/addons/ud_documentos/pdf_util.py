# coding: utf-8

from base64 import b64encode, b64decode
from cStringIO import StringIO
from mako.template import Template
from os.path import join
from pyPdf import PdfFileReader, PdfFileWriter
from weasyprint import HTML
from re import match, UNICODE

class TemplateError(Exception):
    pass

class Pdf():
    """
    Cria um PDF a partir de um template em HTML5 e CSS3, codificado ou não em Base 64, além de permitir a
    mesclagem de outros PDFs no final do PDF resultante.
    
    O template pode conter marcadores entre de chaves duplas e caracters maiúsculos ou utilizando a sintax
    do Mako para execultar códigos em python. A única restrição é que o dicionário que contém os dados que
    serão inseridos no template deve conter como uma de suas chaves a string correspondente.
        Ex.: {{MARCADOR_1}},
             {{MARCADOR_PERSONALIZADO}} ==> {'Marcador_1': VALOR, 'marcador_personalizado': VALOR, ...}
    
    Tratando-se de tabelas, o tipo de dado requisitado é uma matriz (list/tuple de list/tuple) onde a
    primeira posição é o cabeçalho e o restante são as linhas.
        Ex.: [(CABEÇALHO 1, CABEÇALHO 2, ..., CABEÇALHO n), # Cabeçalho
              (LIN_1 COL_1, LIN_1 COL_2, ..., LIN_1 COL_n),
              ...,
              (LIN_n COL_1, LIN_n COL_2, ..., LIN_n COL_n)]
    
    Caso não deseje criar tabelas dessa forma, com a possibilidade de utilização de códigos Python dentro
    do template é possível personalizar a forma de tratatamento dos dados. Para isso, em vez de utilizar
    algum marcador que sejam matrizes, basta utilizar o nome das chaves do dicionário de dados como
    variáveis.
        Ex.: % for linha in variavel:
                 <<CÓDIGO>>
                 ${linha}
                 <<CÓDIGO>>
             % endfor ==> {'variavel': VALOR}

    :see: http://docs.makotemplates.org/en/latest/syntax.html
    """
    
    _template_table = u"""<table{attrs}>
    % if caption:
    % try:
    <caption>${caption}</caption>
    % except UnicodeDecodeError:
    <caption>${unicode(caption)}</caption>
    % endtry
    % endif
    <thead>
        <th>
        % for dado in dados[0]:
        % try:
            <td>${dado}</td>
        % except UnicodeDecodeError:
            <td>${unicode(dado)}</td>
        % endtry
        % endfor
        </th>
    </thead>
    <tbody>
        % for linha in dados[1:]:
        <tr>
        % for dado in linha:
        % try:
            <td>${dado}</td>
        % except UnicodeDecodeError:
            <td>${unicode(dado)}</td>
        % endtry
        % endfor
        </tr>
        % endfor
    <tbody>
</table>"""

    def __init__(self, template, dic, abs_path=None, base64=True, base64_anexos=True):
        """
        :param template: String com o HTML do modelo do PDF.
        :param dic: Dicionario com os dados a serem substituídos nas tags do template.
        :param abs_path: Local absoluto do módulo.
        :param base64: Define se o PDF será codificado para base64. Padrão True.
        
        :attention: As as chaves do dicionário devem ter os mesmos símbolos e letras, maiúsculas ou não,
                    em relação as tags do HTML.
        :attention: Para inserir uma imagem com a tag {{IMG_UFAL}}, o caminho absoluto deve preceder
                    o local "static/src/img/ufal.png".
        
        :raise TemplateError: Caso exista algum erro no processamento do template para código python.
        """
        if dic.has_key("data"):
            data = match("^(?P<ano>\d{4})(?P<sep>[-/])(?P<mes>\d\d)(?P=sep)(?P<dia>\d\d)$", dic["data"], UNICODE)
            if not data:
                data = match("^(?P<dia>\d\d)(?P<sep>[-/])(?P<mes>\d\d)(?P=sep)(?P<ano>\d{4})$", dic["data"], UNICODE)
            if data:
                meses = {'01': u'Janeiro', '02': u'Fevereiro', '03': u'Março', '04': u'Abril',
                         '05': u'Maio', '06': u'Junho', '07': u'Julho', '08': u'Agosto',
                         '09': u'Setembro', '10': u'Outubro', '11': u'Novembro', '12': u'Dezembro'}
                g = data.groupdict()
                g.pop("sep")
                dic.update(g)
                g["mes"] = meses[data.group("mes")]
                dic["data"] = u"{dia} de {mes} de {ano}".format(**g)
            else:
                dic.pop("data")
        template = template.replace(u"{{IMG_UFAL}}", join(u"static", u"src", u"img", u"ufal.png"))
        self.base64 = base64
        try:
            template_mako = Template(text=template, output_encoding="utf-8")
            template = template_mako.render_unicode(**dic)
        except:
            raise TemplateError
        
        for key in dic.keys():
            campo = dic.get(key)
            if campo and isinstance(campo, (list, tuple)):
                if isinstance(campo[0], (list, tuple)):
                    campo = Pdf.tabela_default(campo)
            campo = unicode(campo if campo else "")
            template = template.replace("{{%s}}" %(key.upper()), campo.replace("\n", "<br>"))
        
        self.__pdf = Pdf.to_pdf(template, abs_path)
        if dic.has_key("anexo"):
            self.merge_pdf(dic.get("anexo"), base64_anexos)
        elif dic.has_key("anexos"):
            for anexo in dic.get("anexos"):
                self.merge_pdf(anexo, base64_anexos)
    
    @property
    def pdf(self):
        return b64encode(self.__pdf) if self.base64 else self.__pdf
    
    def toPdf(self):
        """
        Converte o pdf para uma dada configuração.
        
        :return: Retorna o pdf de acordo com as configurações dadas.
        :deprecated: Seu uso pode ser evitado utilizando 'intancia.pdf' ambos com as mesmas funcionalidades.
        """
        return b64encode(self.__pdf) if self.base64 else self.__pdf
    
    def merge_pdf(self, anexo, base64_anexos=True):
        """
        Une o PDF criado a partir dos dados informados com outro PDF, esteja ele codificado ou não
        em base 64.
        
        :param anexo: PDF a ser inserido no final do PDF existente
        :param base64_anexos: Informar se o anexo está codificado ou não em bae 64
        """
        pdf_gerado = PdfFileReader(StringIO(self.__pdf))
        anexo = PdfFileReader(StringIO(b64decode(anexo) if base64_anexos else anexo))
        
        pdf_unido = PdfFileWriter()
        for i in range(0, pdf_gerado.getNumPages()):
            pdf_unido.addPage(pdf_gerado.getPage(i))
        
        for i in range(0, anexo.getNumPages()):
            pdf_unido.addPage(anexo.getPage(i))
        
        stream = StringIO()
        pdf_unido.write(stream)
        stream.seek(0)
        self.__pdf = "".join(stream.readlines())
        stream.close()
    
    @staticmethod
    def is_pdf(arquivo, base64=True):
        """
        Verifica se um arquivo um PDF.
        
        :param arquivo: Dados binários do arquivo a ser verificado
        :type arquivo: 'str' com os dados do arquivo
        :param base64: Informa se o arquivo está condificado em base64.
        
        :return: Retorna True ou False
        
        :attention: Fornecer dados que não sejam um arquivo poderá causar resultados inesperados.
        """
        try:
            PdfFileReader(StringIO(b64decode(arquivo) if base64 else arquivo))
            return True
        except:
            return False
    
    @staticmethod
    def to_pdf(template, abs_path=None):
        """
        Converte um template devidamente preenchido em PDF.
        
        :param template: String com o HTML do modelo do PDF.
        :param abs_path: Local absoluto do módulo.
        
        :return: O PDF renderizado.
        
        :attention: Não será convertido em Base 64.
        """
        if abs_path:
            doc = HTML(string=template, encoding="UTF-8", base_url=abs_path)
        else:
            doc = HTML(string=template, encoding="UTF-8")
        return doc.write_pdf()
    
    @staticmethod
    def tabela_default(dados):
        """
        Cria uma tabela em HTML a partir de um conjunto de listas ou tuplas, sendo a primeira linha o cabeçalho da tabela.
        Atributo padrão: style="border-collapse: collapse;"
        
        :param dados: lista de valores que serão convertidos em tabela em HTML.
        :type dados: array bidimensional
        
        :raise UnicodeDecodeError: Se existir alguma string não Unicode com caracter especial.
        
        :return: HTML Unicode com os dados das listas.
        """
        return Pdf.tabela(dados, border=1, style="border-collapse: collapse;")
    
    @staticmethod
    def tabela(dados, caption=None, **attrs_table):
        """
        Cria uma tabela em HTML a partir de um conjunto de listas ou tuplas, sendo a primeira linha o cabeçalho da tabela.
        
        :param dados: lista de valores que serão convertidos em tabela em HTML.
        :type dados: array bidimensional
        :param caption: Cabeçalho da tabela.
        :keyword **attrs_table: Devem ser os atributos que serão inseridos na tag "table", tal como style".
        
        :raise UnicodeDecodeError: Se existir alguma string não Unicode com caracter especial nos parâmetros 'dados' ou 'caption'.
        
        :return: HTML Unicode com os dados das listas.
        """
        template = Template(text=Pdf._template_table, output_encoding="utf-8")
        tabela = template.render_unicode(dados=dados, caption=caption)
        atributos = lambda dic: "".join([" {}=\"{}\"".format(chave, dic.get(chave)) for chave in dic])
        return tabela.replace("{attrs}", atributos(attrs_table) if attrs_table else "")



