openerp.ud_monitoria = function (openerp) {
    openerp.web.form.widgets.add("hora", "openerp.ud_monitoria.Hora");
    openerp.ud_monitoria.Hora = openerp.web.form.FieldChar.extend({
        template: "hora",
        init: function (view, code) {
            this._super(view, code);
        }
    });
    $(".semestre :input").mask("0000.0", {clearIfNotMatch: true});
};