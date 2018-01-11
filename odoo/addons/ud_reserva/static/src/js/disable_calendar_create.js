odoo.define('ud_reserva.calendar_view', function (require) {
    var calndarView = require('web_calendar.CalendarView');

    calndarView.include({
        open_quick_create: function () {
            var calendar_models = ['ud.reserva.dia'];
            if (!(calendar_models.includes(this.model))){
                this._super();
            }
        }
    })
});