odoo.define('web_gantt_native.NativeGanttController', function (require) {
"use strict";

var AbstractController = require('web.AbstractController');
var core = require('web.core');
var config = require('web.config');
var Dialog = require('web.Dialog');
var dialogs = require('web.view_dialogs');
var time = require('web.time');

var GanttPager = require('web_gantt_native.Pager');


var _t = core._t;
var QWeb = core.qweb;


var NativeGanttController = AbstractController.extend({

    custom_events: _.extend({}, AbstractController.prototype.custom_events, {
        gantt_refresh_after_change: '_onGanttRefresh',
        gantt_fast_refresh_after_change: '_update',
        gantt_add_hover: '_add_hover',
        gantt_remove_hover: '_remove_hover',

        // gantt_drop_item: '_drop_item',

        'sort_item': function (event) {
            this.sort_item(event.target);
        },

    }),
    events: {
        'mousedown .task-gantt-gutter': 'GutterMouseDown',


        'mouseover  .task-gantt-info, .task-gantt-timeline-row'     :'HandleHoverOver',
        'mouseout   .task-gantt-info, .task-gantt-timeline-row'     :'HandleHoverOut',

        'mouseover  .task-gantt-gutter'     :'GutterOver',
        'mouseout   .task-gantt-gutter'     :'GutterOut'

    },



    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.set('title', params.title);
        this.context = params.context;

    },


    _onOpenRecord: function (event) {
        event.stopPropagation();
        // var record = this.model.get(event.data.id, {raw: true});
        this.trigger_up('switch_view', {
            view_type: 'form',
            res_id: event.data.res_id,
            mode: event.data.mode || 'readonly',
            model: event.data.model
        });
    },


    _onGanttRefresh: function (event) {
        var self = this;
        this.model._do_load().then(function (ev) {
                self.reload();
            });

    },


    _update: function () {
        var self = this;
        //Get Zoom Event from time scale type

        if (this.renderer.timeType === 'month_day'){
            self.ZoomDaysClick();
        }
        if (this.renderer.timeType === 'day_1hour'){
            self.Zoom1hClick();
        }
        if (this.renderer.timeType === 'day_2hour'){
            self.Zoom2hClick();
        }
        if (this.renderer.timeType === 'day_4hour'){
            self.Zoom4hClick();
        }
        if (this.renderer.timeType === 'day_8hour'){
            self.Zoom8hClick();
        }
        if (this.renderer.timeType === 'year_month'){
            self.ZoomMonthClick();
        }
        if (this.renderer.timeType === 'month_week'){
            self.ZoomWeeksClick();
        }
        if (this.renderer.timeType === 'quarter'){
            self.ZoomQuarterClick();
        }


        //Update

        //Get Getter offset from session
        $('.task-gantt-list').width(this.renderer.session.gantt || this.renderer.gutterOffset);

        //Hover selected rows after refresh page
        var rowdata = '#task-gantt-timeline-row-'+this.renderer.hover_id;
        var rowitem = '#task-gantt-item-'+this.renderer.hover_id;

        $(rowdata).addClass("task-gantt-timeline-row-hover");
        $(rowitem).addClass("task-gantt-item-hover");


        // Goto Vertial and Horizontal Scroll
        if (this.renderer.TimeToLeft) {
            var task_left = this.renderer.TimeToLeft;
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


            this.renderer.gantt_timeline_scroll_widget.scrollOffset(task_left);

        }


        if (this.renderer.ScrollToTop) {
           var panel_top = this.renderer.ScrollToTop;
            $('.task-gantt').animate({
                scrollTop: panel_top
                }, 0, function() {
            // Animation complete.
          });
        }

        if (this.pager){
            this.pager.refresh(this.renderer.state.pager.records, this.renderer.state.pager.limit);
        }


        return this._super.apply(this, arguments);
    },


    renderPager: function ($node, options) {

        var data = [];

        data["size"] = this.renderer.state.pager.records;
        data["limit"] = this.renderer.state.pager.limit;

        this.pager = new GanttPager(this, data.size, data.limit, options);

        this.pager.on('pager_changed', this, function (newState) {
            var self = this;
            self.pager.disable();

            this.renderer.state.pager.limit = parseInt(newState.limit);

            this.reload().then(self.pager.enable.bind(self.pager));

        });
        this.pager.appendTo($node);

    },



    renderButtons: function ($node) {
        if ($node) {
            var context = {measures: _.pairs(_.omit(this.measures, '__count__'))};
            this.$buttons = $(QWeb.render('APSGanttView.buttons', context));
            this.$buttons.click(this.on_button_click.bind(this));

            this.$buttons.appendTo($node);
        }
    },

    on_button_click: function (event) {
        var $target = $(event.target);
        if ($target.hasClass('task-gantt-today')) { return this.ClickToday(); }
        if ($target.hasClass('task-gantt-zoom-1h')) { return this.Zoom1hClick(); }
        if ($target.hasClass('task-gantt-zoom-2h')) { return this.Zoom2hClick(); }
        if ($target.hasClass('task-gantt-zoom-4h')) { return this.Zoom4hClick(); }
        if ($target.hasClass('task-gantt-zoom-8h')) { return this.Zoom8hClick(); }
        if ($target.hasClass('task-gantt-zoom-days')) { return this.ZoomDaysClick(); }
        if ($target.hasClass('task-gantt-zoom-month')) { return this.ZoomMonthClick(); }
        if ($target.hasClass('task-gantt-zoom-weeks')) { return this.ZoomWeeksClick(); }
        if ($target.hasClass('task-gantt-zoom-quarter')) { return this.ZoomQuarterClick(); }

    },

    //Zoom Out - Zoom In



    Zoom1hClick: function() {
        this.ZoomHoursClick(1, 'day_1hour' );
        // this.timeType = 'day_1hour';
    },
    Zoom2hClick: function() {
        this.ZoomHoursClick(2, 'day_2hour');
        // this.timeType = 'day_2hour';
    },
    Zoom4hClick: function() {
        this.ZoomHoursClick(4, 'day_4hour');
        // this.timeType = 'day_4hour';
    },
    Zoom8hClick: function() {
        this.ZoomHoursClick(8, 'day_8hour');
        // this.timeType = 'day_8hour';
    },



    ZoomHoursClick: function(div_hour, timeType) {

        this.renderer.firstDayDate = moment(this.renderer.GtimeStart).clone().startOf('month'); //Start month
        this.renderer.lastDayDate = moment(this.renderer.GtimeStop).clone().endOf('month'); //End

        this.renderer.timeScaleUTC = this.renderer.lastDayDate.valueOf() - this.renderer.firstDayDate.valueOf(); // raznica vremeni
        this.renderer.firstDayScale = this.renderer.firstDayDate.valueOf();

        var iter = moment(this.renderer.firstDayDate).twix(this.renderer.lastDayDate).iterate(div_hour, 'hours');

        var hour2Range=[];
        while(iter.hasNext()){

             hour2Range.push(iter.next().toDate())

        }


        var daysGroup = _(hour2Range).groupBy(function (day) {
             return moment(day).format("YYYY MM DD");

        });

        this.renderer.timeType = timeType;
        this.renderer.timeScale = 40; //px

        var iter_k = moment(this.renderer.firstDayDate).twix(this.renderer.lastDayDate).iterate(1, 'hours');

        var K_scale=0;
        while(iter_k.hasNext()){
             iter_k.next();
             K_scale = K_scale + 1;
        }

        K_scale = K_scale / div_hour;
        // var K_scale = hour2Range.length;
        //
        // var first_tzm_m = this.renderer.firstDayDate.format("ZZ");
        // var second_tzm_m = this.renderer.lastDayDate.format("ZZ");
        // var diff_tzm_h = ( first_tzm_m - second_tzm_m)/100;
        //
        // K_scale = K_scale - (diff_tzm_h / div_hour);



        this.renderer.timeline_width = this.renderer.timeScale*K_scale; // min otrzok 60 - eto 4 4asa. v sutkah 6 otrezkov
        // this.renderer.timeline_width = this.renderer.timeScale*1092.5; // min otrzok 60 - eto 4 4asa. v sutkah 6 otrezkov

        this.renderer.pxScaleUTC = Math.round(this.renderer.timeScaleUTC / this.renderer.timeline_width); // skolko vremeni v odnom px


        this.renderer.AddItemsData();

        this.renderer.AddTimeLineHead(this.renderer.timeScale, this.renderer.timeType, daysGroup, false );
        this.renderer.AddTimeLineData(this.renderer.timeScale, this.renderer.timeType, this.renderer.rows_to_gantt);

        this.renderer.AddTimeLineArrow(this.renderer.timeline_width);
        this.renderer.AddTimeLineGhost();

        this.renderer.AddTimeLineSummary();
        this.renderer.AddTimeLineFirst();



    },

    ZoomDaysClick: function() {

        this.renderer.firstDayDate = moment(this.renderer.GtimeStart).clone().startOf('month'); //Start month
        this.renderer.lastDayDate = moment(this.renderer.GtimeStop).clone().endOf('month'); //End
        this.renderer.timeScaleUTC = this.renderer.lastDayDate.valueOf() - this.renderer.firstDayDate.valueOf(); // raznica vremeni
        this.renderer.firstDayScale = this.renderer.firstDayDate.valueOf();

        var currentLocaleData = moment.localeData();

        //Get Days Range
        var iter = moment(this.renderer.firstDayDate).twix(this.renderer.lastDayDate).iterate("days");

        var dayRange=[];
        while(iter.hasNext()){
            dayRange.push(iter.next().toDate())
        }

        //Get Year - Month range
        var iter_first = moment(this.renderer.firstDayDate).twix(this.renderer.lastDayDate).iterate("month");

        var monthRange=[];
        while(iter_first.hasNext()){

            var mt_month = iter_first.next();
            var month = [];

            month['year'] =  mt_month.year();
            month['month'] =  currentLocaleData.months(mt_month);
            month['days'] =  mt_month.daysInMonth();

            monthRange.push(month)
        }

        this.renderer.timeScale = 24; //px
        this.renderer.timeType = 'month_day';
        this.renderer.timeline_width = this.renderer.timeScale*dayRange.length;
        this.renderer.pxScaleUTC = Math.round(this.renderer.timeScaleUTC / this.renderer.timeline_width); // skolko vremeni v odnom px

        this.renderer.AddItemsData();

        this.renderer.AddTimeLineHead(this.renderer.timeScale, this.renderer.timeType, monthRange, dayRange );
        this.renderer.AddTimeLineData(this.renderer.timeScale, this.renderer.timeType, this.renderer.rows_to_gantt);

        this.renderer.AddTimeLineArrow(this.renderer.timeline_width);
        this.renderer.AddTimeLineGhost();

        this.renderer.AddTimeLineSummary();
        this.renderer.AddTimeLineFirst();

    },

    ZoomMonthClick: function() {

        this.renderer.firstDayDate = moment(this.renderer.GtimeStart).clone().startOf('month'); //Start month
        this.renderer.lastDayDate = moment(this.renderer.GtimeStop).clone().endOf('month'); //End
        this.renderer.timeScaleUTC = this.renderer.lastDayDate.valueOf() - this.renderer.firstDayDate.valueOf(); // raznica vremeni
        this.renderer.firstDayScale = this.renderer.firstDayDate.valueOf();

        var iter = moment(this.renderer.firstDayDate).twix(this.renderer.lastDayDate).iterate('month');

        var month2Range=[];
        while(iter.hasNext()){

             month2Range.push(iter.next().toDate())

        }

        var monthGroup = _(month2Range).groupBy(function (month) {
             return moment(month).format("YYYY");

        });


        this.renderer.timeScale = 30 ;//px
        this.renderer.timeType = 'year_month';

        this.renderer.timeline_width = this.renderer.timeScale*month2Range.length; // min otrzok 60 - eto 4 4asa. v sutkah 6 otrezkov
        this.renderer.pxScaleUTC = Math.round(this.renderer.timeScaleUTC / this.renderer.timeline_width); // skolko vremeni v odnom px

        this.renderer.AddItemsData();

        this.renderer.AddTimeLineHead(this.renderer.timeScale, this.renderer.timeType, monthGroup, false );
        this.renderer.AddTimeLineData(this.renderer.timeScale, this.renderer.timeType, this.renderer.rows_to_gantt);

        this.renderer.AddTimeLineArrow(this.renderer.timeline_width);
        this.renderer.AddTimeLineGhost();

        this.renderer.AddTimeLineSummary();
        this.renderer.AddTimeLineFirst();

    },


    ZoomWeeksClick: function() {
        //
        this.renderer.firstDayDate = moment(this.renderer.GtimeStart).clone().startOf('isoWeek'); //Start month
        this.renderer.lastDayDate = moment(this.renderer.GtimeStop).clone().endOf('isoWeek'); //End

        this.renderer.timeScaleUTC = this.renderer.lastDayDate.valueOf() - this.renderer.firstDayDate.valueOf(); // raznica vremeni
        this.renderer.firstDayScale = this.renderer.firstDayDate.valueOf();

        var iter = moment(this.renderer.firstDayDate).twix(this.renderer.lastDayDate).iterate('Week');

        var week2Range=[];
        while(iter.hasNext()){
             week2Range.push(iter.next().toDate())
        }

        var weeksGroup = _(week2Range).groupBy(function (week) {
             return moment(week).format("YYYY");
        });


        this.renderer.timeScale = 30 ;//px
        this.renderer.timeType = 'month_week';

        this.renderer.timeline_width = this.renderer.timeScale*week2Range.length; // min otrzok 60 - eto 4 4asa. v sutkah 6 otrezkov
        this.renderer.pxScaleUTC = Math.round(this.renderer.timeScaleUTC / this.renderer.timeline_width); // skolko vremeni v odnom px

        this.renderer.AddItemsData();

        this.renderer.AddTimeLineHead(this.renderer.timeScale, this.renderer.timeType, weeksGroup, false );
        this.renderer.AddTimeLineData(this.renderer.timeScale, this.renderer.timeType, this.renderer.rows_to_gantt);

        this.renderer.AddTimeLineArrow(this.renderer.timeline_width);
        this.renderer.AddTimeLineGhost();

        this.renderer.AddTimeLineSummary();
        this.renderer.AddTimeLineFirst();


    },


    ZoomQuarterClick: function() {


        this.renderer.firstDayDate = moment(this.renderer.GtimeStart).clone().startOf('Quarter'); //Start month
        this.renderer.lastDayDate = moment(this.renderer.GtimeStop).clone().endOf('Quarter'); //End
        this.renderer.timeScaleUTC = this.renderer.lastDayDate.valueOf() - this.renderer.firstDayDate.valueOf(); // raznica vremeni
        this.renderer.firstDayScale = this.renderer.firstDayDate.valueOf();


        var iter = moment(this.renderer.firstDayDate).twix(this.renderer.lastDayDate).iterate('Quarter');

        var quarter2Range=[];
        while(iter.hasNext()){
             quarter2Range.push(iter.next().toDate())
        }

        var quarterGroup = _(quarter2Range).groupBy(function (quarter) {
             return moment(quarter).format("YYYY");
        });


        this.renderer.timeScale = 80 ;//px
        this.renderer.timeType = 'quarter';

        this.renderer.timeline_width = this.renderer.timeScale*quarter2Range.length; // min otrzok 60 - eto 4 4asa. v sutkah 6 otrezkov
        this.renderer.pxScaleUTC = Math.round(this.renderer.timeScaleUTC / this.renderer.timeline_width); // skolko vremeni v odnom px


        this.renderer.AddItemsData();

        this.renderer.AddTimeLineHead(this.renderer.timeScale, this.renderer.timeType, quarterGroup, false );
        this.renderer.AddTimeLineData(this.renderer.timeScale, this.renderer.timeType, this.renderer.rows_to_gantt);

        this.renderer.AddTimeLineArrow(this.renderer.timeline_width);
        this.renderer.AddTimeLineGhost();

        this.renderer.AddTimeLineSummary();
        this.renderer.AddTimeLineFirst();


    },

    //Gutter Movie

    GutterMouseDown: function(event){

        this.renderer.$el.delegate('.task-gantt', 'mouseup', this.proxy('GutterMouseUp'));
        this.renderer.$el.delegate('.task-gantt', 'mousemove', this.proxy('GutterMouseMove'));
        this.renderer.gutterClientX = event.clientX;
    },


    GutterMouseUp: function(event){

        this.renderer.$el.undelegate('.task-gantt', 'mouseup');
        this.renderer.$el.undelegate('.task-gantt', 'mousemove');
    },

    GutterMouseMove: function(event){

        var parentOffset = $('.task-gantt-gutter').parent().offset();
        var pxc = this.renderer.gutterOffsetX + (event.clientX - parentOffset.left);

        $('.task-gantt-list').width(pxc);
        $('.timeline-gantt-items').width(pxc);


        this.renderer.session.gantt = pxc;
        this.renderer.gutterOffsetSession = pxc;
    },


    GutterOver: function(event){

        $('.task-gantt-gutter').addClass("task-gantt-gutter-hover");
        $('.timeline-gantt-gutter').addClass("task-gantt-gutter-hover");


    },

    GutterOut: function(event){

        $('.task-gantt-gutter').removeClass("task-gantt-gutter-hover");
        $('.timeline-gantt-gutter').removeClass("task-gantt-gutter-hover");


    },



//Today Focus of Gantt Line Focus
    ClickToday: function (event) {

        var today = new Date();

        var toscale = this.TimeToScale(today.getTime());

        this.renderer.TimeToLeft = toscale;
        this.Focus_Gantt(toscale);

    },

    // Any can focus on BAR
    Focus_Gantt: function(task_start){

        $('.timeline-gantt-head').animate( { scrollLeft: task_start-500 }, 1000);
        $('.task-gantt-timeline').animate( { scrollLeft: task_start-500 }, 1000);

        this.renderer.gantt_timeline_scroll_widget.scrollOffset(task_start-500);

    },

    TimeToScale: function(time){

       if (time){

        return Math.round((time-this.renderer.firstDayScale) / this.renderer.pxScaleUTC);
    }

    },

    // _drop_item: function(ev) {
    //
    //     var df = 45;
    //
    // },

// HandleHover
    _add_hover:  function(ev) {

        var rowdata = '#task-gantt-timeline-row-'+ev.data['data_id'];
        $(rowdata).addClass("task-gantt-timeline-row-hover");

        var item_info = '#item-info-'+ev.data['data_id'];
        $(item_info).addClass("item-info-hover");


    },

    _remove_hover:  function(ev) {

        var rowdata = '#task-gantt-timeline-row-'+ev.data['data_id'];
        $(rowdata).removeClass("task-gantt-timeline-row-hover");

        var item_info = '#item-info-'+ev.data['data_id'];
        $(item_info).removeClass("item-info-hover");

    },

    HandleHoverOver: function(ev) {

        if (ev.target.allowRowHover)
        {

            // var rowsort = '#task-gantt-item-sorting-'+ev.target['data-id'];
            var rowdata = '#task-gantt-timeline-row-'+ev.target['data-id'];
            // var rowitem = '#task-gantt-item-'+ev.target['data-id'];

            var z_item = '.task-gantt-item-'+ev.target['data-id'];

            // $(rowsort).addClass("task-gantt-sorting-item-hover");

            $(rowdata).addClass("task-gantt-timeline-row-hover");
            // $(rowitem).addClass("task-gantt-item-hover");

            $(z_item).addClass("task-gantt-item-hover");

            var item_info = '#item-info-'+ev.target['data-id'];
            $(item_info).addClass("item-info-hover");


        }

    },


    HandleHoverOut: function(ev) {


        var item_info = '#item-info-'+ev.target['data-id'];
        $(item_info).removeClass("item-info-hover");

        // var rowsort = '#task-gantt-item-sorting-'+ev.target['data-id'];
        var rowdata = '#task-gantt-timeline-row-'+ev.target['data-id'];
        // var rowitem = '#task-gantt-item-'+ev.target['data-id'];

        var z_item = '.task-gantt-item-'+ev.target['data-id'];

        // $(rowsort).removeClass("task-gantt-sorting-item-hover");
        $(rowdata).removeClass("task-gantt-timeline-row-hover");
        // $(rowitem).removeClass("task-gantt-item-hover");

        $(z_item).removeClass("task-gantt-item-hover");

    }









});

return NativeGanttController;

});
