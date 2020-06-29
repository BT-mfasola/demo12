odoo.define('web_gantt_native.ToolField', function (require) {
"use strict";


    var time = require('web.time');
    var field_utils = require('web.field_utils');

    // var formats = require('web.formats');




    function getFields(parent, group_bys) {

        // this.fields_keys = _.keys(this.fields_view.fields);

        var gantt_fields_0 = [
            "id",
            "display_name"
        ];

        var gantt_fields_1 = [

            "name",
            "date_start",
            "date_stop",
            "progress",
            "user_id",

            "task_time",

            "project_id",
            "date_deadline",
            "progress",

            "on_gantt",

            "date_done",
            "state",

            "subtask_project_id",
            "load_data_id",

            "parent_id",

            "default_seq",

            "sorting_seq",
            "sorting_level",
            "subtask_count",

            "is_milestone",
            "schedule_mode",
            "constrain_type",
            "constrain_date",
            "duration",
            "plan_duration",

            "summary_date_start",
            "summary_date_end",

            "plan_action",

            "color_gantt_set",
            "color_gantt",
            "duration_scale",

            "fold",

            "critical_path",
            "cp_shows",
            "cp_detail",

            "p_loop",

            "doc_count"


        ];

        var model_fields_dict = [];
        var model_fields = _.compact(_.map(gantt_fields_1, function(key) {

            var key_field = parent.fields_view.arch.attrs[key] || '';
            model_fields_dict[key] = key_field;
            return key_field
        }));


        model_fields = _.uniq(model_fields.concat(group_bys, gantt_fields_0));


        return {
            model_fields : model_fields,
            gantt_fields : gantt_fields_1,
            model_fields_dict : model_fields_dict
        }

    }



    function flatRows (row_datas, ItemsSorted) {

        var rows_to_gantt = [];
        var self = this;
        //var sefl = undefined;
        self.ItemsSorted = ItemsSorted;

        //recursive tree to flat task.
        var generate_flat_gantt = function(value, parent_value) {

            var zt_id = false;
            var zt_pId = "root_";


            if (parent_value && !self.ItemsSorted){

                zt_pId = parent_value.zt_id
            }


            if (value.is_group) {

                value.zt_id =zt_pId+value.group_info[0]+"_"+value.group_info[1];

                rows_to_gantt.push({

                    id: value.id,
                    is_group: value.is_group,
                    group_id: value.group_info,
                    // level: value.level,
                    value_name: value.task_name,
                    group_field: value.group_field,
                    task_count: value.task_count,
                    fold: value.fold,

                    zt_pId: zt_pId,
                    zt_id:  value.zt_id,
                });

            }
            else {

                //Some browser crash
                var assign_to = undefined;
                try {
                     assign_to = value.assign_to[1];
                } catch (err) {}


                if (self.ItemsSorted){

                    zt_pId = parent_value.zt_id;

                    if ( value.parent_id ){

                        zt_pId = value.parent_id[0]

                    }

                }


                // zt_pId = 0;
                // if ( value.parent_id ){
                //
                //     zt_pId = value.parent_id[0]
                // }


                rows_to_gantt.push({

                    zt_id:  value.id,
                    zt_pId : zt_pId,

                    is_group: value.is_group,
                    // group_field: value.group_field,

                    id: value.id,
                    group_id: value.group_info,
                    // level: value.level,
                    value_name: value.task_name,

                    assign_to: assign_to,

                    task_start: value.task_start,
                    task_stop: value.task_stop,tree_seq: value.tree_seq,

                    default_seq: value.default_seq,

                    sorting_level : value.sorting_level,
                    sorting_seq: value.sorting_seq,

                    project_id : value.project_id,

                    date_deadline: value.date_deadline,
                    progress: value.progress,

                    is_milestone: value.is_milestone,
                    on_gantt: value.on_gantt,

                    schedule_mode: value.schedule_mode,
                    constrain_type: value.constrain_type,
                    constrain_date: value.constrain_date,
                    duration: value.duration,
                    plan_duration: value.plan_duration,


                    plan_action: value.plan_action,

                    color_gantt:  value.color_gantt,
                    color_gantt_set: value.color_gantt_set,

                    duration_scale: value.duration_scale,

                    summary_date_start: value.summary_date_start,
                    summary_date_end: value.summary_date_end,

                    subtask_project_id: value.subtask_project_id,
                    load_data_id: value.load_data_id,

                    parent_id: value.parent_id,
                    subtask_count: value.subtask_count,

                    date_done: value.date_done,
                    state: value.state,

                    fold: value.fold,

                    critical_path: value.critical_path,
                    cp_shows: value.cp_shows,
                    cp_detail: value.cp_detail,

                    p_loop: value.p_loop,
                    doc_count: value.doc_count,

                });

            }

            _.map(value.child_task, function(sub_task) {
                generate_flat_gantt(sub_task, value);
            });
        };


        //Generate Flat Gant to rows_to_gantt
        _.map(row_datas, function(result) {
           return generate_flat_gantt(result);
        });

        return rows_to_gantt;


    }


    function groupRows (tasks, group_bys, self_parent, ItemsSorted) {

        var parent = self_parent;
        var GtimeStopA  = [];
        var GtimeStartA = [];

        var model_fields_dict = parent.model_fields_dict;
        var gantt_attrs = parent.gantt_attrs;
        var second_sort = parent.second_sort;
        var main_group = parent.main_group;

       //prevent more that 1 group by
        //   if (group_bys.length > 0) {
        //       group_bys = [group_bys[0]];
        //   }


        // if there is no group by, simulate it
        if (group_bys.length === 0) {
            group_bys = ["_pseudo_group_by"];
            _.each(tasks, function(el) {
                el._pseudo_group_by = "Plain Gantt View";
            });
            this.fields._pseudo_group_by = {type: "string"};
        }


        //Sort
        var sort_fld = "sequence";


        if (second_sort){

                sort_fld = model_fields_dict["default_seq"];
                if (sort_fld) {
                    tasks = _.sortBy(tasks, function (o) {
                    return o[sort_fld];
                    });
                }
        }


        if (!second_sort){

            if (ItemsSorted){

                sort_fld = model_fields_dict["sorting_seq"];
                if (sort_fld) {
                    tasks = _.sortBy(tasks, function (o) {
                    return o[sort_fld];
                    });
                }

            }

        }


        // get the groups
        var split_groups = function(tasks, group_bys) {

            if (group_bys.length === 0)
                return tasks;
            var sp_groups = [];
            _.each(tasks, function(task) {
                var group_name = task[_.first(group_bys)];
                var group = _.find(sp_groups, function(group) { return _.isEqual(group.name, group_name); });
                if (group === undefined) {
                    group = {name:group_name, tasks: [], __is_group: true};
                   sp_groups.push(group);
                }
                group.tasks.push(task);
            });
            _.each(sp_groups, function(group) {
                group.tasks = split_groups(group.tasks, _.rest(group_bys));
            });
            return sp_groups;
        };

        var groups = split_groups(tasks, group_bys);


        //Sort by sequenses group if detect.
        if (second_sort) {

            var s_field = gantt_attrs["second_seq_field"];
            groups = _.map(groups, function(result) {

                var s_id = result["name"][0];
                var sort_element = _.findWhere(second_sort, {id: s_id});

                if (sort_element) {
                    result["sort_seq"] = sort_element[s_field];
                }else{
                    result["sort_seq"] = -1;
                }

            return result

            });


            groups = _.sortBy(groups, function (o) {
                return o["sort_seq"];
            });

        }

        if (main_group) {

            groups = _.map(groups, function(result) {

                var s_id = result["name"][0];
                var main_element = _.findWhere(main_group, {id: s_id});

                if (main_element) {
                    result["g_data"] = main_element;
                }else{
                    result["g_data"] = false;
                }

            return result

            });
        }




        var assign_to = [];
        // genrate task
        var generate_task_info = function(task, plevel) {

            var level = plevel || 0;
            if (task.__is_group) {
                assign_to = task.user_id;
                var task_infos = _.compact(_.map(task.tasks, function(sub_task) {
                    return generate_task_info(sub_task, level + 1);
                }));
                if (task_infos.length === 0)
                    return;

                //before
                // format_value (value, descriptor, value_if_empty)
                // var group_name = formats.format_value(task.name, parent.fields[group_bys[level]]);


                //last//
                // var field = parent.fields[group_bys[level]];
                // var group_name = field_utils.format[field.type](task.name, field);

                var group_name = undefined;

                var field = parent.fields[group_bys[level]];

                if (field && field.type === "datetime"){
                    var value_format = time.auto_str_to_date(task.name);
                    value_format = moment(value_format);
                    group_name = field_utils.format[field.type](value_format, field, {timezone: false} );
                }
                else{
                    group_name = field_utils.format[field.type](task.name, field);
                }

                // Group by check is fold
                var fold = false;
                if (task.hasOwnProperty("g_data"))
                {
                    fold = task.g_data["fold"]
                }



                var task_count = task_infos.length;
                return {
                    is_group: task.__is_group,
                    group_info: task.name,
                    group_field: group_bys[level],
                    child_task:task_infos,
                    task_name:group_name,
                    level:level,
                    task_count: task_count,
                    fold: fold
                };
            } else {

                var today = new Date();
                var task_name = task.__name;


                assign_to = task[model_fields_dict["user_id"]];

                var mp_level = task[model_fields_dict["mp_level"]];

                var default_seq = task[model_fields_dict["default_seq"]];

                var sorting_level = task[model_fields_dict["sorting_level"]];
                var sorting_seq = task[model_fields_dict["sorting_seq"]];

                var subtask_project_id = task[model_fields_dict["subtask_project_id"]];
                var load_data_id = task[model_fields_dict["load_data_id"]];

                var parent_id = task[model_fields_dict["parent_id"]];
                var subtask_count = task[model_fields_dict["subtask_count"]];


                var task_start = time.auto_str_to_date(task[model_fields_dict["date_start"]]);
                if (!task_start){
                    task_start = today
                }

                var task_stop = time.auto_str_to_date(task[model_fields_dict["date_stop"]]);
                if (!task_stop) {
                    task_stop = task_start
                }

                var date_deadline = time.auto_str_to_date(task[model_fields_dict["date_deadline"]]);
                if (!date_deadline){
                    date_deadline = false
                }

                var progress = task[model_fields_dict["progress"]];
                var is_milestone = task[model_fields_dict["is_milestone"]];
                var on_gantt = task[model_fields_dict["on_gantt"]];

                var project_id = undefined;
                try {
                     project_id = task[model_fields_dict["project_id"]][0];
                } catch (err) {}


                var date_done = time.auto_str_to_date(task[model_fields_dict["date_done"]]);
                if (!date_done){
                    date_done = false
                }


                var constrain_date = time.auto_str_to_date(task[model_fields_dict["constrain_date"]]);
                if (!constrain_date){
                    constrain_date = false
                }

                var duration = task[model_fields_dict["duration"]];
                var plan_duration = task[model_fields_dict["plan_duration"]];


                var plan_action = task[model_fields_dict["plan_action"]];

                var color_gantt_set = task[model_fields_dict["color_gantt_set"]];
                var color_gantt = task[model_fields_dict["color_gantt"]];

                var duration_scale = task[model_fields_dict["duration_scale"]];


                var summary_date_start = time.auto_str_to_date(task[model_fields_dict["summary_date_start"]]);
                if (!summary_date_start){
                    summary_date_start = false
                }

                var summary_date_end = time.auto_str_to_date(task[model_fields_dict["summary_date_end"]]);
                if (!summary_date_end){
                    summary_date_end = false
                }


                var schedule_mode = task[model_fields_dict["schedule_mode"]];
                var constrain_type = task[model_fields_dict["constrain_type"]];

                var state = task[model_fields_dict["state"]];

                var fold = task[model_fields_dict["fold"]];

                var critical_path = task[model_fields_dict["critical_path"]];
                var cp_shows = task[model_fields_dict["cp_shows"]];
                var cp_detail = task[model_fields_dict["cp_detail"]];

                var p_loop = task[model_fields_dict["p_loop"]];
                var doc_count = task[model_fields_dict["doc_count"]];




                try {
                     GtimeStopA.push(task_stop.getTime());
                } catch (err) {}

                try {
                     GtimeStartA.push(task_start.getTime());
                } catch (err) {}

                try {
                     GtimeStopA.push(date_done.getTime());
                     GtimeStartA.push(date_done.getTime());
                } catch (err) {}

                try {
                    GtimeStopA.push(date_deadline.getTime());
                    GtimeStartA.push(date_deadline.getTime());
                } catch (err) {}



                return {
                    id:task.id,
                    task_name: task_name,
                    task_start: task_start,
                    task_stop: task_stop,
                    level:level,
                    assign_to:assign_to,

                    mp_level : mp_level,

                    default_seq : default_seq,

                    sorting_level : sorting_level,
                    sorting_seq : sorting_seq,

                    project_id: project_id,

                    date_deadline: date_deadline,

                    progress: progress,

                    is_milestone: is_milestone,

                    constrain_date: constrain_date,
                    schedule_mode: schedule_mode,
                    constrain_type: constrain_type,

                    duration: duration,
                    plan_duration: plan_duration,


                    plan_action: plan_action,

                    color_gantt_set: color_gantt_set,
                    color_gantt:  color_gantt,

                    duration_scale: duration_scale,

                    summary_date_start: summary_date_start,
                    summary_date_end: summary_date_end,

                    on_gantt: on_gantt,

                    subtask_project_id: subtask_project_id,
                    load_data_id: load_data_id,

                    parent_id: parent_id,
                    subtask_count: subtask_count,

                    date_done: date_done,
                    state: state,

                    fold:fold,

                    critical_path:critical_path,
                    cp_shows: cp_shows,
                    cp_detail: cp_detail,

                    p_loop: p_loop,

                    doc_count: doc_count,

                    is_group: false,
                    // group_field: group_bys[level],


                };
            }
        };

        //generate projects info from groupby
        var projects = _.map(groups, function(result) {
           return generate_task_info(result, 0);
        });


        return {
            projects : projects,
            timestop : GtimeStopA,
            timestart : GtimeStartA

        }


    }

    return {
        flatRows: flatRows,
        groupRows: groupRows,
        getFields : getFields
    }

});