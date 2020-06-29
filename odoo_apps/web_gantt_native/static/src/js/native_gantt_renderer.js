odoo.define('web_gantt_native.NativeGanttRenderer', function (require) {
"use strict";

var AbstractRenderer = require('web.AbstractRenderer');
var core = require('web.core');
var field_utils = require('web.field_utils');
var time = require('web.time');

var GanttToolField =    require('web_gantt_native.ToolField');


var GanttTimeLineHead = require('web_gantt_native.TimeLineHead');
var GanttTimeLineHeader = require('web_gantt_native.TimeLineHeader');
var GanttTimeLineScroll = require('web_gantt_native.TimeLineScroll');

var GanttTimeLineData = require('web_gantt_native.TimeLineData');

var GanttTimeLineArrow = require('web_gantt_native.TimeLineArrow');

var GanttTimeLineGhost = require('web_gantt_native.Ghost');
var GanttTimeLineSummary = require('web_gantt_native.Summary');
var GanttTimeLineFirst = require('web_gantt_native.BarFirst');

var GanttTimeLineInfo = require('web_gantt_native.Info');

var GanttResourcesLevel = require('web_gantt_native.ResLevel');
var GanttResourcesBar = require('web_gantt_native.ResBar');


var GanttListOptionsItem = require('web_gantt_native.ItemOptions');
var GanttTimeLineDocs = require('web_gantt_native.Docs');



var GanttListAction = require('web_gantt_native.ItemAction');
var GanttItemzTree = require('web_gantt_native.ItemzTree');
var GanttListInfo = require('web_gantt_native.ItemInfo');


var session = require('web.session');





var _lt = core._lt;

var QWeb = core.qweb;

return AbstractRenderer.extend({
    className: "o_native_gantt_view",
    display_name: _lt('Gantt APS'),


    /**
     * @overrie
     */

    init: function () {
        this._super.apply(this, arguments);

        var self = this;

        this.chart_id = _.uniqueId();
        this.gantt_events = [];

        this.type = this.arch.attrs.type || 'native_gantt';

        // this.gutterOffset = this.session["gantt"] || 400;
        this.gutterOffset = 400;


        this.firstDayDate = undefined;
        this.lastDayDate = undefined;

        this.GtimeStartA = [];
        this.GtimeStopA = [];

        this.GtimeStart = undefined;
        this.GtimeStop = undefined;


        this.widgets = [];

        this.session = session;

        this.counter = 0;
        this.widgets = [];
        this.options = "all";

        this.gutterOffset = this.session["gantt"] || 400;
        this.gutterOffsetX = 2;
        this.timeline_width = undefined;
        this.timeScale = undefined;

        this.timeType = undefined;
        this.gantt_timeline_head_widget = undefined;
        this.gantt_timeline_data_widget = [];
        this.pxScaleUTC = undefined;
        this.firstDayScale = undefined;
        this.rows_to_gantt = undefined;
        this.timeScaleUTC = undefined;

        this.firstDayDate = undefined;
        this.lastDayDate = undefined;


        this.GtimeStartA = [];
        this.GtimeStopA = [];

        this.GtimeStart = undefined;
        this.GtimeStop = undefined;



        this.BarMovieValue = undefined;
        this.BarClickDiffX = undefined;
        this.BarClickX = undefined;

        this.BarRecord= undefined;

        this.BarClickDown = false;

        this.BarWidth = undefined;

        this.TimeToLeft = false;

        this.ItemsSorted = false;

        this.hint_move_widget = undefined;
        this.tip_move_widget = undefined;

        this.hover_id = undefined;

        this.ScrollToTop = undefined;


        this.Predecessor = undefined;

        this.Ghost = undefined;
        this.Ghost_Data = undefined;

        this.BarFirst = undefined;
        this.BarFirst_Data = undefined;


        this.main_group_id_name = undefined;

        this.list_show = false;
        this.list_type = "datetime";


    },
    /**
     * @override
     */
    destroy: function () {
        while (this.gantt_events.length) {
            gantt.detachEvent(this.gantt_events.pop());
        }
        this._super();
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _render: function () {

        this._renderGantt();
        return $.when();
    },
    /**
     * Prepare the tasks and group by's to be handled by dhtmlxgantt and render
     * the view. This function also contains workaround to the fact that
     * the gantt view cannot be rendered in a documentFragment.
     *
     * @private
     */
    _renderGantt: function () {
        var self = this;

        // var parent = {};

        self.Predecessor = self.state.data.predecessor;
        self.Task_Info = self.state.data.task_info;

        self.Ghost = self.state.data.Ghost ;
        self.Ghost_Data = self.state.data.Ghost_Data ;

        self.BarFirst = self.state.data.BarFirst;
        self.BarFirst_Data =  self.state.data.BarFirst_Data;

        self.ExportWizard = self.state.data.ExportWizard;
        self.Main_Group_Id_Name = self.state.data.Main_Group_Id_Name;
        self.Action_Menu = self.state.data.Action_Menu;

        self.fields_view = self.state.fields_view;
        self.ItemsSorted = self.state.data.ItemsSorted;
        self.fields = self.state.fields;
        self.model_fields_dict  = self.state.data.model_fields_dict;
        self.TreeView = self.state.data.TreeView;

        self.LoadMode = self.state.data.LoadMode;
        self.Load_Data = self.state.data.Load_Data;

        self.Task_Load_Data = self.state.data.Task_Load_Data;

        self.GtimeStart = self.state.data.GtimeStart;
        self.GtimeStop = self.state.data.GtimeStop;


        //set time scale type if is undefined
        if ( self.timeType === undefined ) {
            self.timeType = 'month_day';
        }


        //Gantt Conteriner Render.
        self.$el.html(QWeb.render('GanttContainerView.main', {
            'title': "My Table",
            'widget': self,
            'display_name': this.display_name,
            'gutterOffset' : this.gutterOffset,

        }));

        //Sorted and grouped to flat list
        self.rows_to_gantt = self.state.data.rows_to_gantt;


        // Start - End month
        self.firstDayDate = moment(self.GtimeStart).clone().startOf('month'); //Start month
        self.lastDayDate = moment(self.GtimeStop).clone().endOf('month'); //End month
        self.timeScaleUTC = self.lastDayDate.valueOf() - self.firstDayDate.valueOf(); // raznica vremeni
        self.firstDayScale = self.firstDayDate.valueOf();



        var options = { items_sorted: self.ItemsSorted,
                        export_wizard: self.ExportWizard,
                        main_group_id_name: self.Main_Group_Id_Name,
                        tree_view : self.TreeView,
                        action_menu: self.Action_Menu,

        };

        self.widget_ztree = new GanttItemzTree(self, self.rows_to_gantt, options);
        self.widget_ztree.appendTo(self.$('.task-gantt-items'));


    },


    AddItemsData: function (){
        var self = this;


        //Item Action
        if (self.widget_item_action){
            this.widget_item_action.destroy();
            self.widget_item_action = [];
        }

        var options = {
            items_sorted: self.ItemsSorted,
            export_wizard: self.ExportWizard,
            main_group_id_name: self.Main_Group_Id_Name,
            tree_view: self.TreeView,
            action_menu: self.Action_Menu,
        };


        self.widget_item_action = new GanttListAction(self, options);
        self.widget_item_action.appendTo(self.$('.task-gantt-action'));



        //Item Info
        if (self.widget_item_info){
            this.widget_item_info.destroy();
            self.widget_item_info = [];
        }

        self.widget_item_info = new GanttListInfo(self, options);
        self.widget_item_info.appendTo(self.$('.task-gantt-info'));


    },


    AddTimeLineArrow: function( timeline_width ) {

        var self = this;
        if (self.gantt_timeline_arrow_widget){
            this.gantt_timeline_arrow_widget.destroy();
            self.gantt_timeline_arrow_widget = [];
        }

        this.gantt_timeline_arrow_widget = new GanttTimeLineArrow(self, timeline_width );
        this.gantt_timeline_arrow_widget.appendTo(self.$('.task-gantt-timeline-inner'));

    },


    AddTimeLineHead: function(timeScale, time_type, time_month, time_day ) {

        var self = this;
        if (this.gantt_timeline_head_widget){
            this.gantt_timeline_head_widget.destroy();
        }

        this.gantt_timeline_head_widget = new GanttTimeLineHead(self, timeScale, time_type, time_month, time_day  );
        this.gantt_timeline_head_widget.appendTo(self.$('.task-gantt-timeline-inner'));


        if (this.gantt_timeline_header_widget){
            this.gantt_timeline_header_widget.destroy();
            this.gantt_timeline_header_widget = [];
        }

        this.gantt_timeline_header_widget = new GanttTimeLineHeader(self, timeScale, time_type, time_month, time_day  );

        // var ctrl_panel = $('.o_control_panel');
        var ctrl_panel = self.$('.timeline-gantt');
        this.gantt_timeline_header_widget.appendTo(ctrl_panel);


        if (this.gantt_item_options_widget){
            this.gantt_item_options_widget.destroy();
            this.gantt_item_options_widget = [];
        }
        this.gantt_item_options_widget = new GanttListOptionsItem.OptionsItem(self);
        this.gantt_item_options_widget.appendTo(self.$('.timeline-gantt-options'));


        if (this.gantt_timeline_scroll_widget){
            this.gantt_timeline_scroll_widget.destroy();
            this.gantt_timeline_scroll_widget = [];
        }


        this.gantt_timeline_scroll_widget = new GanttTimeLineScroll(self, timeScale, time_type, time_month, time_day  );

        // var ctrl_panel = $('.o_control_panel');
        var scroll_panel = self.$('.timeline-gantt-scroll');
        this.gantt_timeline_scroll_widget.appendTo(scroll_panel);



        // Goto Horizontal Scroll
        if (this.TimeToLeft) {
            var task_left = this.TimeToLeft;
            $('.task-gantt-timeline').animate({
                scrollLeft: task_left
                }, 0, function() {
            // Animation complete.
            });
            $('.timeline-gantt-head').animate({
                scrollLeft: task_left
                }, 0, function() {
            // Animation complete.
            });

            self.gantt_timeline_scroll_widget.scrollOffset(task_left);

        }

    },




     AddTimeLineData: function(timeScale, time_type, rows_to_gantt ) {

        var self = this;
        if (this.gantt_timeline_data_widget.length > 0){
            this.gantt_timeline_data_widget = [];
           //  _.each(this.gantt_timeline_data_widget, function(data_widget) {
           //      data_widget.destroy();
           //  })
        }

        var $zTree = self.widget_ztree.$zTree;
        var options = { items_sorted: self.ItemsSorted, tree_view : self.TreeView};
        var nodes = $zTree.getNodes();

         _.each(nodes, function (node) {

             var childNodes = $zTree.transformToArray(node);

             _.each(childNodes, function (child) {

                 var gantt_time_line_data = new GanttTimeLineData(self, timeScale, time_type, child, options);

                gantt_time_line_data.appendTo(self.$('.task-gantt-timeline-data'));
                self.gantt_timeline_data_widget.push(gantt_time_line_data);



             })
         });

        // var options = { items_sorted: self.ItemsSorted, tree_view : self.TreeView};
        //
        // _.map(rows_to_gantt, function (record) {
        //
        //      var gantt_time_line_data = new GanttTimeLineData(self, timeScale, time_type, record, options);
        //
        //      gantt_time_line_data.appendTo(self.$('.task-gantt-timeline-data'));
        //      self.gantt_timeline_data_widget.push(gantt_time_line_data);
        // });



     },

    AddTimeLineGhost: function() {

        //Ghost
        var self = this;
        if (self.gantt_timeline_ghost_widget){
            this.gantt_timeline_ghost_widget.destroy();
            self.gantt_timeline_ghost_widget = [];
        }

        this.gantt_timeline_ghost_widget = new GanttTimeLineGhost.GhostWidget(self);
        this.gantt_timeline_ghost_widget.appendTo(self.$('.task-gantt-timeline-data'));


        //Info
        if (self.gantt_timeline_info_widget){
            this.gantt_timeline_info_widget.destroy();
            self.gantt_timeline_info_widget = [];
        }

        this.gantt_timeline_info_widget = new GanttTimeLineInfo.InfoWidget(self);
        this.gantt_timeline_info_widget.appendTo(self.$('.task-gantt-bar-plan'));

        //Resources Level
        if (self.gantt_timeline_res_level_widget){
            this.gantt_timeline_res_level_widget.destroy();
            self.gantt_timeline_res_level_widget = [];
        }
        this.gantt_timeline_res_level_widget = new GanttResourcesLevel.ResLevelWidget(self);
        this.gantt_timeline_res_level_widget.appendTo(self.$('.task-gantt-timeline-data'));


        //Detail Task
        if (self.gantt_timeline_res_bar_widget){
            this.gantt_timeline_res_bar_widget.destroy();
            self.gantt_timeline_res_bar_widget = [];
        }
        this.gantt_timeline_res_bar_widget= new GanttResourcesBar.ResBarWidget(self);
        this.gantt_timeline_res_bar_widget.appendTo(self.$('.task-gantt-timeline-data'));


        //Docs
        if (self.gantt_timeline_docs_widget){
            this.gantt_timeline_docs_widget.destroy();
            self.gantt_timeline_docs_widget = [];
        }
        this.gantt_timeline_docs_widget= new GanttTimeLineDocs.DocsWidget(self);
        this.gantt_timeline_docs_widget.appendTo(self.$('.task-gantt-timeline-data'));


    },

    AddTimeLineSummary: function() {

        var self = this;
        if (self.gantt_timeline_summary_widget){
            self.gantt_timeline_summary_widget.destroy();
            self.gantt_timeline_summary_widget = [];
        }

        self.gantt_timeline_summary_widget = new GanttTimeLineSummary.SummaryWidget(self);
        self.gantt_timeline_summary_widget.appendTo(self.$('.task-gantt-timeline-data'));

    },

    AddTimeLineFirst: function() {

        var self = this;
        if (self.gantt_timeline_first_widget){
            this.gantt_timeline_first_widget.destroy();
            self.gantt_timeline_first_widget = [];
        }

        this.gantt_timeline_first_widget = new GanttTimeLineFirst.BarFirstWidget(self);
        this.gantt_timeline_first_widget.appendTo(self.$('.task-gantt-timeline-data'));

    },


});

});
