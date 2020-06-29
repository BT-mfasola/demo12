odoo.define('web_gantt_native.ItemzTree', function (require) {
    "use strict";

    var core = require('web.core');
    var _t = core._t;
    var _lt = core._lt;
    var Widget = require('web.Widget');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var framework = require('web.framework');
    var Dialog = require('web.Dialog');
    var dialogs = require('web.view_dialogs');
    var NativeGanttData = require('web_gantt_native.NativeGanttData');

    var ztree_Max = 160;

//                   setting.edit.drag.isMove = true
// Position settings:
// prev  inner  next
// setting.edit.drag.prev = true
// setting.edit.drag.inner = true
// setting.edit.drag.next = true

    var ItemzTree = Widget.extend({
        className: 'zitemtree',
        template: 'GanttList.item.ztree',

        custom_events: {
            'item_plan_action' : 'plan_action',
            'item_export_wizard': 'open_export_wizard',
            'item_record_edit': 'edit_record',
            'item_record_add':  'add_record',

        },

        init: function (parent, data, options) {
            var self = this;
            this._super.apply(this, arguments);
            this.items_sorted = options.items_sorted;
            this.export_wizard = options.export_wizard;
            this.main_group_id_name = options.main_group_id_name;
            this.action_menu = options.action_menu;
            this.tree_view = options.tree_view;

            this.parent = parent;

            this.setting = {

                edit: {
                    enable: this.parent.ItemsSorted,
                    showRemoveBtn: false,
                    showRenameBtn: self.showRenameBtn,
                    drag: {
                        next: true,
                        inner: true,
                        prev: true,
                        isCopy: false
                      }
                },
                view: {

                    selectedMulti: false,
                    fontCss: self.getFont,
                    nameIsHTML: true,
                    showIcon: false,
                    txtSelectedEnable: false,
                    addHoverDom: self.addHoverDom,
                    removeHoverDom: self.removeHoverDom,
                    // addDiyDom: self.addDiyDom
                },
                data: {
                    key: {
                        name: "value_name"
                    },
                    simpleData: {
                        enable: true,
                        idKey: "zt_id",
                        pIdKey: "zt_pId",

                    }
                },
                callback: {
				    beforeDrag: self.beforeDrag,
				    beforeDrop: self.beforeDrop,
                    onDrop: self.onDrop,
                    onClick: self.zTreeOnClick,
                    onCollapse: self.onCollapse,
				    onExpand: self.onExpand,
                    beforeCollapse: self.beforeCollapse,
                    beforeEditName: self.beforeEditName,
                    onRename: self.OnRename,

			    }
            };

            if (data)
                this.records = data;


            // this.ztree_field = data.ztree_field;
            // this.ztree_model = data.ztree_model;
            // this.ztree_parent_key = data.ztree_parent_key;
            // this.ztree_domain = data.ztree_domain;
            // this.ztree_context = data.ztree_context ? data.ztree_context : session.user_context;
            // this.order = data.order;
            // this.ztree_selected_id = Number(data.ztree_selected_id);
            // this.ztree_selected_vals = [];
            // this.ztree_with_sub_node = data.ztree_with_sub_node;
            // this.ztree_index = data.ztree_index;
            // this.ztree_add_show_all = data.ztree_add_show_all;
            // this.ztree_expend_level = data.ztree_expend_level >= 0 ? Number(data.ztree_expend_level) : 3;
            // this.limit = data.limit > 0 ? data.limit : 160;
            // this.ztree_id = 'ztree-' + this.guid();
            // this.ztree_type = data.ztree_type;
        },

        getFont: function (treeId, node) {

            //Task have subtask
             if (node['subtask_count']){
                return {'font-weight':'bold'}
            }else{
                return {}
             }

		},


        showRenameBtn: function (treeId, treeNode) {
			return !treeNode.is_group;

		},
        beforeEditName: function (treeId, treeNode) {

            var check_field = ["name"];
            var self = treeNode.widget;
            var parent = treeNode.widget_parent;

			var _read_only = NativeGanttData.CheckReadOnly(check_field,  parent.fields, treeNode);
			var check_readonly = _.findWhere(_read_only,{readonly: true});

			if (check_readonly){

			    self.trigger_up('warning', {
                    title: _t('Try update'),
                    message: _.str.sprintf(_t("You are trying to edit on a read-only field! : '%s' "),check_readonly["field"])
                });

                return false;
            }
        },


        OnRename: function(event, treeId, treeNode, isCancel) {

            var self = treeNode.widget;

            if (!isCancel){


                var parent = treeNode.widget_parent;
                var r_id = treeNode.id;

                // if (treeNode.is_group && treeNode.group_id){
                //     r_id = treeNode.group_id[0];
                // }

                var data = {};

                data["name"] = treeNode.value_name;

                parent._rpc({
                    model: parent.state.modelName,
                    method: 'write',
                    args: [[r_id], data],
                    context: parent.state.contexts
                })
                .then(function(ev) {

                    self.trigger_up('warning', {
                        title: _t('Item Data Update'),
                        message: _t('Data updated : ') + ev
                    });

                    var match_item = _.find(parent.rows_to_gantt, function(item) { return item.id === treeNode.id });
                    match_item.value_name = treeNode.value_name;

                    if (treeNode.on_gantt){
                        parent.trigger_up('gantt_fast_refresh_after_change');
                    }



                });
            }else{

                self.$zTree.cancelEditName();


            }


            // parent.trigger_up('gantt_fast_refresh_after_change');

        },



		beforeCollapse: function (treeId, treeNode) {

            var collaplse = treeNode.collapse;

            // if (!treeNode.widget.tree_view){
            //     collaplse = false;
            // }

			return (collaplse !== false);
		},


        getChildNodes: function getChildNodes(treeNode) {
            var childNodes = this.$zTree.transformToArray(treeNode);
            var nodes = [];

             _.each(childNodes, function (child) {

                 if (treeNode.zt_id !== child.zt_id) {
                     nodes.push(child)
                 }
             });

            return nodes
        },


        fold_bar: function(node, childs, fold){
            var self = this;

            // var fold_dic = {};

            _.each(childs, function (child) {
                var match_task_id = _.find(self.parent.rows_to_gantt, function(item) { return item.id === child.id });

                match_task_id.fold = fold;
                child.fold = fold;

                // fold_dic[match_task_id.id] = fold;

            });

            self.parent.trigger_up('gantt_fast_refresh_after_change');


            if (node.widget.tree_view){

                var fold_dic = {};

                if (node["id"]) {
                    fold_dic[node["id"]] = fold;

                    var parent = self.parent;
                    var task_model = parent.state.modelName;

                     parent._rpc({
                            model: task_model,
                            method: 'fold_update',
                            args: [fold_dic],
                            context: parent.state.contexts
                        })
                        .then(function(ev) {
                            // parent.trigger_up('warning', {
                            //     title: _t('Tree Data Update'),
                            //     message: _t('Data updated : ') + ev
                            // });
                     });

                }

            }






        },


        onCollapse: function(event, treeId, treeNode) {


            var self = this;

            var widget = treeNode.widget;
            var zTree = widget.$zTree;

            var node = zTree.getNodeByTId(treeNode.tId);

            var childs =  treeNode.widget.getChildNodes(node);

            // console.log(lch);

            widget.fold_bar(node, childs, true)


        },

        onExpand: function (event, treeId, treeNode) {

            var widget = treeNode.widget;
            var zTree = widget.$zTree;
            // var zTree = $.fn.zTree.getZTreeObj("treeGantt");

            var node = zTree.getNodeByTId(treeNode.tId);

            var childs =  treeNode.widget.getChildNodes(node);

            // console.log(lch)

             widget.fold_bar(node, childs, false)
        },




        addHoverDom: function (treeId, treeNode) {

            var widget = treeNode.widget;

            treeNode.widget_parent.trigger_up('gantt_add_hover', {
                data_id: treeNode.id
            });




            //              if (this.record.group_field === self.action_menu){
            //
            //     var first_bar = $('<div class="task-gantt-item-info" style="float: right;"/>');
            //
            //
            //
            //      // this.$el.append('<div class="task-gantt-item-info" style="float: right;">'+duration_humanize+'</div>');
            //
            //     first_bar.append('<span class="task-gantt-plus"><i class="fa fa-plus fa-1x"></i></span>');
            //     first_bar.append('<span class="task-gantt-refresh"><i class="fa fa-refresh fa-1x"></i></span>');
            //
            //     if (self.export_wizard){
            //         first_bar.append('<span class="task-gantt-wizard"><i class="fa fa-arrow-right fa-arrow-click fa-1x"></i></span>');
            //     }
            //
            //     // first_bar.append('<span class="task-gantt-critical"><i class="fa fa-line-chart fa-1x"></i></span>');
            //     this.$el.append(first_bar);
            // }




                 if (!$(".item-button_" + treeNode.tId).length) {

                     var aObj = $("#" + treeNode.tId + "_a");

                     if (widget.tree_view ) {

                         //add
                         var add_bar = $('<span class="button custom task-gantt-add"/>');
                         add_bar.addClass("item-button_" + treeNode.tId);
                         add_bar.append('<i class="fa fa-plus fa-1x"></i>');
                         add_bar.attr("title", "Add Record");
                         aObj.append(add_bar);
                     }



                     if (treeNode.group_field && treeNode.group_field === widget.action_menu) {


                         //Refresh
                         var refresh_bar = $('<span class="button custom task-gantt-refresh"/>');
                         refresh_bar.addClass("item-button_" + treeNode.tId);
                         refresh_bar.append('<i class="fa fa-refresh fa-1x"></i>');
                          refresh_bar.attr("title", "Rescheduling");
                         aObj.append(refresh_bar);


                         //Export
                         if (widget.export_wizard){
                             var export_bar = $('<span class="button custom task-gantt-wizard"/>');
                             export_bar.addClass("item-button_" + treeNode.tId);
                             export_bar.append('<i class="fa fa-arrow-right fa-arrow-click fa-1x"></i>');
                             export_bar.attr("title", "Export Wizard");
                             aObj.append(export_bar);
                         }

                     }


             }

        },

        removeHoverDom: function (treeId, treeNode) {

            treeNode.widget_parent.trigger_up('gantt_remove_hover', {
                    treeNode: treeNode,
                    treeId: treeId,
                    data_id: treeNode.id
                });

            $(".item-button_" + treeNode.tId).remove();

        },


        open_record: function (event, options) {


        var res_id = false;
        var res_model = false;
        var res_open = false;
        var start_date = false;

        var readonly = false;

        var buttons = [
                {
                    text: _lt("Save"),
                    classes: 'btn-primary',
                    close: true,
                    click:  function () {
                        this._save().then(
                            self.trigger_up('gantt_refresh_after_change' )
                        );
                    }
                },

                {
                    text: _t("Edit in Form View"),
                    classes: 'btn-primary',
                    close: true,
                    click: function() {

                        this.trigger_up('open_record', {res_id: this.res_id, mode: "edit", model : this.res_model});
                    }},

                {
                    text: _lt("Delete"),
                    classes: 'btn-default',
                    close: true,
                    click: function () {

                        self._rpc({
                                model: this.res_model,
                                method: 'unlink',
                                args: [this.res_id],
                            })
                            .then(function(ev) {
                                self.trigger_up('gantt_refresh_after_change',ev );
                        });

                }},

                {
                    text: _lt("Close"),
                    classes: 'btn-default',
                    close: true,
                    click: function (){
                        self.trigger_up('gantt_refresh_after_change' )
                    }}
            ];



        if (event.data.is_group && event.data.group_field == 'project_id') {

            res_id = event.data.group_id;
            res_model = 'project.project';
            res_open = true;
            readonly = false;
            buttons.splice(1, 1)

        }

         if ( event.data.is_group == false && event.data.id ) {

            res_id = event.data.id;
            res_model = this.__parentedParent.state.modelName;
            res_open = true;

        }


        if (res_open) {

            var self = this.__parentedParent;

            var rowdata = '#task-gantt-timeline-row-'+res_id;
            var rowitem = '#task-gantt-item-'+res_id;

            $(rowdata).addClass("task-gantt-timeline-row-hover");
            $(rowitem).addClass("task-gantt-item-hover");

            self.hover_id = res_id;

            self.TimeToLeft = $('.task-gantt-timeline').scrollLeft();
            self.ScrollToTop = $('.task-gantt').scrollTop();


            var view_id = false;

            this.model = res_model;

            new dialogs.FormViewDialog(this.__parentedParent, {

                res_model: res_model,
                res_id: res_id,
                view_id: view_id,
                context: this.__parentedParent.state.contexts,
                readonly: readonly,
                buttons: buttons,

            }).open();


        } else {
            this.__parentedParent.do_warn("Gannt: Open Only - Project or Task # " + event.data.id);
        }
    },

        edit_record: function (event) {
            this.open_record(event, {mode: 'edit'});
        },


        zTreeOnClick: function(ev, treeId, treeNode) {

            //alert(treeNode.tId + ", " + treeNode.zt_id);

            //Scheduling action
            var is_group = treeNode.is_group || false;
            var group_id = false;
            var group_field = false;


            //Edit Task
            if ($(ev.target).hasClass("node_name" )) {

                if (is_group) {

                    group_id = treeNode.group_id[0];
                    group_field = treeNode.group_field;
                }

                treeNode.widget.trigger_up('item_record_edit', {
                    id: treeNode.id,
                    is_group: is_group,
                    group_id: group_id,
                    group_field: group_field,
                    start_date: treeNode.start_date

                });

            }



            //Resechuling
            if ($(ev.target).hasClass("fa-refresh")) {

                if (is_group) {
                    group_id = treeNode.group_id[0];
                    group_field = treeNode.group_field;
                }

                treeNode.widget.trigger_up('item_plan_action', {
                    id: treeNode.id,
                    is_group: is_group,
                    group_id: group_id,
                    group_field: group_field,
                    start_date: treeNode.start_date
                });
            }


            //Wizard export
            if ($(ev.target).hasClass("fa-arrow-click" )) {

                if (is_group) {

                    group_id = treeNode.group_id[0];
                    group_field = treeNode.group_field;
                }

               treeNode.widget.trigger_up('item_export_wizard', {
                   id: treeNode.id,
                   is_group: is_group,
                   group_id: group_id,
                   group_field: group_field,
                   exoprt_wizard: treeNode.widget.export_wizard,
               });

            }


                        //Add Task
            if ($(ev.target).hasClass("fa-plus")) {


                // var is_group = match_node.is_group || false;

                var parent_id = false;
                var project_id = false;

                if (is_group) {
                    project_id = treeNode.group_id[0];
                }
                else{
                    parent_id = treeNode.id;
                    project_id = treeNode.subtask_project_id[0]
                }

                treeNode.widget.trigger_up('item_record_add', {
                        project_id: project_id,
                        parent_id: parent_id,
                });

            }



        },


        beforeDrag: function (treeId, treeNodes) {
			for (var i=0,l=treeNodes.length; i<l; i++) {
				if (treeNodes[i].drag === false) {
					return false;
				}
			}
			return true;
		},

        beforeDrop: function (treeId, treeNodes, targetNode, moveType) {

            var result = false;

            // if (targetNode.parentTId !== treeNodes[0].parentTId){
            //     return result
            // }

            if (targetNode && targetNode.drop !== false) {
                result = true;
            }
            return result
        },


		onDrop: function (ev, treeId, treeNodes, targetNode, moveType) {

            var self = this;
            var result = false;
            if (targetNode && targetNode.drop !== false){

                var treeNode = treeNodes[0];


                //if (child['isParent']) {
                //     aObj.addClass("task-gantt-items-subtask")
                // }

                var zTree = targetNode.widget.$zTree;

                var nodes = zTree.getNodes();

                var match_task = undefined;
                var zt_pId = undefined;

                if (moveType === "inner"){

                    match_task = zTree.getNodeByParam('id', treeNode.id);
                    match_task.plan_action = 1;
                    zt_pId = targetNode.zt_id;
                }

                if (moveType === "next" || moveType === "prev"){

                    // if (targetNode.is_group){
                    //     targetNode.widget_parent.trigger_up('gantt_refresh_after_change');
                    //     return false
                    // }

                    match_task = zTree.getNodeByParam('id', treeNode.id);
                    match_task.plan_action = 1;
                    zt_pId = targetNode.zt_pId

                }
                // console.log(moveType);


                var rows_to_gantt = [];

                _.each(nodes, function (node) {

                    var childNodes = zTree.transformToArray(node);

                    _.each(childNodes, function (child) {

                        var root_node_select =  "root_"+treeNode.subtask_project_id[0]+"_"+treeNode.subtask_project_id[1];

                        if (root_node_select  === node.zt_id){

                            if (child.isParent){
                                child.fontCss = {'font-weight':'bold'}
                            }else{
                                child.fontCss = {}
                            }



                            var for_update = {
                                "id": child.id,
                                "plan_action": child.plan_action,
                                "is_group": child.is_group,
                                "sorting_level": child.level
                            };
                            rows_to_gantt.push(for_update)
                        }

                    });

                });


                if (match_task){

                    var parent = targetNode.widget_parent;
                    var task_model = parent.state.modelName;

                     parent._rpc({
                            model: task_model,
                            method: 'tree_update',
                            args: [rows_to_gantt, treeNode.zt_id, zt_pId],
                            context: parent.state.contexts
                        })
                        .then(function(ev) {
                            parent.trigger_up('warning', {
                                title: _t('Tree Data Update'),
                                message: _t('Data updated : ') + ev
                            });
                     });

                }

                targetNode.widget_parent.trigger_up('gantt_fast_refresh_after_change');

                result = true;
            }

            return result;

		},


        plan_action: function(event) {

            if (event.data.is_group && event.data.group_field === 'project_id') {
                var self = this.__parentedParent;

                var  res_id = event.data.group_id;

                var  res_model = 'project.task';
                framework.blockUI();

                self._rpc({
                        model: res_model,
                        method: 'scheduler_plan',
                        args: [res_id],
                        context: self.state.contexts
                    })
                    .then(function(ev) {
                        framework.unblockUI();
                        self.trigger_up('gantt_refresh_after_change',ev );
                });
            }
        },


        start: function () {
            var self = this;
            this._super.apply(this, arguments);
            if (!self.$zTree) {


                _.each(self.records, function (record) {

                    record["open"] = !record["fold"]

                });

                self.$zTree = $.fn.zTree.init(self.$el.find("#treeGantt"), self.setting, self.records);


                var nodes = self.$zTree.getNodes();

                 _.each(nodes, function (node) {

                    if (typeof(node["fold"]) != 'undefined' && node["fold"] != null) {

                        // if (!node["fold"]){
                        //     self.$zTree.expandNode(node, true, true, true);
                        // }

                    }else{
                        self.$zTree.expandAll(true);
                    }


                     var childNodes = self.$zTree.transformToArray(node);


                     _.each(childNodes, function (child) {


                            var nnode = self.$zTree.getNodeByTId(child.tId);
                            var nchildren = nnode.children;
                            _.each(nchildren, function (nchild) {
                                    nchild["fold"] = !child["open"]
                            });


                            var aObj = self.$el.find("#" + child.tId + "_a");
                            aObj.addClass("task-gantt-item-"  + child.zt_id + "");
                            aObj.addClass("task-gantt-item");
                            aObj.prop('data-id', child.zt_id);

                            child["widget_parent"] = self.parent;
                            child["widget"] = self;

                            if (child["is_group"]) {
                                aObj.addClass("task-gantt-items-group");
                                aObj.css({'background-color':  "rgba(40, 95, 143, 0.10)"});

                            }

                            if (child["is_group"] && child["level"] === 0) {
                                aObj.css({'background-color':  "beige"});
                            }


                     })

                 });

            }
        },


        add_record: function(event){

            var context = this.__parentedParent.state.contexts;
            var self = this.__parentedParent;

            context['default_project_id'] = event.data.project_id || false;
            context['default_parent_id'] = event.data.parent_id || false;


            self.TimeToLeft = $('.task-gantt-timeline').scrollLeft();
            self.ScrollToTop = $('.task-gantt').scrollTop();


            var pop = new dialogs.FormViewDialog(self, {
                res_model: 'project.task',
                res_id: false,
                context: context,
                title: _t("Please Select Project First For Task"),
                on_saved: function () {
                    self.trigger_up('gantt_refresh_after_change' )
                    },
            }).open();

        },


        open_export_wizard: function(event){


            var context = this.__parentedParent.state.contexts;
            var self = this.__parentedParent;

            // var rows_to_gantt = self.rows_to_gantt;
            var time_type = self.timeType;


            var group_id = event.data["group_id"];

            context['default_group_id'] = group_id || false;
            // context['rows_to_gantt'] = rows_to_gantt || false;
            context['time_type'] = time_type || false;



            var res_model = event.data["exoprt_wizard"];

            var pop = new dialogs.FormViewDialog(this.__parentedParent, {
                res_model: res_model,
                res_id: false,
                context: context,
                title: _t("PDF Report for Project"),
            }).open();

        },

    });

    return ItemzTree

});
