odoo.define('web_gantt_native.ItemAction', function (require) {
"use strict";

var Widget = require('web.Widget');


var GanttListAction = Widget.extend({
    template: "GanttList.action",

    custom_events: {
        'focus_gantt_line' : 'focus_gantt_line'
    },

    init: function(parent, options) {

        this._super(parent);
        this.parent = parent;
        this.items_sorted = options.items_sorted;
        this.export_wizard = options.export_wizard;
        this.main_group_id_name = options.main_group_id_name;
        this.action_menu = options.action_menu;
        this.tree_view = options.tree_view;
        this.$zTree = parent.widget_ztree.$zTree;


    },

    start: function() {

        var self = this;
        var $zTree = this.$zTree;

        var nodes = $zTree.getNodes();

         _.each(nodes, function (node) {

             var childNodes = $zTree.transformToArray(node);

             _.each(childNodes, function (child) {

                var item_action = $('<div class="item-action"/>');


                var id = child["zt_id"];

                if (id !== undefined) {
                    item_action.prop('id', "item-action-" + id + "");
                    item_action.attr('data-id', id);
                }


                item_action.append('<span class="action-focus"><i class="fa fa-crosshairs fa-1x"></i></span>');


                if (child["plan_action"]) {
                    item_action.append('<span class="action-plan"><i class="fa fa-exclamation"></i></span>');
                }


                var fold = child["fold"];
                // if (self.tree_view) {
                    if (fold) {
                        item_action.css({'display': 'none'});
                    }

                // }

                self.$el.append(item_action);

             });

         });

    },



    renderElement: function () {
        this._super();

        // this.$el.data('record', this);
        this.$el.on('click', this.proxy('on_global_click'));

    },



    focus_gantt_line: function (event) {

        var self = this.parent.__parentedParent;
        var $zTree = this.$zTree;

        var record = $zTree.getNodeByParam('zt_id', event.data["id"]);
        $zTree.selectNode(record);

        if (!record.is_group){
            var toscale = Math.round((record.task_start.getTime()-self.renderer.firstDayScale) / self.renderer.pxScaleUTC);
            self.renderer.TimeToLeft = toscale;

            var new_toscale = toscale-500;
            if (new_toscale < 0){
                new_toscale = 0;
            }


            $('.timeline-gantt-head').animate( { scrollLeft: new_toscale }, 1000);
            $('.task-gantt-timeline').animate( { scrollLeft: new_toscale }, 1000);
            self.renderer.gantt_timeline_scroll_widget.scrollOffset(new_toscale);

        }

    },


    on_global_click: function (ev) {

        if (!ev.isTrigger) { //human detect

            var id = $(ev.target).parent().parent().data("id");

            //Focus Task
            if ($(ev.target).hasClass("fa-crosshairs")) {
               this.trigger_up('focus_gantt_line', {id: id});
            }

        }
    },



});

return GanttListAction;

});