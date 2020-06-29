odoo.define('web_widget_time_delta.TimeDelta', function(require) {
    "use strict";

    var field_registry = require('web.field_registry');
    var Field = field_registry.get('char');
    var core = require('web.core');
    var _t = core._t;

    var FieldTimeDelta = Field.extend({



        template: 'FieldTimeDelta',
        widget_class: 'oe_form_field_time_delta',

        init: function () {

            this._super.apply(this, arguments);
            this.mask_humanize = undefined;
            this.showDays = false;
            this.showSeconds = false;

            if ("mask_humanize_string" in this.nodeOptions) {
                this.mask_humanize = this.nodeOptions["mask_humanize_string"];
            }

            if ("mask_humanize_field" in this.nodeOptions) {
                this.mask_humanize = this.recordData[this.nodeOptions["mask_humanize_field"]];
            }

            var mask_picker = "";
            if ("mask_picker_string" in this.nodeOptions) {
                mask_picker = this.nodeOptions["mask_picker_string"];

                if (mask_picker === "day_second"){
                    this.showDays = true;
                    this.showSeconds = true;
                }
                if (mask_picker === "day"){
                    this.showDays = true;
                }
                if (mask_picker === "second"){
                    this.showSeconds = true;
                }
            }

            if ("mask_picker_field" in this.nodeOptions) {
                mask_picker = this.recordData[this.nodeOptions["mask_picker_field"]];

                if (mask_picker === "day_second"){
                    this.showDays = true;
                    this.showSeconds = true;
                }
                if (mask_picker === "day"){
                    this.showDays = true;
                }
                if (mask_picker === "second"){
                    this.showSeconds = true;
                }
            }

        },

        _renderReadonlyValue: function (value) {

            if (this.mask_humanize){
                return  humanizeDuration(value*1000,{ units: this.mask_humanize.split(","),  round: true});
            }
            else{
                return humanizeDuration(value*1000);
            }
        },


        _renderReadonly: function () {
            var total = parseInt(this.value, 10);

            this.$el.text(this._renderReadonlyValue(total));



        },

        _getValue: function () {
            var $input = this.$el.find('input');
            return $input.val();
        },

        _renderEdit: function () {

                var show_value = parseInt(this.value, 10);
                var $input = this.$el.find('input');
                $input.val(show_value);
                var self = this;
                $input.durationPicker({
                  translations: {
                        day: _('day'),
                        hour:  _('hour'),
                        minute:  _('minute'),
                        second:  _('second'),
                        days:  _('days'),
                        hours:  _('hours'),
                        minutes:  _('minutes'),
                        seconds:  _('seconds')
                      },

                    showSeconds: self.showSeconds,
                    showDays:  self.showDays,
                    onChanged: function (newVal) {
                        $input.val(newVal);
                    }
                });
                this.$input = $input;

        },





    });



    field_registry
        .add('time_delta_list', FieldTimeDelta)
        .add('time_delta', FieldTimeDelta);


return {
    FieldTimeDelta: FieldTimeDelta
};

});
