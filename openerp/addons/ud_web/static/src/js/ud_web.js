openerp.ud_web = function (openerp){

	instance = openerp;

	openerp.web.View.include({
		do_show : function () {
			this._super.apply(this, arguments);

			var maskBehavior = function (val) {
			 return val.replace(/\D/g, '').length === 11 ? '(00) 00000-0000' : '(00) 0000-00009';
			},
			options = {onKeyPress: function(val, e, field, options) {
			 field.mask(maskBehavior.apply({}, arguments), options);
			 }
			};
			 
			$('.telefone input').mask(maskBehavior, options);
			$(".cpf input").mask("999.999.999-99", {clearIfNotMatch: true});
			$(".data input").mask("99/99/9999", {clearIfNotMatch: true});
			$(".agencia input").mask("9999-X", {clearIfNotMatch: true});
			$(".conta input").mask("99999-9", {clearIfNotMatch: true});
			$('.valor input').mask('000.000.000.000.000,00', {reverse: true});
			$(".data-hora input").mask("99/99/9999 ás 99h 99m", {clearIfNotMatch: true});
			$(".time").mask("00:00", {clearIfNotMatch: true});
			// Escondendo os menus
			$('.collapse').collapse();
		}
	});

	openerp.web.WebClient.include ({
		_template : "UdWebClient",
	    show_application: function() {
			this._super.apply(this, arguments);
	        // Função que conecta o botão de menu para celulares
	        this.menu_mobile();
	    },
	    menu_ativo: true,
	    menu_mobile: function(){
	    	$("#botao-menu").click(function(){
	    		if (this.menu_ativo){
	    			$(".oe_leftbar").css("left","-320px");
	    			this.menu_ativo = false;
	    		}else{
	    			$(".oe_leftbar").css("left", "0");
	    			this.menu_ativo = true;
	    		}
	    	});
	    },
	    set_title: function(title) {
	        title = _.str.clean(title);
	        var sep = _.isEmpty(title) ? '' : ' - ';
	        document.title = title + sep + 'Universidade Digital';
	    },
	});

	openerp.web.ViewManagerAction.include({
		template : "UdViewManager"
	});

	// Meus widgets
	// Encontrado em:
	//  https://www.odoo.com/forum/help-1/question/how-to-make-a-button-that-triggers-javascript-action-v6-4254
	// ############# MEUS WIDGETS ##############################################
	instance.web.form.widgets.add("mapa", "instance.web.form.mapa");

	instance.web.form.mapa = instance.web.form.FieldText.extend({
		template : "mapa",
//		events : {
			// "click .home_menu a" : "menu_action"
//		},

		init : function () {
			this._super.apply(this, arguments);
		},

		// destroy : {

		// },
	});
	// ############# MEUS WIDGETS - FIM ##############################################
};
