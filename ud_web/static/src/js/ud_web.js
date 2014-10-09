openerp.ud_web = function (openerp){

	instance = openerp;

	openerp.web.WebClient.include ({
		_template : "UdWebClient",
	    show_application: function() {
	        var self = this;
	        self.toggle_bars(true);
	        self.update_logo();
	        self.menu = new openerp.web.Menu(self);
	        self.menu.replace(this.$el.find('.oe_menu_placeholder'));
	        self.menu.on('menu_click', this, this.on_menu_action);
	        self.user_menu = new openerp.web.UserMenu(self);
	        self.user_menu.replace(this.$el.find('.oe_user_menu_placeholder'));
	        self.user_menu.on('user_logout', self, self.on_logout);
	        self.user_menu.do_update();
	        self.bind_hashchange();
	        self.set_title();
	        self.check_timezone();
	        // Meu método
	        self.mostra_menu();
	    },
	    mostra_menu: function (){
	    	$('#botao-menu-opcoes').click(function(){
	    		$(".menu-principal").slideToggle();
	    	});
	    	$("#botao-fechar").click(function (){
	    		$(".menu-principal").slideToggle();
	    	});
			setTimeout(function(self){
				$(".menu-principal").slideToggle();
		    	$(".oe_secondary_menus_container li a").click(function (){
		    		$(".menu-principal").slideToggle();
		    	});
			}, 5000);
	    },
	});
};