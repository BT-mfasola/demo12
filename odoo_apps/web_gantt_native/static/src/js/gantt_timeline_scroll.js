odoo.define('web_gantt_native.TimeLineScroll', function (require) {
"use strict";


var core = require('web.core');
var Widget = require('web.Widget');
var time = require('web.time');


var _t = core._t;



var GanttTimeLineScroll = Widget.extend({
    template: "TimelineGantt.scroll",

    init: function(parent, timeScale, timeType, first_scale, second_scale) {
        this._super(parent);

        this.timeScale = timeScale;
        this.timeType = timeType;

        this.first_scale = first_scale;
        this.second_scale = second_scale;

        this.TODAY = moment();

       // this.record_id = this.record['id']

    },


    scrollOffset: function (gantt_data_offset){


        var scale_width = $('.timeline-gantt-scroll-scale').width()-50;

        var x1 = $('.task-gantt-timeline').width();
        var x2 = $('.task-gantt-timeline-data').width();
        var  scroll_width = x2 - x1;

        var scale = scroll_width/(scale_width);

        var offset_left = (gantt_data_offset) / scale;

        if (offset_left > scale_width){
            offset_left = scale_width
        }

        if (offset_left <= 0){
            offset_left = 0
        }


        // $(".timeline-gantt-scroll-slider").offset({ left: offset_left  });

        $(".timeline-gantt-scroll-slider").css({left:offset_left});
        //$(".timeline-gantt-scroll-slider").position({ left: offset_left  });


    },


    updateCounterStatus: function ($event_counter, scale_width ,scroll_width) {

        var self = this.__parentedParent;

        // var offset = $event_counter.offset();
        // var offset_left = offset.left;

        var offset_left = $event_counter[0].offsetLeft;

        var scale = scroll_width/(scale_width-50);
        var scale_x = offset_left * scale;


        $('.timeline-gantt-head').animate( { scrollLeft: scale_x }, 0);
        $('.task-gantt-timeline').animate( { scrollLeft: scale_x }, 0);


        //Test
        self.TimeToLeft = scale_x;


    },



    start: function(){

        var self = this;
        var el = self.$el;
        //
        // var gutterOffset = self.__parentedParent.gutterOffsetSession || self.__parentedParent.gutterOffset;
        //
        //
        //
        // var menu = $('.o_sub_menu_content');
        //
        // if (menu){
        //     gutterOffset = gutterOffset + menu[0].offsetWidth;
        // }

        // var div_cell = $('<div class="timeline-gantt-scroll-slider"></div>');

        var div_cell = $('<div class="timeline-gantt-scroll-slider"></div>');

        var scale_width = 0;
        var scroll_width = 0;

        div_cell.draggable({
            axis: "x",
            containment: ".timeline-gantt-scroll-scale",
            scroll: false,

            start: function () {

                var timeline = $('.task-gantt-timeline');

                scale_width = $('.timeline-gantt-scroll-scale').width();
                var x1 = timeline.width();
                var x2 = $('.task-gantt-timeline-data').width();
                scroll_width = x2 - x1;

                var x13 = timeline.scrollLeft();

            },

            drag: function() {

                self.updateCounterStatus( div_cell, scale_width, scroll_width);
            },

        });

        var parent = this.__parentedParent;


        var scroll_start_dt = new Date(0);
        scroll_start_dt.setTime(parent.firstDayDate);

        var scroll_end_dt = new Date(0);
        scroll_end_dt.setTime(parent.lastDayDate);

        var l10n = _t.database.parameters;
        var formatDate = time.strftime_to_moment_format( l10n.date_format + ' ' + l10n.time_format);

        var scroll_start_str = moment(scroll_start_dt).format(formatDate);
        var scroll_end_str = moment(scroll_end_dt).format(formatDate);

        var bar_start = $('<div class="timeline-gantt-scroll-scale-start"></div>');
        var bar_end = $('<div class="timeline-gantt-scroll-scale-end"></div>');

        $('<div class="timeline-gantt-scroll-scale-start-date">'+scroll_start_str+'</div>').appendTo(bar_start);
        $('<div class="timeline-gantt-scroll-scale-end-date">'+scroll_end_str+'</div>').appendTo(bar_end);

        el.append(bar_start);
        el.append(bar_end);

        el.append(div_cell);

    }


});

return GanttTimeLineScroll;

});