# Manual de uso de máscaras Javascript

Tutorial simples para aplicação de máscaras javascript (Atualizando para nova versão do [MaskedInput](http://igorescobar.github.io/jQuery-Mask-Plugin/))

## Aplicando máscaras

Para usar as máscaras, é necessário apenas adicionar a classe css referente ao tipo de informação do campo, exemplo:
```xml
...
<field name="solicitante_telefone"  class="telefone" />
...
<field name="data_nascimento"  class="data" />
...
```

### Classes disponíveis

<table>
	<thead>
		<tr>
			<td>Classe</td>
			<td>Seletor</td>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td>telefone</td>
			<td> $(".telefone input") </td>
		</tr>
		<tr>
			<td>cpf</td>
			<td>$(".cpf input")</td>
		</tr>
		<tr>
			<td>data</td>
			<td>$(".data input")</td>
		</tr>
		<tr>
			<td>agencia</td>
			<td>$(".agencia input")</td>
		</tr>
		<tr>
			<td>conta</td>
			<td>$(".conta input")</td>
		</tr>
		<tr>
			<td>valor</td>
			<td>$('.valor input')</td>
		</tr>
		<tr>
			<td>data-hora</td>
			<td>$(".data-hora input")</td>
		</tr>
	</tbody>
</table>

**Obs: ** O seletor `valor`, se refere a dinheiro

**Obs² : ** A máscara `data-hora` não é atualmente compatível com o formato do field datetime.

## Criando novas máscaras

Para manter a organização, é recomendado que qualquer novo tipo de máscara seja inserido no módulo do webclient, assim, a máscara ficará disponível para todos os módulos.

**Obs: ** É recomendável que o desenvolvedor tenha um mínimo de conhecimento sobre o framework Backbone.js, assim como na linguagem javascript

É possível extender ainda mais as funcionalidades do Webclient apenas sobrescrevendo o model Backbone base para todas as views, assim é possível adicionar novas máscaras usando o mecanismo de herança e composição do framework Backbone, por exemplo:

```js
// Adicionando escopo para as alterações
openerp.<nome_do_modulo> = function(openerp){
	// herdando o objeto View do módulo web
	openerp.web.View.include({
		// herdando o método "do_show", que realiza a renderização dos elementos
		do_show : function(){
			// Chamando o método original
			this._super.apply(this, arguments);
			// Adicione seu código aqui
			// Por exemplo: Novas máscaras
			$(".hora input").mask("99h 99m", {clearIfNotMatch: true});
			// também é possível associar eventos usando JQuery ou qualquer outro código javascript
		},
		// ... Ou, o próprio Backbone usando o subobjeto events, por exemplo:
		events : {
			 // "<evento> <seletor_css>" : "<metodo>",
			 "click button" : "metodo_x",
		},
		metodo_x : function(){
			// Seu código
		}
	});
};
```
