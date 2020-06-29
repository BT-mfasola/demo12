odoo.define('web_gantt_native.ItemInfo', function (require) {
"use strict";


var core = require('web.core');

var dialogs = require('web.view_dialogs');

var Widget = require('web.Widget');
var Model = require('web.AbstractModel');

var framework = require('web.framework');

var time = require('web.time');


var _lt = core._lt;
var _t = core._t;





var GanttListInfo = Widget.extend({
    template: "GanttList.info",

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

        var items_start = $('<div class="item-list"/>');
        var items_stop = $('<div class="item-list"/>');
        var l10n = _t.database.parameters;
        var formatDate = time.strftime_to_moment_format( l10n.date_format + ' ' + l10n.time_format);
        var formatDate_only = time.strftime_to_moment_format( l10n.date_format);
        var formatTime_only = time.strftime_to_moment_format( l10n.time_format);


        var items_duration = $('<div class="item-info"/>');

        _.each(nodes, function (node) {
            var childNodes = $zTree.transformToArray(node);

            _.each(childNodes, function (child) {


                var item_info = $('<div class="item-info"/>');
                var id = child["id"];

                if (id !== undefined) {
                    item_info.prop('id', "item-info-" + id);
                    item_info.prop('data-id', id);
                    item_info.prop('allowRowHover', true);
                }

                var fold = child["fold"];
                // if (self.tree_view) {
                    if (fold) {
                        item_info.css({'display': 'none'});
                    }
                // }


                //Duration
                var item_duration = item_info.clone();
                var duration = child['duration'];
                var duration_units = undefined;

                if (duration){

                    var duration_scale = child['duration_scale'];

                    if (duration_scale) {

                        duration_units =  duration_scale.split(",");

                    }
                    // Array of strings to define which units are used to display the duration (if needed).
                    // Can be one, or a combination of any, of the following:
                    // ['y', 'mo', 'w', 'd', 'h', 'm', 's', 'ms']
                    //
                    // humanizeDuration(3600000, { units: ['h'] })       // '1 hour'
                    // humanizeDuration(3600000, { units: ['m'] })       // '60 minutes'
                    // humanizeDuration(3600000, { units: ['d', 'h'] })  // '1 hour'

                    var duration_humanize = humanizeDuration(duration*1000, { round: true });

                    if (duration_units){
                        duration_humanize = humanizeDuration(duration*1000,{ units: duration_units, round: true });
                    }


                    if (child['isParent']){
                        item_duration.append('<div class="task-gantt-item-info task-gantt-items-subtask" style="float: right;">'+duration_humanize+'</div>');
                    }
                    else{
                        item_duration.append('<div class="task-gantt-item-info" style="float: right;">'+duration_humanize+'</div>');
                    }

                }

                items_duration.append(item_duration);




                if (self.parent.list_show){

                    var formatDate_type = formatDate;
                    if (self.parent.list_type === "date"){
                        formatDate_type = formatDate_only
                    }else if (self.parent.list_type === "time"){

                         formatDate_type = formatTime_only
                    }


                    //Start
                    var item_start = item_info.clone();
                    var task_start = child['task_start'];

                    if (task_start){
                        var start_date_html = moment(task_start).format(formatDate_type);

                        if (child['isParent']){
                            item_start.append('<div class="task-gantt-item-info task-gantt-items-subtask" style="float: right;">'+start_date_html+'</div>');
                        }
                        else{
                            item_start.append('<div class="task-gantt-item-info" style="float: right;">'+start_date_html+'</div>');
                        }
                    }


                    //Stop
                    var item_stop = item_info.clone();
                    var task_stop = child['task_stop'];

                    if (task_stop){
                        var stop_date_html = moment(task_stop).format(formatDate_type);

                        if (child['isParent']){
                            item_stop.append('<div class="task-gantt-item-info task-gantt-items-subtask" style="float: right;">'+stop_date_html+'</div>');
                        }
                        else{
                            item_stop.append('<div class="task-gantt-item-info" style="float: right;">'+stop_date_html+'</div>');
                        }
                    }


                items_start.append(item_start);
                items_stop.append(item_stop);



                }


            })


        });

        self.$el.append(items_duration);
        self.$el.append(items_start);
        self.$el.append(items_stop);

    },


});

return GanttListInfo;

});