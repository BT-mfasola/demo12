odoo.define('ks_list_view_manager.ks_color_picker', function (require) {
    "use strict";

    require('web.dom_ready');

    var registry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');

    var QWeb = core.qweb;

    var KsColorPicker = AbstractField.extend({

        supportedFieldTypes: ['char'],

        events: _.extend({}, AbstractField.prototype.events, {
            'change.spectrum .ks_color_picker': '_ksOnColorChange',

        }),

        init: function (parent, state, params) {
            this._super.apply(this, arguments);
        },


        _render: function () {
            this.$el.empty();
            var ks_color_value = '#376CAE';
            if (this.value) {
                ks_color_value = this.value.split(',')[0];
            }
            var $view = $("<input class='ks_color_picker'/>")

            this.$el.append($view)

            this.$el.find(".ks_color_picker").spectrum({
                color: ks_color_value,
                showInput: true,
                hideAfterPaletteSelect: true,

                clickoutFiresChange: true,
                showInitial: true,
                preferredFormat: "rgb",
            });

            if (this.mode === 'readonly') {
                this.$el.find('.ks_color_picker').addClass('ks_not_click');
                this.$el.find('.ks_color_picker').spectrum("disable");
            } else {
                this.$el.find('.ks_color_picker').spectrum("enable");
            }
        },

        _ksOnColorChange: function (e, tinycolor) {
            this._setValue(tinycolor.toHexString());
        },

    });
    registry.add('ks_color_picker', KsColorPicker);

    return {
        KsColorPicker: KsColorPicker
    };

});