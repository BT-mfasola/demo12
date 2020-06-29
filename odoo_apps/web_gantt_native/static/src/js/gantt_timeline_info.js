odoo.define('web_gantt_native.Info', function (require) {
"use strict";

var Widget = require('web.Widget');

var GanttTimeLineInfo = Widget.extend({
    // template: "GanttTimeLine.info",

    init: function(parent) {
        this._super.apply(this, arguments);
    },

    gen_element: function(e_text, e_pos){


            var e_class = 'task-gantt-bar-plan-info-' + e_pos;
            var bar_e = $('<div class='+e_class+'/>');
            var bar_e_text = $('<a/>');
            bar_e_text.text(e_text);
            bar_e.append(bar_e_text);

            return bar_e


    },


    start: function(){

        var self = this;
        var el = self.$el;

        var parentg =  this.getParent();

        var data_widgets =  parentg.gantt_timeline_data_widget;

        var task_info = parentg.Task_Info;

        _.each(data_widgets, function(widget) {

            if (!widget.record.is_group) {


                    var el = widget.$el;

                    var row_id = widget.record.id;
                    var cp_detail = widget.record.cp_detail;
                    var rowdata = '.task-gantt-bar-plan-' + row_id;
                    var row_el = el.find(rowdata);


                    var info_data = {};

                    var task_info_to = _.where(task_info, {task_id: row_id});

                    _.each(task_info_to, function(info){

                        if (info["show"] || cp_detail) {

                            _.each(info, function (info, key) {

                                if (info_data[key]) {

                                    if (info) {
                                        info_data[key] = info_data[key] + ', ' + info
                                    }
                                } else {
                                    info_data[key] = info

                                }

                            });
                        }


                    });


                    //Record for text

                    var info_list = {};

                    info_list["start"] = info_data["start"] || '';
                    info_list["left-up"] = info_data["left_up"] || '';
                    info_list["left-down"] = info_data["left_down"] || '';
                    info_list["end"] = info_data["end"] || '';
                    info_list["right-up"] = info_data["right_up"] || '';
                    info_list["right-down"] = info_data["right_down"] || '';

                    _.each(info_list, function( val, key ) {

                        row_el.append(self.gen_element(val, key));

                    })

            }

            return true;
        })


    }


});

return {
    InfoWidget: GanttTimeLineInfo
}

});