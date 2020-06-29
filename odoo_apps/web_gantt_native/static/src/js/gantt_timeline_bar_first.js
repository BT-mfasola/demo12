odoo.define('web_gantt_native.BarFirst', function (require) {
"use strict";


var Widget = require('web.Widget');
var time = require('web.time');




var GanttTimeLineFirst = Widget.extend({
    template: "GanttTimeLine.first",

    init: function(parent) {
        this._super.apply(this, arguments);
    },


    start: function(){

        var parentg =  this.getParent();

        var data_widgets =  parentg.gantt_timeline_data_widget;




        _.each(data_widgets, function(widget) {

            if (parentg.ItemsSorted && widget.record.is_group) {

                var row_id = widget.record.group_id[0];

                // var barfirst_datas =  parentg.BarFirst_Data;
                var link_first_result = _.where(parentg.BarFirst_Data, {data_row_id: row_id});

                if (link_first_result.length > 0){

                    var link_first_data = link_first_result[0];

                    var start_time = false;
                    if (link_first_data.date_start){
                        start_time = link_first_data.date_start.getTime();
                    }

                    var stop_time = false;
                    if (link_first_data.date_end){
                        stop_time = link_first_data.date_end.getTime();
                    }


                    if (start_time && stop_time){

                        var start_pxscale = Math.round((start_time-parentg.firstDayScale) / parentg.pxScaleUTC);
                        var stop_pxscale = Math.round((stop_time-parentg.firstDayScale) / parentg.pxScaleUTC);

                        var bar_left = start_pxscale;
                        var bar_width = stop_pxscale-start_pxscale;

                        var first_bar = $('<div class="task-gantt-bar-first"></div>');
                        first_bar.addClass("task-gantt-bar-first-"+row_id);

                        first_bar.css({"left": bar_left + "px"});
                        first_bar.css({"width": bar_width + "px"});

                        // var rowdata = '#task-gantt-timeline-group-row-'+row_id;
                        var rowdata = widget.$el;

                        var first_bar_start = $('<div class="task-gantt-first task-gantt-first-start"></div>');
                        var first_bar_end = $('<div class="task-gantt-first task-gantt-first-end"></div>');

                        var height_m = parseInt(widget.record.task_count);

                        if (height_m){
                            first_bar_start.css({"height": (1+height_m)*30 + "px"});
                            first_bar_end.css({"height": (1+height_m)*30 + "px"});
                        }



                        first_bar.append(first_bar_start);
                        first_bar.append(first_bar_end);



                        $(rowdata).append(first_bar);

                    }


                }



                // if (widget.record.subtask_count > 0) {
                //
                //     var start_time = false;
                //     if (widget.record.summary_date_start){
                //         start_time = widget.record.summary_date_start.getTime();
                //     }
                //
                //     var stop_time = false;
                //     if (widget.record.summary_date_end){
                //         stop_time = widget.record.summary_date_end.getTime();
                //     }
                //
                //     var start_pxscale = Math.round((start_time-parentg.firstDayScale) / parentg.pxScaleUTC);
                //     var stop_pxscale = Math.round((stop_time-parentg.firstDayScale) / parentg.pxScaleUTC);
                //
                //     var bar_left = start_pxscale;
                //     var bar_width = stop_pxscale-start_pxscale;
                //
                //     var summary_bar = $('<div class="task-gantt-bar-summary"></div>');
                //
                //     summary_bar.addClass("task-gantt-bar-summary-"+row_id);
                //
                //     summary_bar.css({"left": bar_left + "px"});
                //     summary_bar.css({"width": bar_width + "px"});
                //
                //     var rowdata = '#task-gantt-timeline-row-'+row_id;
                //
                //
                //     var bar_summary_start = $('<div class="task-gantt-summary task-gantt-summary-start"></div>');
                //     var bar_summary_end = $('<div class="task-gantt-summary task-gantt-summary-end"></div>');
                //
                //     summary_bar.append(bar_summary_start);
                //     summary_bar.append(bar_summary_end);
                //
                //     var bar_summary_width = $('<div class="task-gantt-summary-width"></div>');
                //     bar_summary_width.css({"width": bar_width + "px"});
                //
                //     summary_bar.append(bar_summary_width);
                //
                //     $(rowdata).append(summary_bar);
                //
                // }


            }

            return true;
        })


    }


});

function get_data_barfirst (parentg) {

        // var ghosts = parentg.Ghost;
        // var ghost_id = parentg.fields_view.arch.attrs.ghost_id;
        // var ghost_ids_name = parentg.fields_view.arch.attrs.ghost_name;
        // var ghost_ids_date_start = parentg.fields_view.arch.attrs.ghost_date_start;
        // var ghost_ids_date_end = parentg.fields_view.arch.attrs.ghost_date_end;
        // var ghost_ids_durations = parentg.fields_view.arch.attrs.ghost_durations;

        // var barfirsts = parentg.BarFirst;
    var barfirsts = parentg.gantt.data.BarFirst;

        var barfirst_id = "id";
        var barfirst_name = "name";
        var barfirst_date_start = "date_start";
        var barfirst_date_end = "date_end";

        var data_barfirst = _.map(barfirsts, function(barfirst) {

                var data_row_id = barfirst[barfirst_id];

                var date_start = barfirst[barfirst_date_start];
                if (date_start){
                    date_start = time.auto_str_to_date(date_start);
                }

                var date_end = barfirst[barfirst_date_end];
                if (date_end){
                    date_end = time.auto_str_to_date(date_end);
                }


                return {
                    data_row_id: data_row_id,
                    name : barfirst[barfirst_name],
                    date_start : date_start,
                    date_end : date_end,

            }
        });

        // try {
        //     var data_min = _.min(data_ghosts, function (ghost) {
        //         return ghost.date_start;
        //     });
        // }
        // catch (err) {}
        //
        //
        // try {
        //     var data_max = _.max(data_ghosts, function (ghost) {
        //         return ghost.date_end;
        //     });
        // }
        // catch (err) {}
        //
        //
        //
        // try {
        //     var start_time = data_min["date_start"].getTime();
        //     parentg.GtimeStopA = parentg.GtimeStopA.concat(start_time);
        // } catch (err) {}
        //
        // try {
        //     var stop_time = data_max["date_end"].getTime();
        //     parentg.GtimeStartA = parentg.GtimeStartA.concat(stop_time);
        // } catch (err) {}


        return data_barfirst;


}


return {
    get_data_barfirst: get_data_barfirst,
    BarFirstWidget: GanttTimeLineFirst
}

});