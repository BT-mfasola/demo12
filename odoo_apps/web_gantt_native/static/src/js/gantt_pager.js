odoo.define('web_gantt_native.Pager', function (require) {
"use strict";


var Widget = require('web.Widget');


var GanttPager = Widget.extend({
    template: "GanttAPS.Pager",
    events: {
        'click .o_pager_limit': '_onEdit',
    },

    init: function (parent, size, limit, options) {
        this.state = {
            size: size,
            limit: limit
        };

        this.options = _.defaults({}, options, {
            can_edit: true, // editable
            single_page_hidden: false, // displayed even if there is a single page
            validate: function() {
                return $.Deferred().resolve();
            },

        });
        this._super(parent);
    },

    start: function () {
        this.$size = this.$('.o_pager_size');
        this.$limit = this.$('.o_pager_limit');
        this.$info = this.$('.gantt_pager_info');

        this._render();
        return this._super();
    },

    refresh: function (size, limit) {

        this.state.size = size;
        this.state.limit = limit;
        this._render()
    },


    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    disable: function () {
        this.disabled = true;
    },

    enable: function () {
        this.disabled = false;
    },


    updateState: function (state, options) {
        _.extend(this.state, state);
        this._render();
        if (options && options.notifyChange) {
            this.trigger('pager_changed', _.clone(this.state));
        }
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _edit: function () {
        if (this.options.can_edit) {
            var self = this;
            var $input = $('<input>', {class: 'o_input', type: 'text', value: this.$limit.html()});
            $input.css({'width': 45 + "px"});
            this.$info.css('display','none');
            this.$limit.html($input);
            $input.focus();

            // Event handlers
            $input.click(function(ev) {
                ev.stopPropagation(); // ignore clicks on the input
            });
            $input.blur(function(ev) {
                self._save($(ev.target)); // save the state when leaving the input
            });
            $input.on('keydown', function (ev) {
                ev.stopPropagation();
                if (ev.which === $.ui.keyCode.ENTER) {
                    self._save($(ev.target)); // save on enter
                } else if (ev.which === $.ui.keyCode.ESCAPE) {
                    self._render(); // leave on escape
                }
            });
        }
    },

    _render: function () {
        var size = parseInt(this.state.size);
        var limit = parseInt(this.state.limit);

        this.do_show();
        this.$info.css('display','inline');

        this.$size.css('color','green');

        if (limit !== 0){
            if (size > limit) {
                this.$size.css('color','red');
            }
        }

        this.$limit.html(limit);
        this.$size.html(size);

    },


    _save: function ($input) {
        var self = this;
        this.options.validate().then(function() {
            var value = $input.val();

            if (value) {

                self.state.limit = value;
                self.trigger('pager_changed', _.clone(self.state));
            }
        }).always(function() {
            // Render the pager's new state (removes the input)
            self._render();
        });
    },


    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    _onEdit: function (event) {
        event.stopPropagation();
        if (!this.disabled) {
            this._edit();
        }
    },

});

return GanttPager;

});
