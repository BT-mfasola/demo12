odoo.define('web_gantt_native.Docs', function (require) {
"use strict";


var Widget = require('web.Widget');



var GanttTimeLineDocs = Widget.extend({
    template: "GanttTimeLine.docs",

    init: function(parent) {
        this._super.apply(this, arguments);
    },


    start: function(){

        var parentg =  this.getParent();

        var data_widgets =  parentg.gantt_timeline_data_widget;

        _.each(data_widgets, function(widget) {

            if (!widget.record.is_group) {
                
                var el = undefined;
                var find_el = undefined;
                var doc_el = $('<i class="fa fa-paperclip" aria-hidden="false"></i>');
                var doc_bar = undefined;

                var doc_count = widget.record.doc_count;

                if (doc_count && doc_count.length){

                    if (_.has(widget.bar_widget, "done_slider") && widget.bar_widget.done_slider) {

                        el = widget.bar_widget.done_slider[0];
                        find_el = $(el).find(".task-gantt-done-info");


                        doc_bar = $('<div class="task-gantt-docs task-gantt-docs-slider">');
                        doc_bar.append(doc_el);

                        if (find_el && find_el.length){
                            $(find_el).append(doc_bar);
                        }else{
                            $(el).append(doc_bar);

                        }

                    } else if (_.has(widget.bar_widget, "deadline_bar") && widget.bar_widget.deadline_bar) {

                        el = widget.bar_widget.deadline_bar[0];
                        var width = parseInt($(el).css('width'));

                        doc_bar = $('<div class="task-gantt-docs task-gantt-docs-slider">');
                        doc_bar.append(doc_el);

                        doc_bar.css({"left": width+10 + "px" });
                        doc_bar.css({"position": "absolute" });
                        $(el).append(doc_bar);

                    }
                    else {

                        doc_bar = $('<div class="task-gantt-docs task-gantt-docs-bar">');
                        doc_bar.append(doc_el);

                        el = widget.$el;
                        find_el = $(el).find(".task-gantt-bar-plan-info-end");
                        $(find_el).before(doc_bar);
                    }

                }

                // var row_id = widget.record.id;
                // var rowdata = widget.$el;
                //
                //  //console.log(widget.$el)
                //
                // if (_.has(widget.bar_widget, "done_slider") && widget.bar_widget.done_slider) {
                //
                //     var el = widget.bar_widget.done_slider[0];
                //
                //
                //     var fel = $(el).find(".task-gantt-done-info");
                //     var _bar = $('<div class="task-gantt-docs task-gantt-docs-slider"></div>');
                //     var doc_bar = $('<i class="fa fa-paperclip" aria-hidden="false"></i>');
                //     _bar.append(doc_bar);
                //
                //     if (fel.length){
                //          $(fel).append(_bar);
                //     }else{
                //         $(el).append(_bar);
                //
                //     }
                //
                // } else if (_.has(widget.bar_widget, "deadline_bar") && widget.bar_widget.deadline_bar) {
                //
                //     var d_el = widget.bar_widget.deadline_bar[0];
                //
                //     var width = parseInt($(d_el).css('width'));
                //
                //     var d_bar = $('<div class="task-gantt-docs task-gantt-docs-slider"></div>');
                //     //
                //     d_bar.css({"left": width+10 + "px" });
                //     d_bar.css({"position": "absolute" });
                //
                //
                //     var d_doc_bar = $('<i class="fa fa-paperclip" aria-hidden="false"></i>');
                //     d_bar.append(d_doc_bar);
                //
                //     $(d_el).append(d_bar);
                //
                //
                //
                // }
                // else{
                //
                //     var row_el = widget.$el;
                //
                //     var p_el = $(row_el).find(".task-gantt-bar-plan-info-end"); //.task-gantt-bar-plan-info-end //task-gantt-bar-plan
                //
                //     var p_bar = $('<div class="task-gantt-docs task-gantt-docs-bar"></div>');
                //
                //     var p_doc_bar = $('<i class="fa fa-paperclip" aria-hidden="false"></i>');
                //     p_bar.append(p_doc_bar);
                //
                //     // p_el.before(p_bar);
                //
                //
                //
                //     var domain = [
                //         ['res_model', '=', "project.task"],
                //         ['res_id', '=',  widget.record_id],
                //         ['type', 'in', ['binary', 'url']]
                //     ];
                //     var fields = ['name', 'url', 'type',
                //         'create_uid', 'create_date', 'write_uid', 'write_date'];
                //
                //     parentg._rpc({
                //         model: 'ir.attachment',
                //         method: 'search_read',
                //         context: parentg.state.contexts,
                //         domain: domain,
                //         fields: fields,
                //     }).then(function (result) {
                //         if (result.length){
                //             p_el.before(p_bar);
                //         }
                //
                // });
                //
                //
                // }



                    // <i class="fa fa-paperclip" aria-hidden="true"></i>

                // if (widget.record.subtask_count > 0) {



                    // var start_time = false;
                    // if (widget.record.summary_date_start){
                    //     start_time = widget.record.summary_date_start.getTime();
                    // }
                    //
                    // var stop_time = false;
                    // if (widget.record.summary_date_end){
                    //     stop_time = widget.record.summary_date_end.getTime();
                    // }
                    //
                    // var start_pxscale = Math.round((start_time-parentg.firstDayScale) / parentg.pxScaleUTC);
                    // var stop_pxscale = Math.round((stop_time-parentg.firstDayScale) / parentg.pxScaleUTC);
                    //
                    // var bar_left = start_pxscale;
                    // var bar_width = stop_pxscale-start_pxscale;
                    //
                    // var summary_bar = $('<div class="task-gantt-bar-summary"></div>');
                    //
                    // summary_bar.addClass("task-gantt-bar-summary-"+row_id);
                    //
                    // summary_bar.css({"left": bar_left + "px"});
                    // summary_bar.css({"width": bar_width + "px"});
                    //
                    // var row_data = _.find(parentg.gantt_timeline_data_widget, function (o) { return o.record_id === row_id; })
                    // var rowdata = row_data.el;
                    //
                    // var bar_summary_start = $('<div class="task-gantt-summary task-gantt-summary-start"></div>');
                    // var bar_summary_end = $('<div class="task-gantt-summary task-gantt-summary-end"></div>');
                    //
                    // summary_bar.append(bar_summary_start);
                    // summary_bar.append(bar_summary_end);
                    //
                    // var bar_summary_width = $('<div class="task-gantt-summary-width"></div>');
                    // bar_summary_width.css({"width": bar_width + "px"});
                    //
                    // summary_bar.append(bar_summary_width);
                    //
                    // $(rowdata).append(summary_bar);

                // }


            }

            return true;
        })


    }


});

return {
    DocsWidget: GanttTimeLineDocs
}

});