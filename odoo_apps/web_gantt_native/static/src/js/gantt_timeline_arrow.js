odoo.define('web_gantt_native.TimeLineArrow', function (require) {
"use strict";

var Widget = require('web.Widget');
var ArrowDraw = require('web_gantt_native.TimeLineArrowDraw');




var GanttTimeLineArrow = Widget.extend({
    template: "GanttTimeLine.arrow",

    init: function(parent, timeline_width) {
        // this._super(parent);
        this._super.apply(this, arguments);
        this.canvas_width = timeline_width;
    },



    start: function(){


        var parentw =  this.getParent();

        var data_widget =  parentw.gantt_timeline_data_widget;

        var new_data_widget = _.filter(data_widget,

            function(widget){

            if (widget.items_sorted && widget.record.fold){
                return false
            }
            return widget

        });



         new_data_widget = _.map(new_data_widget, function(widget , key) {

            var task_start_pxscale = 0;
            var task_stop_pxscale = 0;

            if (!widget.record.is_group) {
                var task_start_time = widget.record.task_start.getTime();
                var task_stop_time = widget.record.task_stop.getTime();

                task_start_pxscale = Math.round((task_start_time - parentw.firstDayScale) / parentw.pxScaleUTC);
                task_stop_pxscale = Math.round((task_stop_time - parentw.firstDayScale) / parentw.pxScaleUTC);
            }


            return {

                 key: key,
                 y: 30*key,
                 record_id: widget.record.id,
                 group: widget.record.is_group,
                 task_start_pxscale: task_start_pxscale,
                 task_stop_pxscale: task_stop_pxscale,
                 fold: widget.record.fold,
                 critical_path: widget.record.critical_path,
                 cp_shows: widget.record.cp_shows,
                 p_loop: widget.record.p_loop,

             }

         });

        new_data_widget = _.compact(new_data_widget);
        var canvas_height = 30*new_data_widget.length;
        var canvas_width = this.canvas_width;

        //var myCanvas = $('<canvas id="canvas" width="'+canvas_width+'" height="'+canvas_height+'" class="task-gantt-timeline-arrow-canvas"></canvas>');

        var GanttDrawLink = $('<div id="gantt_draw_timeline_link" class="task-gantt-timeline-arrow-canvas"></div>');
        GanttDrawLink.css({'width': canvas_width + "px"});
        GanttDrawLink.css({'height': canvas_height + "px"});

        var self = this;
        var el = self.$el;




        var predecessors = parentw.Predecessor;

        _.each(predecessors, function(predecessor , key){


            var to = predecessor.task_id[0];
            var from = predecessor.parent_task_id[0];

            var from_obj = _.findWhere(new_data_widget, {record_id: from});
            var to_obj = _.findWhere(new_data_widget, {record_id: to});

            if (from_obj == null || to_obj == null){

                return false
            }

            var GanttTimelineLink = $('<div class="gantt_timeline_link" id="gantt_timeline_link-'+predecessor["id"]+'" ></div>');


            _.each(ArrowDraw.drawLink(from_obj, to_obj, predecessor.type), function(line){
                    GanttTimelineLink.append(line);
            });

            GanttDrawLink.append(GanttTimelineLink);
            el.append(GanttDrawLink);

        })

    },


});

return GanttTimeLineArrow;

});