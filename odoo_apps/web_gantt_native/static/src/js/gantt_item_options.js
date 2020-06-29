odoo.define('web_gantt_native.ItemOptions', function (require) {
"use strict";

var Widget = require('web.Widget');
var Model = require('web.AbstractModel');
var framework = require('web.framework');

var dialogs = require('web.view_dialogs');
var core = require('web.core');
var _t = core._t;
var _lt = core._lt;

var time = require('web.time');

var GanttListOptionsItem = Widget.extend({
    template: "GanttList.options",

    custom_events: {
        'item_order' : 'order_action',
        'item_list' : 'list_action',
        'item_export' : 'export_action',

    },

    init: function(parent) {
        this.parent = parent;
        this._super.apply(this, arguments);
        this.$zTree = parent.widget_ztree.$zTree;
    },

    start: function () {
        // var _widget =  this.parent.gantt_timeline_header_widget;
        // var el_widget = _widget.$el;

        if (this.parent.ItemsSorted){

            // var div_manual = $('<div class="text-left task-gantt-item-sort-manual"/>');
            // div_manual.text("Manual Sort");
            // this.$el.append(div_manual);

        } else if (this.parent.state.orderedBy && this.parent.state.orderedBy.length){

        // Sort Options
            var div_ = $('<div class="text-left gantt-list-options-item"/>');
            // div_.text(this.parent.fields[this.parent.state.orderedBy[0].name].string);
            var _text = "Sort - " + this.parent.fields[this.parent.state.orderedBy[0].name].string;

            var  div_typer = $('<div class="fa fa-sort-amount-desc gantt-list-options-item-sort" aria-hidden="false" title="desc '+ _text +'"></div>');


            if (this.parent.state.orderedBy[0].asc){
                 div_typer = $('<div class="fa fa-sort-amount-asc gantt-list-options-item-sort" aria-hidden="false" title="asc '+ _text +'"></div>');
            }

            div_.append(div_typer);
            this.$el.append(div_);

        }

        // Show List

        var item_list = $('<div class="text-left gantt-list-options-item"/>');
        var list_div = $('<div class="fa fa-list gantt-list-options-item-check gantt-list-options-item-check-inactive" aria-hidden="false" title="Show List"></div>');
        if (this.parent.list_show){
            list_div = $('<div class="fa fa-list gantt-list-options-item-check gantt-list-options-item-check-active" aria-hidden="false" title="Show List"></div>');
        }

        item_list.append(list_div);
        this.$el.append(item_list);


        //Export to file

        var export_to_file = $('<div class="text-left gantt-list-options-item"/>');
        var export_to_file_div = $('<div class="fa fa-file-text-o gantt-list-options-export-to-file" aria-hidden="false" title="Export to File"></div>');

        export_to_file.append(export_to_file_div);
        this.$el.append(export_to_file);


    },


    renderElement: function () {
        this._super();

        this.$el.data('parent', this);
        this.$el.on('click', this.proxy('on_global_click'));

    },

    on_global_click: function (ev) {

        if (!ev.isTrigger) { //human detect

            if ($(ev.target).hasClass("gantt-list-options-item-sort" )) {

                this.trigger_up('item_order', {
                    orderedBy: this.parent.state.orderedBy,
                });
            }

            else if ($(ev.target).hasClass("gantt-list-options-item-check" )) {
                this.trigger_up('item_list', {});
            }

            else if ($(ev.target).hasClass("gantt-list-options-export-to-file" ))
            {
                this.trigger_up('item_export', {});
            }




        }
    },

    order_action: function(event) {

        var self = this.__parentedParent;
        var parent = this.parent;
        var orderedBy = event.data.orderedBy;


        if (orderedBy.length){

            if (orderedBy[0].asc){
                orderedBy[0].asc = false
            }else{

                orderedBy[0].asc = true
            }

            self.trigger_up('gantt_refresh_after_change' )

        }
    },

    list_action: function(event) {

        var self = this.__parentedParent;
        var parent = this.parent;
        // var list_show = event.data.list_show;


        if (parent.list_show) {
            parent.list_show = false
        }else{
            parent.list_show = true
        }


        self.trigger_up('gantt_fast_refresh_after_change' )


    },

    export_action: function(event) {

        var self = this.__parentedParent;
        var parent = this.parent;


        var zTree = this.$zTree;
        //
        var nodes = zTree.getNodes();


        var rows_to_gantt = [];

                _.each(nodes, function (node) {

                    var childNodes = zTree.transformToArray(node);

                    _.each(childNodes, function (row) {



                        var date_start = undefined;
                        if (typeof row.task_start !== "undefined" ){
                            date_start = time.auto_date_to_str(row.task_start, "datetime")
                        }

                        var date_end = undefined;
                        if (typeof row.task_stop !== "undefined" ){
                            date_end = time.auto_date_to_str(row.task_stop, "datetime")
                        }


                        var subtask_count = 0;
                        if (row.isParent){
                                subtask_count = 1
                            }

                        var for_update = {
                                "id": row.id,
                                "name": row.value_name,
                                "duration": row.duration,
                                "date_start": date_start,
                                "date_end": date_end,
                                "sorting_level": row.level,
                                "subtask_count": subtask_count,
                                "wbs": undefined,
                                "stuff": "",
                                "separate": row.is_group

                        };
                        rows_to_gantt.push(for_update)






                        // var root_node_select =  "root_" + treeNode.subtask_project_id[0];
                        //
                        // if (root_node_select  === node.zt_id){
                        //
                        //     if (child.isParent){
                        //         child.fontCss = {'font-weight':'bold'}
                        //     }else{
                        //         child.fontCss = {}
                        //     }
                        //
                        //
                        //
                        //     var for_update = {
                        //         "id": child.id,
                        //         "plan_action": child.plan_action,
                        //         "is_group": child.is_group,
                        //         "sorting_level": child.level
                        //     };
                        //     rows_to_gantt.push(for_update)
                        // }

                    });

                });



        // var rows_to_gantt = [];
        //
        // _.each(self.rows_to_gantt, function (row) {
        //
        //     var date_start = undefined;
        //     if (typeof row.task_start !== "undefined" ){
        //         date_start = time.auto_date_to_str(row.task_start, "datetime")
        //     }
        //
        //     var date_end = undefined;
        //     if (typeof row.task_stop !== "undefined" ){
        //         date_end = time.auto_date_to_str(row.task_stop, "datetime")
        //     }
        //
        //
        //     var for_update = {
        //             "id": row.id,
        //             "name": row.value_name,
        //             "duration": row.duration,
        //             "date_start": date_start,
        //             "date_end": date_end,
        //             "sorting_level": row.sorting_level,
        //             "subtask_count": row.subtask_count,
        //             "wbs": undefined,
        //             "stuff": "",
        //             "separate": row.is_group
        //
        //     };
        //     rows_to_gantt.push(for_update)
        // });





                //         var rows_to_gantt = [];
                //
                // _.each(nodes, function (node) {
                //
                //     var childNodes = zTree.transformToArray(node);
                //
                //     _.each(childNodes, function (child) {
                //
                //         var root_node_select =  "root_" + treeNode.subtask_project_id[0];
                //
                //         if (root_node_select  === node.zt_id){
                //
                //             if (child.isParent){
                //                 child.fontCss = {'font-weight':'bold'}
                //             }else{
                //                 child.fontCss = {}
                //             }
                //
                //
                //
                //             var for_update = {
                //                 "id": child.id,
                //                 "plan_action": child.plan_action,
                //                 "is_group": child.is_group,
                //                 "sorting_level": child.level
                //             };
                //             rows_to_gantt.push(for_update)
                //         }
                //
                //     });
                //
                // });




        var context = this.__parentedParent.state.contexts;


            // var rows_to_gantt = self.rows_to_gantt;
        // var time_type = self.timeType;


        // var group_id = event.data["group_id"];

        // context['default_group_id'] = group_id || false;
        // context['rows_to_gantt'] = rows_to_gantt || false;
        context['time_type'] = self.timeType || false;
        context['default_screen'] = true;
        context['default_data_json'] = JSON.stringify(rows_to_gantt);


        var res_model = "project.native.report"; //event.data["exoprt_wizard"];

        var pop = new dialogs.FormViewDialog(this.__parentedParent, {
            res_model: res_model,
            res_id: false,
            context: context,
            title: _t("PDF Report for Screen"),
        }).open();


                   //         id: treeNode.id,
                   // is_group: is_group,
                   // group_id: group_id,
                   // group_field: group_field,
                   // exoprt_wizard: treeNode.widget.export_wizard,



        // var list_show = event.data.list_show;

        // if (parent.list_show) {
        //     parent.list_show = false
        // }else{
        //     parent.list_show = true
        // }
        //
        //
        // self.trigger_up('gantt_fast_refresh_after_change' )


    }





});



return {

    OptionsItem : GanttListOptionsItem

};


});