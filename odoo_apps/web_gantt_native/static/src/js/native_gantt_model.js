odoo.define('web_gantt_native.NativeGanttModel', function (require) {
"use strict";

var AbstractModel = require('web.AbstractModel');
var GanttToolField = require('web_gantt_native.ToolField');
var GanttTimeLineGhost = require('web_gantt_native.Ghost');
var GanttTimeLineFirst = require('web_gantt_native.BarFirst');
var framework = require('web.framework');



return AbstractModel.extend({

    init: function () {
        this._super.apply(this, arguments);
        this.gantt = null;

    },

    get: function () {
        return _.extend({}, this.gantt);
    },

    load: function (params) {
        this.modelName = params.modelName;
        this.fields_view  = params.fieldsView;
        //this.params = params;
        // this.fieldNames = params.fieldNames;
        // this.fieldsInfo = params.fieldsInfo;
        this.gantt = {
            modelName : params.modelName,
            group_bys : params.groupedBy,
            domains : params.domain || [],
            contexts :  params.context || {},
            fields_view : params.fieldsView,
            fields : params.fields,
            pager : [],
            orderedBy : params.orderedBy,

        }

        return this._do_load();

    },

        //---1---//
    _do_load: function () {

        var domains = this.gantt.domains;
        var contexts = this.gantt.contexts;
        var group_bys = this.gantt.group_bys;

        var self = this;

        self.main_group_id_name = self.fields_view.arch.attrs.main_group_id_name;
        self.action_menu = self.fields_view.arch.attrs.action_menu;

        // Sort allow only if Group by project and domain search by project.
        // Project get from XML = main_group_id_name = "project_id"

        self.ItemsSorted = false;
        if (group_bys.length === 1){

            if (group_bys[0] === self.main_group_id_name){
                 self.ItemsSorted = true;
            }
            if (domains.length > 0){
                if (domains[0][0] !== self.main_group_id_name){
                 self.ItemsSorted = false;
                }
            }

            if (domains.length > 1){
                self.ItemsSorted = false;
            }
        }

        if (self.fields_view.arch.attrs.no_group_sort_mode){
            self.ItemsSorted = false;
        }

        // Tree View only if group by main_group_id_name
        self.TreeView = false;

        if (group_bys.length === 1) {

            if (group_bys[0] === self.main_group_id_name || group_bys[-1] === self.main_group_id_name) {
                self.TreeView = true;
            }
        }

        if (group_bys.length > 1 ) {

            if (group_bys[group_bys.length-1] === self.main_group_id_name) {
                self.TreeView = true;
            }
        }




        // self.last_domains = domains;
        // self.last_contexts = contexts;
        // self.last_group_bys = group_bys;
        // self.date_start = null;
        // self.date_stop = null;

        var n_group_bys = [];

        // select the group by - we can select group by from attribute where XML if not determinate dafault group
        // for model

        if (this.fields_view.arch.attrs.default_group_by) {
           n_group_bys = this.fields_view.arch.attrs.default_group_by.split(',');
        }

        if (group_bys.length) {
            n_group_bys = group_bys;
        }



        var getFields = GanttToolField.getFields(self, n_group_bys);
        self.model_fields = getFields["model_fields"];
        self.model_fields_dict = getFields["model_fields_dict"];

        var fields = self.model_fields;
        // fields.push('display_name');

        // this.fields_view.arch.attrs.default_group_by
        var export_wizard = false;

        if (self.fields_view.arch.attrs.hasOwnProperty('export_wizard')){
            export_wizard = self.fields_view.arch.attrs.export_wizard
        }



        //Pager
        var limit_view = 0;
        if (self.fields_view.arch.attrs.hasOwnProperty('limit_view')){
            limit_view = parseInt(self.fields_view.arch.attrs.limit_view)
        }

        if(self.gantt.pager.limit){
            limit_view = self.gantt.pager.limit
        }


        //Load Level
        var load_group_id_name = self.fields_view.arch.attrs.load_group_id_name;
        self.LoadMode = false;
        if (group_bys.length === 1) {

            if (group_bys[0] === load_group_id_name || group_bys[-1] === load_group_id_name) {
                self.LoadMode = true;
            }
        }

        if (group_bys.length > 1 ) {

            if (group_bys[group_bys.length-1] === load_group_id_name) {
                self.LoadMode = true;
            }
        }


        self.gantt.data = {
            ItemsSorted : self.ItemsSorted,
            ExportWizard : export_wizard,
            TreeView : self.TreeView,
            Main_Group_Id_Name : self.main_group_id_name,
            Action_Menu : self.action_menu,
            model_fields : fields,
            model_fields_dict : self.model_fields_dict,
            model_fields_view : self.fields_view,
            LoadMode : self.LoadMode,

        };

        return this._rpc({
                model: this.modelName,
                method: 'search_read',
                context: this.gantt.contexts,
                domain: this.gantt.domains,
                fields: _.uniq(fields),
                limit: limit_view,
                orderBy: this.gantt.orderedBy
            })
            .then(function (data) {
                self.gantt.pager.limit = limit_view;
                return self.on_data_loaded_count(data, n_group_bys);
            });

    },








    on_data_loaded_count: function(tasks, group_bys) {
        var self = this;

        return this._rpc({
                model: this.modelName,
                method: 'search_count',
                args: [this.gantt.domains],
                context: this.gantt.contexts,
            })
            .then(function (result) {
                self.gantt.pager.records = result;

                if (self.gantt.pager.records > self.gantt.pager.limit){
                    self.gantt.data.ItemsSorted = false
                }

                return self.on_data_loaded_dummy(tasks, group_bys);
            });


    },



    on_data_loaded_dummy: function(tasks, group_bys) {
        var self = this;
        return self.on_data_loaded_info(tasks, group_bys);
    },

    //Fist Entry poin load predecessor after. get atributes from XML
    on_data_loaded_info: function(tasks, group_bys) {
        var self = this;
        var ids = _.pluck(tasks, "id");

        var info_model = self.fields_view.arch.attrs.info_model;
        var info_task_id = "task_id";

        if (info_model) {

            return this._rpc({
                    model: info_model,
                    method: 'search_read',
                    context: this.gantt.contexts,
                    domain: [[info_task_id, 'in', _.uniq(ids)]],
                    fields: _.uniq([info_task_id,"start", "end", "left_up","left_down","right_up","right_down","show"])
                })
                .then(function (result) {

                    if (result){
                        result = _.map(result, function(info) {

                        if (info.task_id){
                            info.task_id = info.task_id[0];
                            return info;
                        }
                        });
                    }



                    self.gantt.data.task_info = result;
                    return self.on_data_loaded_predecessor(tasks, group_bys);
                });
            }
        else{
            return self.on_data_loaded_predecessor(tasks, group_bys);
        }

    },





    //Fist Entry poin load predecessor after. get atributes from XML
    on_data_loaded_predecessor: function(tasks, group_bys) {
        var self = this;
        var ids = _.pluck(tasks, "id");

        var predecessor_model = self.fields_view.arch.attrs.predecessor_model;
        var predecessor_task_id = self.fields_view.arch.attrs.predecessor_task_id;
        var predecessor_parent_task_id = self.fields_view.arch.attrs.predecessor_parent_task_id;
        var predecessor_type = self.fields_view.arch.attrs.predecessor_type;

        if (predecessor_model) {

            return this._rpc({
                    model: predecessor_model,
                    method: 'search_read',
                    context: this.gantt.contexts,
                    domain: [[predecessor_task_id, 'in', _.uniq(ids)]],
                    fields: _.uniq([predecessor_task_id, predecessor_parent_task_id, predecessor_type])
                })
                .then(function (result) {
                    self.gantt.data.predecessor = result;
                    return self.on_data_loaded_ghost(tasks, group_bys);
                });
            }
        else{
            return self.on_data_loaded_ghost(tasks, group_bys);
        }

    },


    on_data_loaded_ghost: function(tasks, group_bys) {
        var self = this;
        var ids = _.pluck(tasks, "id");

        var ghost_id = self.fields_view.arch.attrs.ghost_id;
        var ghost_model = self.fields_view.arch.attrs.ghost_model;
        var ghost_name = self.fields_view.arch.attrs.ghost_name;
        var ghost_date_start = self.fields_view.arch.attrs.ghost_date_start;
        var ghost_date_end = self.fields_view.arch.attrs.ghost_date_end;
        var ghost_durations = self.fields_view.arch.attrs.ghost_durations;

        if (ghost_model) {
            return this._rpc({
                    model: ghost_model,
                    method: 'search_read',
                    context: this.gantt.contexts,
                    domain: [[ghost_id, 'in', _.uniq(ids)]],
                    fields: _.uniq([ghost_id ,ghost_name, ghost_date_start, ghost_date_end, ghost_durations])
                })
                .then(function (result) {
                    self.gantt.data.Ghost = result;
                    self.gantt.data.Ghost_Data = GanttTimeLineGhost.get_data_ghosts(self);

                    return self.on_data_loaded_barfirst(tasks, group_bys);
                });

        }
        else{
            return self.on_data_loaded_barfirst(tasks, group_bys);
        }

    },







    on_data_loaded_barfirst: function(tasks, group_bys) {

        var self = this;

        if (self.ItemsSorted) {

            var barfirst_field = "project_id";

            var barfirst_field_ids = _.pluck(tasks, "project_id");

            var ids = _.pluck(barfirst_field_ids, "0");

            var barfirst_model = "project.project";
            var barfirst_name = "name";
            var barfirst_date_start = "date_start";
            var barfirst_date_end = "date_end";


            return this._rpc({
                    model: barfirst_model,
                    method: 'search_read',
                    context: this.gantt.contexts,
                    domain: [['id', 'in', _.uniq(ids)]],
                    fields: _.uniq(['id', barfirst_name, barfirst_date_start, barfirst_date_end])
                })
                .then(function (result) {
                    self.gantt.data.BarFirst = result;
                    self.gantt.data.BarFirst_Data = GanttTimeLineFirst.get_data_barfirst(self);

                    return self.on_data_loaded_name_get(tasks, group_bys);
                });

        }
        else{
            return self.on_data_loaded_name_get(tasks, group_bys);
        }

    },


        //Get name get from model form name field
    on_data_loaded_name_get: function(tasks, group_bys) {
        var self = this;
        var ids = _.pluck(tasks, "id");

        return this._rpc({
                model: this.modelName,
                method: 'name_get',
                args: [ids],
                context: this.gantt.contexts,
            })
            .then(function (names) {
                var ntasks = _.map(tasks, function(task) {
                        return _.extend({__name: _.detect(names, function(name) { return name[0] == task.id; })[1]}, task);
                });

                // return self.gantt_render(ntasks, group_bys);
                self.gantt.data.ntasks = ntasks;
                self.gantt.data.group_bys = group_bys;
                return self.get_second_sort_data(ntasks, group_bys);

            });


    },


    get_second_sort_data: function(tasks, group_bys) {

            var self = this;
            self.gantt.data["second_sort"] = undefined;
            var gantt_attrs = self.fields_view.arch.attrs;

            var link_field = gantt_attrs["second_seq_link_field"];

            if (group_bys.length === 1 && group_bys[0] === link_field) {

                var ids = [];
                _.map(tasks, function (result) {

                    if (result[link_field]) {
                        ids.push(result[link_field][0]);
                    }
                });

                var s_model =  gantt_attrs["second_seq_model"];
                var s_field =  gantt_attrs["second_seq_field"];

                return this._rpc({
                    model: s_model,
                    method: 'search_read',
                    context: this.gantt.contexts,
                    domain: [['id', 'in', _.uniq(ids)]],
                    fields: _.uniq(['id',s_field])
                })
                .then(function (result) {
                    self.gantt.data["second_sort"] = result;
                    return self.get_minmax_step(tasks, group_bys);
                });
            }
            else {
                return self.get_main_group_data(tasks, group_bys);
            }


    },


    get_main_group_data: function(tasks, group_bys) {

            var self = this;
            self.gantt.data["main_group"] = undefined;
            var gantt_attrs = self.fields_view.arch.attrs;

            var main_id = gantt_attrs["main_group_id_name"];
            var s_model =  gantt_attrs["main_group_model"];
            var s_field = ["id", "name","fold"];

            if (group_bys.length === 1 && group_bys[0] === main_id && s_model) {

                var ids = [];
                _.map(tasks, function (result) {

                    if (result[main_id]) {
                        ids.push(result[main_id][0]);
                    }
                });

                return this._rpc({
                    model: s_model,
                    method: 'search_read',
                    context: this.gantt.contexts,
                    domain: [['id', 'in', _.uniq(ids)]],
                    fields: _.uniq(s_field)
                })
                .then(function (result) {
                    self.gantt.data["main_group"] = result;
                    return self.get_minmax_step(tasks, group_bys);
                });
            }
            else{
                return self.get_minmax_step(tasks, group_bys);
            }



    },


    get_minmax_step: function(tasks, group_bys) {
        var self = this;

        var parent = {};

        parent.fields = self.gantt.fields;

        parent.model_fields_dict = self.gantt.data.model_fields_dict;
        parent.gantt_attrs = self.gantt.data.model_fields_view.arch.attrs;
        parent.second_sort = self.gantt.data.second_sort;
        parent.main_group = self.gantt.data.main_group;

        var groupRows = GanttToolField.groupRows(tasks, group_bys, parent, self.ItemsSorted);

        self.gantt.data["rows_to_gantt"] =  GanttToolField.flatRows(groupRows["projects"], self.ItemsSorted);

        // self.gantt.data["projects"] = groupRows["projects"];
        //Get Max Min date for data
        var GtimeStartA = groupRows["timestart"];
        var GtimeStopA = groupRows["timestop"];


        self.gantt.data["GtimeStart"] = Math.min.apply(null, GtimeStartA); // MAX date in date range
        self.gantt.data["GtimeStop"] = Math.max.apply(null, GtimeStopA); // Min date in date range

        GtimeStopA = [];
        GtimeStartA = [];

        return self.get_res_task_load(tasks, group_bys);


    },

    get_res_task_load: function(tasks, group_bys) {
        var self = this;

        var gantt_attrs = self.fields_view.arch.attrs;

        var load_model = gantt_attrs["load_bar_model"];
        var load_id = gantt_attrs["load_id"];
        var load_id_from = gantt_attrs["load_id_from"];
        var load_ids_from = gantt_attrs["load_ids_from"];

        var ids = false;
        if (load_ids_from === "id"){

            ids = _.pluck(tasks, "id");

        }
        else if(load_ids_from !== "" && load_ids_from !== undefined){

            var gp_load =  _.map(tasks , function (group_value) {
                if (group_value[load_ids_from] !== false && group_value[load_ids_from] !== undefined && group_value[load_ids_from].length > 0 ){
                    return group_value[load_ids_from][0]
                }

                // if (group_value[load_id] !== false && group_value[load_id].length == 1 ){
                //     return group_value[load_id]
                // }

            });

            ids = _.compact(gp_load);

        }


        if (ids){
                   var _fields = [load_id, load_id_from, 'data_from', 'data_to', 'data_aggr', 'duration'];
                   var _domain = [[load_id_from, 'in', _.uniq(ids)]];

                    return this._rpc({
                            model: load_model,
                            method: 'search_read',
                            context: this.gantt.contexts,
                            domain: _domain,
                            fields: _fields
                        })
                        .then(function (result) {
                           self.gantt.data["Task_Load_Data"] = result;
                           return self.get_res_load(tasks, group_bys);
                        });

       }
       else{
          return true
       }


        // var ghost_id = self.fields_view.arch.attrs.ghost_id;
        // var ghost_model = self.fields_view.arch.attrs.ghost_model;
        // var ghost_name = self.fields_view.arch.attrs.ghost_name;
        // var ghost_date_start = self.fields_view.arch.attrs.ghost_date_start;
        // var ghost_date_end = self.fields_view.arch.attrs.ghost_date_end;
        // var ghost_durations = self.fields_view.arch.attrs.ghost_durations;
        //
        // if (ghost_model) {
        //     return this._rpc({
        //             model: ghost_model,
        //             method: 'search_read',
        //             context: this.gantt.contexts,
        //             domain: [[ghost_id, 'in', _.uniq(ids)]],
        //             fields: _.uniq([ghost_id ,ghost_name, ghost_date_start, ghost_date_end, ghost_durations])
        //         })
        //         .then(function (result) {
        //             self.gantt.data.Ghost = result;
        //             self.gantt.data.Ghost_Data = GanttTimeLineGhost.get_data_ghosts(self);
        //
        //             return self.get_res_load(tasks, group_bys);
        //         });
        //
        // }
        // else{
        //     return self.get_res_load(tasks, group_bys);
        // }

    },



    get_res_load: function(tasks, group_bys) {

        var self = this;


        if (self.LoadMode) {

            // var _contexts = self.gantt.contexts;

            // var _ctx = {
            //         'group_by': 'data_aggr',
            //         'lang': _contexts.lang,
            //         'tz': _contexts.tz,
            //         'uid': _contexts.uid
            // };
            var gantt_attrs = self.fields_view.arch.attrs;
            var load_model = gantt_attrs["load_bar_model"];
            var _ctx = self.gantt.contexts;

            var m_GtimeStart = moment(self.gantt.data["GtimeStart"]).format("YYYY-MM-DD");
            var m_GtimeStop = moment(self.gantt.data["GtimeStop"]).format("YYYY-MM-DD");
            // var _domain = [['data_aggr', '>=', m_GtimeStart], ['data_aggr', '<=', m_GtimeStop]];

            var data_load_group = _.where(self.gantt.data["rows_to_gantt"], {is_group: true});

            var gp_load =  _.map(data_load_group , function (group_value) {
                if (group_value.group_id !== false && group_value.group_id.length > 0 ){
                    return group_value.group_id[0]
                }
            });

            var gp_domain_ids = _.compact(gp_load);
            var _domain = [['resource_id', 'in', _.uniq(gp_domain_ids)],['data_aggr', '>=', m_GtimeStart], ['data_aggr', '<=', m_GtimeStop]];
            var _fields = ['task_id', 'data_from', 'data_to', 'user_id', 'data_aggr', 'duration', 'resource_id'];

            // project.task.detail.plan
            // project.task.detail.plan.res.link
            return this._rpc({
                model: load_model,
                method: 'search_read',
                context: _ctx,
                domain: _domain,
                fields: _fields
            })

            .then(function (result) {
                self.gantt.data["Load_Data"] = result;
                return true
            });

        }
        else{
            return true
        }


    },

        // var m_GtimeStart = moment(self.GtimeStart).format("YYYY-MM-DD");
        // var m_GtimeStop = moment(self.GtimeStop).format("YYYY-MM-DD");
        //
        // var _contexts = self.state.contexts;
        //
        // // var _domain = [['data_aggr', '>=', m_GtimeStartA], ['data_aggr', '<=', m_GtimeStopA], ['iser_id', 'in', _.uniq(ids)]];
        // // _.uniq([user_id ,ghost_name, ghost_date_start, ghost_date_end, ghost_durations])
        //
        // var _domain = [['data_aggr', '>=', m_GtimeStart], ['data_aggr', '<=', m_GtimeStop]];
        // var _fields = ['task_id', 'data_from', 'data_to', 'durations', 'user_id', 'data_aggr'];
        //
        //
        // if (self.LoadMode) {
        //         this._rpc({
        //
        //             model: "project.task.detail.plan",
        //             method: 'search_read',
        //             context: _contexts,
        //             domain: _domain,
        //             fields: _fields
        //         })
        //
        //         .then(function (result) {
        //             self.state.data.Dloads = result;
        //         });
        //
        // }

            // var tasks = self.state.data.ntasks;
        // var group_bys = self.state.data.group_bys;
        //
        //
        // var groupRows = GanttToolField.groupRows(tasks, group_bys, parent);

        // //Get all tasks with group
        // self.projects = groupRows["projects"];
        //
        // //Get Max Min date for data
        // self.GtimeStopA = self.GtimeStopA.concat(groupRows["timestop"]);
        // self.GtimeStartA = self.GtimeStartA.concat(groupRows["timestart"]);
        //
        // //Calc Min - Max
        // self.GtimeStart = Math.min.apply(null, self.GtimeStartA); // MAX date in date range
        // self.GtimeStop = Math.max.apply(null, self.GtimeStopA); // Min date in date range
        //
        // //Clean
        // self.GtimeStartA = [];
        // self.GtimeStopA = [];







    reload: function (handle, params) {
        if (params.domain) {
            this.gantt.domains = params.domain;
        }
        if (params.context) {
            this.gantt.contexts = params.context;
        }
        if (params.groupBy) {
            this.gantt.group_bys = params.groupBy;
        }
        return this._do_load();
    },

});

});
