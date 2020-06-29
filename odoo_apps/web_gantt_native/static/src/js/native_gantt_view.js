odoo.define('web_gantt_native.NativeGanttView', function (require) {
"use strict";

var AbstractView = require('web.AbstractView');
var core = require('web.core');

var NativeGanttModel = require('web_gantt_native.NativeGanttModel');
var NativeGanttRenderer = require('web_gantt_native.NativeGanttRenderer');
var NativeGanttController = require('web_gantt_native.NativeGanttController');

var view_registry = require('web.view_registry');

var _lt = core._lt;

var GanttContainer = AbstractView.extend({

    display_name: _lt('Native Gantt'),
    icon: 'fa-tasks',
    viewType: 'ganttaps',

    config: {
        Model: NativeGanttModel,
        Controller: NativeGanttController,
        Renderer: NativeGanttRenderer,
    },


    init: function (viewInfo, params) {

        this._super.apply(this, arguments);


        this.rendererParams.viewType = this.viewType;

        this.controllerParams.confirmOnDelete = true;
        this.controllerParams.archiveEnabled = 'active' in this.fields;
        this.controllerParams.hasButtons = 'action_buttons' in params ? params.action_buttons : true;

        this.loadParams.fieldsInfo = this.fieldsInfo;
        this.loadParams.fields = viewInfo.fields;
        this.loadParams.context = params.context || {};
        this.loadParams.limit = parseInt(this.arch.attrs.limit, 10) || params.limit;
        this.loadParams.viewType = this.viewType;
        this.loadParams.parentID = params.parentID;
        this.recordID = params.recordID;

        this.model = params.model;

        this.loadParams.fieldsView = viewInfo;
        this.loadParams.fieldsView.arch = this.arch;
        this.loadParams.mapping = this.arch.attrs;



    },
});

view_registry.add('ganttaps', GanttContainer);

return GanttContainer;

});
