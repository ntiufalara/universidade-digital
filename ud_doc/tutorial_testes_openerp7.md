# Tutorial API de testes OpenERP v7

Usando a API YAML para testes (baseado [nesse tutorial](http://www.zbeanztech.com/blog/how-effective-yaml-testing-openerp))

Os testes usando YAML são uma maneira simples de realizar testes em módulos do OpenERP sem possuir muito conhecimento (envolvimento) com programação, no tutorial do link acima fica demonstrado a construção colaborativa entre especialista e desenvolvedor dos casos de teste.

## Criando testes YAML

A estrutura básica de um teste YAML é exemplificada a seguir:

```yaml
-
  Testamdo a inserção do campus Arapiraca
-
  !record {model: ud.campus, id: campus_arapiraca}:
    name: Arapiraca

-
  !assert {model: ud.campus, id: campus_arapiraca, severity: error, string: O nome do campus precisa ser Arapiraca}:
    - name == "Arapis"

```

O teste exemplificaddo acima deve causar um erro pois os nomes comparados são diferentes.

Também é possível executar código Python nos testes, por exemplo:

```yaml
-
  !python {model: survey.request}: |
    self.survey_req_waiting_answer(cr, uid, [ref("survey_request_1")], context)

```

Para executar, é necessário adicionar o arquivo YML aos metadados do módulo:

Arquivo \_\_init\_\_.py

**Obs**: Supondo que o nome do arquivo `.yml` é `campus.yml` e ele está tentro da pasta `test`.

```python
...
'test': [
    'test/campus.yml',
],
...
```

## Executando os testes

É recomendado criar um banco de dados só para realizar os testes, visto que os módulos precisam ser atualizados e/ou resinstalados para executar os testes.

Executando o comando:

`./openerp-server -d dbteste -i ud --test-enable --log-level=test`

O `-i` pode ser subistituído por `-u` caso o módulo já esteja instalado

## Usando o unittest2 com Python

A seguir exemplificaremos o uso do framework python `unittest2` em conjunto com a API de testes do OpenERP para criar testes unitários. Esse método é um complemento a API XML/YAML para testes server-side. Para realizar testes client-side existe um framework de testes unitários javaScript dentro do pacote padrão do OpenERP que também funciona com o QUnit e o PhamtonJS.

Os teste unitários com unittes2 devem ser usados para testes em cenários específicos ou para testar funcionalidades ou permissões que não podem ser testadas através da API YAML de testes, portanto, esses testes unitários não devem cobrir testes de CRUD (apesar de ser possível, é bem mais trabalhoso realizar testes CRUD dessa forma).

## Estrutura de arquivos

Para começar, vamos criar a estrutura básica de testes de módulo e entender alguns conceitos.

### Exemplo:

```
ud/
    __init__.py
    ud.py
    ...
    tests/
          __init__.py
          test_ud_emplyee.py
          ...
```

A estrutura acima adicionada ao módulo `ud` acrescenta o pacote python `tests` onde serão armazenados e escritos os testes unitários para o módulo.

## Suítes de teste

Para adicionar testes unitários ao OpenERP, é necessário adicionar os módulos de teste ao mecanismo `test suite`, a versão 7 utiliza duas suites de testes nomeadas `fast_suite` e `checks`

A suite `fast_suite` deve conter apenas os testes que podem ser executados frequentemente após a instalação ou atualização do módulo (testes longos não devem ser especificados nessa lista).

O funcionamento da suite `checks` é análogo a `fast_suite`, porém os testes dessa lista são executados a cada instalação de módulo (Qualquer módulo), migração de banco de dados ou mesmo periodicamente durante o estado de produção através de `Cron Threads`.

Quando o teste não é listado em nenhuma das suites, ele é adicionado automaticamente as duas listas.

## Adicionando teste a Suíte

Exemplificando essa etapa, temos:

Arquivo \_\_init\_\_.py

```python
import test_ud_employee
...
fast_suite = [
  test_ud_employee,
  ...
]
checks = [
  test_ud_employee,
  ...
]
```

## Criando caso de teste

Vamos criar um caso de teste simples para exemplificar o uso do `unittest2`

Arquivo test_ud_emplyee.py

```python
# -*- encoding: UTF-8 -*-

import unittest2
# Para testar as views, usaremos o lxml
from lxml import etree
# Importando o framework de testes
from openerp.tests import common
# Importanto o logger
from openerp.tools.misc import mute_logger

# Grupo usado para teste (Opcional)
GROUP = "base.admin_ud"

# também e possível criar casos de teste usando a classe unittest2.TestCase, porém os testes devem ser estáticos
class Teste_ud_emplyee(common.TransactionCase):
  def setUp(self):
      super(Teste_ud_emplyee, self).setUp()
      self.ud_employee = self.registry('ud.employee')
      self.demo_uid = 3
      self.group = self.registry('ir.model.data').get_object(self.cr, self.uid,*(GROUP.split('.')))

  def test_fields_browse_restriction(self):
      """
      Testamdo acesso a campos restritos
      """
      # Adiciona o grupo como atributo de permissão do campo matrícula
      self.ud_employee._columns['matricula'].groups = GROUP
      try:
          P = self.ud_employee
          # Buscando um employee qualquer
          pid = P.search(self.cr, self.demo_uid, [], limit=1)[0]
          # Recuperando os registros
          part = P.browse(self.cr, self.demo_uid, pid)
          # Esse acesso não deve levantar excessão
          part.cidade
          # ... Esse acesso deve levantar uma excessão caso o grupo não seja permitido
          # Nesse caso, a excessão ocorre dentro do bloco with, não influenciando na execução
          # A excessão é armazenada na variável "cm"
          with self.assertRaises(openerp.osv.orm.except_orm) as cm:
              with mute_logger('openerp.osv.orm'):
                  part.matricula
          # ... Verifica se o acesso foi mesmo proibido, caso contrário, o teste falha
          self.assertEqual(cm.exception.args[0], 'Access Denied')
      finally:
          # Retira o atributo adicionado para o teste, retornando ao estado original
          self.ud_employee._columns['email'].groups = False
```

## Executando os testes

É recomendado criar um banco de dados só para realizar os testes, visto que os módulos precisam ser atualizados e/ou resinstalados para executar os testes.

Executando o comando:

`./openerp-server -d dbteste -i ud --test-enable --log-level=test`

O `-i` pode ser subistituído por `-u` caso o módulo já esteja instalado
