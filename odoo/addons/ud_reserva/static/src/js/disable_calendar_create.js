odoo.define('ud_reserva.calendar_view', function (require) {
    var calndarView = require('web_calendar.CalendarView');
    var form_common = require('web.form_common');
    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;

    calndarView.include({
        open_quick_create: function () {
            var calendar_models = ['ud.reserva.dia'];
            if (!(calendar_models.includes(this.model))) {
                this._super();
            }
        }
    });

    calndarView.extend({
        open_event: function (id, title) {
            console.log(title);
            var self = this;
            var calendar_models = ['ud.reserva'];
            if (!(calendar_models.includes(this.model))) {
                new form_common.FormViewDialog(this, {
                    res_model: 'ud.reserva',
                    res_id: parseInt(id).toString() === id ? parseInt(id) : id,
                    context: this.dataset.get_context(),
                    title: title,
                    view_id: +this.open_popup_action,
                    readonly: true,
                    buttons: [
                        {
                            text: _t("Edit"), classes: 'btn-primary', close: true, click: function () {
                            self.dataset.index = self.dataset.get_id_index(id);
                            self.do_switch_view('form', {mode: "edit"});
                        }
                        },

                        {
                            text: _t("Delete"), close: true, click: function () {
                            self.remove_event(id);
                        }
                        },

                        {text: _t("Close"), close: true}
                    ]
                }).open();
                return false;
            }
        }
    })
});