/*

################################ Máscaras Javascript ################################

Para inserir máscaras de campo nos campos do OpenERP:

 - Não faça isso se não tiver conhecimento com Javascript.

 - Primeiro, verifique se existe o diretório Estático no módulo:
 
 static/src/js/
 
 Caso negativo:
	- Crie o diretório e insira-o nos metadados do seu módulo
	
	__openerp__.py
		...
		'js' : ['static/src/js/*.js']
		...
	
	- Faça o donwload do jQuery Masked input e coloque no diretório
	- Crie o arquivo .js para a personalização no mesmo diretório.
	- Insira o seguinte código no seu .js
	
	Obs: Assuma como "nomeDoSeuModulo" a pasta que contém o seu módulo
*/

// Esta linha declara a inicialização do código Javascript caso o seu módulo
// esteja instalado e possua "actions" no banco de dados

openerp.ud = function (openerp) {
	
	/*
	 * Vamos recuperar o objeto View do módulo web e sobrescrever o inicializador
	 * obs: Não vamos sobrescrever o construtor ( init: ), por isso, não use this._super()
	 * Usando o método include temos acesso indireto ao objeto JSON
	 */
	// Desta forma:
	openerp.web.View.include({
		/*
		 * Este será o objeto JSON que será concatenado com o objeto original
		 * Detalhe:
		 * 		Caso prefira criar um widget próprio, pode fazer isso usando o método extend
		 * 		do objeto openerp.web.widget (mas, enfim, não importa).
		 */
		start : function () {
		  
			id = this.load_view();
			/*
			 * Esta função é o inicializador (renderizador) do template Qweb
			 * Cuidado com o que coloca ou retira daqui.
			 */
			// A função setTimeout() foi usada por um problema no atraso do Qweb
			// Dessa forma o problema foi resolvido
			setTimeout(function () {
				// Função que será chamada após oo Timeout
				// Aqui eu fiz as chamada diretas as funções jQuery, 
				// mas, se preferir, pode criar novos membros JSON para cada função
				// E chamá-los aqui depois
				// Exemplo:
				$(".cpf input").mask("999.999.999-99");
				$(".birthday input").mask("99-99-9999");
				$(".mobile_phone input").mask("(99) 9999-9999");
				$(".work_phone input").mask("(99) 9999-9999")
				$(".agencia input").mask("9999-X");
				$(".conta input").mask("99999-9");
				$(".data_validade input").mask("99-99-9999");
				$(".valor_bolsa input").mask("999.99");
				
			}, 500);
			// Mais do mesmo...
			// repetindo o código original:
			// Esse trecho é importante pois o que é feito aqui é a concatenação / regravação do 
			// documento JSON, e não do conteúdo dos seus membros.
			return id;
		}
	
	});
	
	
};
/*
 * Boa Sorte! :D
 */
