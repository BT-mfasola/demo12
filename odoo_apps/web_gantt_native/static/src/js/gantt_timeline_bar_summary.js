odoo.define('web_gantt_native.Summary', function (require) {
"use strict";


var Widget = require('web.Widget');



var GanttTimeLineSummary = Widget.extend({
    template: "GanttTimeLine.summary",

    init: function(parent) {
        this._super.apply(this, arguments);
    },


    start: function(){

        var parentg =  this.getParent();

        var data_widgets =  parentg.gantt_timeline_data_widget;

        _.each(data_widgets, function(widget) {

            if (!widget.record.is_group) {

                var row_id = widget.record.id;

                // if (widget.record.subtask_count > 0 || widget.record.isParent) {

                if (widget.record.isParent) {

                    var start_time = false;
                    if (widget.record.summary_date_start){
                        start_time = widget.record.summary_date_start.getTime();
                    }

                    var stop_time = false;
                    if (widget.record.summary_date_end){
                        stop_time = widget.record.summary_date_end.getTime();
                    }

                    if (start_time && stop_time){

                        var start_pxscale = Math.round((start_time-parentg.firstDayScale) / parentg.pxScaleUTC);
                        var stop_pxscale = Math.round((stop_time-parentg.firstDayScale) / parentg.pxScaleUTC);

                        var bar_left = start_pxscale;
                        var bar_width = stop_pxscale-start_pxscale;

                        var summary_bar = $('<div class="task-gantt-bar-summary"></div>');

                        summary_bar.addClass("task-gantt-bar-summary-"+row_id);

                        summary_bar.css({"left": bar_left + "px"});
                        summary_bar.css({"width": bar_width + "px"});

                        var row_data = _.find(parentg.gantt_timeline_data_widget, function (o) { return o.record_id === row_id; })
                        var rowdata = row_data.el;

                        var bar_summary_start = $('<div class="task-gantt-summary task-gantt-summary-start"></div>');
                        var bar_summary_end = $('<div class="task-gantt-summary task-gantt-summary-end"></div>');

                        summary_bar.append(bar_summary_start);
                        summary_bar.append(bar_summary_end);

                        var bar_summary_width = $('<div class="task-gantt-summary-width"></div>');
                        bar_summary_width.css({"width": bar_width + "px"});

                        summary_bar.append(bar_summary_width);

                        $(rowdata).append(summary_bar);

                    }



                }


            }

            return true;
        })


    }


});

return {
    SummaryWidget: GanttTimeLineSummary
}

});