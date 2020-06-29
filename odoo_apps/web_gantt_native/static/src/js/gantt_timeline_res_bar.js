

odoo.define('web_gantt_native.ResBar', function (require) {
"use strict";

var Widget = require('web.Widget');
var time = require('web.time');


//     function secondsToTime(secs)
// {
//
//
//     var pad = function(num, size) { return ('000' + num).slice(size * -1); },
//     time = parseFloat(secs).toFixed(3),
//     hours = Math.floor(time / 60 / 60),
//     minutes = Math.floor(time / 60) % 60,
//     seconds = Math.floor(time - minutes * 60),
//     milliseconds = time.slice(-3);
//
//         var obj = {
//         "h": pad(hours, 2),
//         "m": pad(minutes, 2),
//         "s":  pad(seconds, 2)
//     };
//     return obj;
//
// }



var GanttTimeLineResBar = Widget.extend({
    template: "GanttTimeLine.resbar",

    init: function(parent) {
        this._super.apply(this, arguments);
    },


    start: function(){

        var parentg =  this.getParent();

        var data_widgets =  parentg.gantt_timeline_data_widget;
        var task_load_data = parentg.Task_Load_Data;



        if (task_load_data){

            var gantt_attrs = parentg.arch.attrs;
            var load_id = gantt_attrs["load_id"];
            var load_id_from = gantt_attrs["load_id_from"];
            var load_bar_record_row  =  gantt_attrs["load_bar_record_row"];
            var load_data_id = gantt_attrs["load_data_id"];

            // var subtask_project_id  =  gantt_attrs["subtask_project_id"];

            // S1
             var data_load_s1 = _.map(task_load_data, function (res_data) {

                    var active_id = res_data[load_id] ? res_data[load_id][0] : -1;
                    var active_id_from = res_data[load_id_from] ? res_data[load_id_from][0] : -1;

                    return {
                        data_from: res_data["data_from"],
                        data_to : res_data["data_to"],
                        active_id : active_id,
                        active_id_from: active_id_from
                }
             });

            var data_load_s2 = _.groupBy(data_load_s1, 'active_id' );

            _.each(data_widgets, function(widget) {

                    if (!widget.record.is_group) {

                        var row_id = widget.record["id"];
                        if (load_bar_record_row){
                             row_id = widget.record[load_bar_record_row];
                        }


                        var color_gantt = widget.record["color_gantt"];


                        var data_load = data_load_s2[row_id];


                        // if (data_load) {
                        // gantt_bar.css({"background": color_gantt.replace(/[^,]+(?=\))/, '0.2')});
                        // }
                        var rowdata = widget.$el;
                        var active_id_from_data = widget.record["load_data_id"] ? widget.record["load_data_id"][0] : -1;

                        if (load_data_id === "id") {
                            active_id_from_data = widget.record["id"];
                        }

                        _.each(data_load, function(link_load){

                                if (active_id_from_data === link_load.active_id_from){


                                        var dt_start = time.auto_str_to_date(link_load.data_from);
                                        var time_start = dt_start.getTime();

                                        var dt_to = time.auto_str_to_date(link_load.data_to);
                                        var time_to = dt_to.getTime();


                                        var load_start_pxscale = Math.round((time_start-parentg.firstDayScale) / parentg.pxScaleUTC);
                                        var load_stop_pxscale = Math.round((time_to-parentg.firstDayScale) / parentg.pxScaleUTC);

                                        var load_bar_left = load_start_pxscale;
                                        var load_bar_width = load_stop_pxscale-load_start_pxscale;

                                        var load_bar_x = $('<div class="task-gantt-bar-load-task"></div>');

                                        load_bar_x.css({"left": load_bar_left + "px"});
                                        load_bar_x.css({"width": load_bar_width + "px"});

                                        var gantt_bar = $(rowdata).find(".task-gantt-bar-plan");

                                        gantt_bar.css({"background": color_gantt.replace(/[^,]+(?=\))/, '0.4')});
                                        load_bar_x.css({"background": color_gantt});

                                        $(rowdata).append(load_bar_x);

                                 }



                        });


                    }






            });



                // var data_load = self.task_load_data[id];
                //
                // if (data_load) {
                //     gantt_bar.css({"background": color_gantt.replace(/[^,]+(?=\))/, '0.2')});
                // }
                //
                //  _.each(data_load, function(link_load){
                //
                //
                //         var dt_start = time.auto_str_to_date(link_load.data_from);
                //         var time_start = dt_start.getTime();
                //
                //         var dt_to = time.auto_str_to_date(link_load.data_to);
                //         var time_to = dt_to.getTime();
                //
                //
                //         var load_start_pxscale = Math.round((time_start-self.parent.firstDayScale) / self.parent.pxScaleUTC);
                //         var load_stop_pxscale = Math.round((time_to-self.parent.firstDayScale) / self.parent.pxScaleUTC);
                //
                //         var load_bar_left = load_start_pxscale;
                //         var load_bar_width = load_stop_pxscale-load_start_pxscale;
                //
                //         var load_bar_x = $('<div class="task-gantt-bar-load-task"></div>');
                //
                //         load_bar_x.css({"left": load_bar_left + "px"});
                //         load_bar_x.css({"width": load_bar_width + "px"});
                //
                //         load_bar_x.css({"background": color_gantt});
                //
                //         self.$el.append(load_bar_x);
                //
                //
                // });


            //  _.each(data_widgets, function(widget) {
            //
            //     if (widget.record.is_group) {
            //
            //         var row_id = widget.record["group_id"] ? widget.record["group_id"][0] : -1;
            //         var data_load_w = _.where(data_load_s3, {user_id: row_id});
            //
            //         // Get Load Data
            //         if (typeof data_load_w !== 'undefined' && data_load_w.length > 0 ){
            //
            //             var data_group = data_load_w[0]["data_group"];
            //
            //             var gp_load =  _.map(data_group , function (data_load_value, key) {
            //
            //
            //                 var duration =  _.reduce(data_load_value,
            //                 function (memoizer, value) {
            //                     return memoizer + value.duration;
            //                 }, 0);
            //
            //                 var r_obj = [];
            //                 r_obj["date"] = key;
            //                 r_obj["duration"] = duration;
            //
            //                 return r_obj
            //             });
            //         }
            //
            //         var rowdata = widget.$el;
            //
            //         // Render Load Data
            //         _.each(gp_load, function(link_load){
            //
            //             var date_point = time.auto_str_to_date(link_load.date);
            //             var start_time = date_point.getTime();
            //
            //             var left_point = Math.round((start_time-parentg.firstDayScale) / parentg.pxScaleUTC);
            //
            //             var load_bar_x = $('<div class="task-gantt-bar-load"></div>');
            //
            //             // var duration_seconds = humanizeDuration(parseInt(link_load.duration, 10)*1000, {round: true });
            //
            //             var duration_ = secondsToTime(link_load.duration);
            //
            //             var load_duration = $('<div class="task-gantt-load-duration">'+duration_.h+'</div>');
            //             load_bar_x.append(load_duration);
            //
            //
            //             if (duration_.m !== "00") {
            //                 var load_duration_m = $('<div class="task-gantt-load-duration-m">' + duration_.m + '</div>');
            //                 load_bar_x.append(load_duration_m);
            //             }
            //
            //
            //             load_bar_x.css({"left": left_point + "px"});
            //             load_bar_x.css({"width": parentg.timeScale + "px"});
            //
            //             $(rowdata).append(load_bar_x);
            //         });
            //
            //
            //     }
            //
            // });



        }

    }

});

return {
    ResBarWidget: GanttTimeLineResBar


}

});









