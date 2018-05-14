openerp.ud_monitoria = function (openerp) {
    openerp.web.form.widgets.add("hora", "openerp.ud_monitoria.Hora");
    openerp.ud_monitoria.Hora = openerp.web.form.FieldChar.extend({
        template: "hora",
        init: function (view, code) {
            this._super(view, code);
        }
    });
    openerp.web.form.widgets.add("semestre", "openerp.ud_monitoria.Semestre");
    openerp.ud_monitoria.Semestre = openerp.web.form.FieldChar.extend({
        template: "semestre",
        init: function (view, code) {
            this._super(view, code);
        }
    });

    if (typeof jQuery == "undefined") {
        var script = document.createElement('script');
        script.src = 'http://code.jquery.com/jquery-1.11.0.min.js';
        script.type = 'text/javascript';
        document.getElementsByTagName('head')[0].appendChild(script);
    }
};
