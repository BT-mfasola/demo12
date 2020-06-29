odoo.define('web_gantt_native.Ghost', function (require) {
"use strict";

var Widget = require('web.Widget');
var time = require('web.time');



function get_data_ghosts (parentg) {

        var ghosts = parentg.gantt.data.Ghost;
        var ghost_id = parentg.fields_view.arch.attrs.ghost_id;
        var ghost_ids_name = parentg.fields_view.arch.attrs.ghost_name;
        var ghost_ids_date_start = parentg.fields_view.arch.attrs.ghost_date_start;
        var ghost_ids_date_end = parentg.fields_view.arch.attrs.ghost_date_end;
        var ghost_ids_durations = parentg.fields_view.arch.attrs.ghost_durations;

        var data_ghosts = _.map(ghosts, function(ghost) {

                var data_row_id = ghost[ghost_id][0];

                var durations = ghost[ghost_ids_durations];

                var date_start = time.auto_str_to_date(ghost[ghost_ids_date_start]);
                if (!date_start){
                    return
                }
                var date_end = time.auto_str_to_date(ghost[ghost_ids_date_end]);
                if (!date_end){

                    if (durations){
                        date_end = moment(date_start).add(durations*60, 'minutes')._d;
                    }
                    else{
                        return
                    }
                }

                return {
                    data_row_id: data_row_id,
                    name : ghost[ghost_ids_name],
                    date_start : date_start,
                    date_end : date_end,
                    durations : ghost[ghost_ids_durations]
            }
        });

        try {
            var data_min = _.min(data_ghosts, function (ghost) {
                return ghost.date_start;
            });
        }
        catch (err) {}


        try {
            var data_max = _.max(data_ghosts, function (ghost) {
                return ghost.date_end;
            });
        }
        catch (err) {}



        try {
            var start_time = data_min["date_start"].getTime();
            parentg.GtimeStopA = parentg.GtimeStopA.concat(start_time);
        } catch (err) {}

        try {
            var stop_time = data_max["date_end"].getTime();
            parentg.GtimeStartA = parentg.GtimeStartA.concat(stop_time);
        } catch (err) {}


        return data_ghosts;



}


var GanttTimeLineGhost = Widget.extend({
    template: "GanttTimeLine.ghost",

    init: function(parent) {
        this._super.apply(this, arguments);
    },


    start: function(){

        var parentg =  this.getParent();


        var data_widgets =  parentg.gantt_timeline_data_widget;

        var data_ghosts = parentg.Ghost_Data;

        _.each(data_widgets, function(widget) {

            if (!widget.record.is_group) {

                var row_id = widget.record.id;

                var link_ghosts = _.where(data_ghosts, {data_row_id: row_id});

                if (link_ghosts.length > 0){

                    var data_min = _.min(link_ghosts, function(ghost){ return ghost.date_start; });
                    var data_max = _.max(link_ghosts, function(ghost){ return ghost.date_end; });

                    var start_time = data_min["date_start"].getTime();
                    var stop_time = data_max["date_end"].getTime();

                    var start_pxscale = Math.round((start_time-parentg.firstDayScale) / parentg.pxScaleUTC);
                    var stop_pxscale = Math.round((stop_time-parentg.firstDayScale) / parentg.pxScaleUTC);

                    var bar_left = start_pxscale;
                    var bar_width = stop_pxscale-start_pxscale;

                    var ghost_bar = $('<div class="task-gantt-bar-ghosts"></div>');

                    ghost_bar.addClass("task-gantt-bar-ghosts-"+row_id);

                    ghost_bar.css({"left": bar_left + "px"});
                    ghost_bar.css({"width": bar_width + "px"});

                    // var rowdata = '#task-gantt-timeline-row-'+row_id;
                    var rowdata = widget.$el;


                    _.each(link_ghosts, function(link_ghost){

                        var ghost_bar_x = $('<div class="task-gantt-bar-ghost"></div>');
                        var ghost_start_time = link_ghost["date_start"].getTime();
                        var ghost_stop_time = link_ghost["date_end"].getTime();

                        var ghost_start_pxscale = Math.round((ghost_start_time-parentg.firstDayScale) / parentg.pxScaleUTC);
                        var ghost_stop_pxscale = Math.round((ghost_stop_time-parentg.firstDayScale) / parentg.pxScaleUTC);

                        var ghost_bar_left = ghost_start_pxscale;
                        var ghost_bar_width = ghost_stop_pxscale-ghost_start_pxscale;

                        ghost_bar_x.css({"left": ghost_bar_left + "px"});
                        ghost_bar_x.css({"width": ghost_bar_width + "px"});

                        $(rowdata).append(ghost_bar_x);
                    });

                    $(rowdata).append(ghost_bar);


                }

            }

            return true;
        })


    }


});

return {
    get_data_ghosts: get_data_ghosts,
    GhostWidget: GanttTimeLineGhost
}

});