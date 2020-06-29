odoo.define('ks_list_view_manager.controller', function (require) {
    "use strict";

    var core = require('web.core');
    var ajax = require('web.ajax');
    var QWeb = core.qweb;
    var session = require('web.session');
    var Dialog = require('web.Dialog');
    var fieldUtils = require('web.field_utils');
    var ListController = require('web.ListController');
    var framework = require('web.framework');
    var view_registry = require('web.view_registry');
    var dom = require('web.dom');


    var _t = core._t;

    ListController.include({



        custom_events: _.extend({}, ListController.prototype.custom_events,{
            Ks_update_advance_search_renderer : "Ks_update_advance_search_controller",
            ks_remove_domain:"ks_remove_popup_domain",
            ks_update: "ks_update_columns",
            ks_clear_field_filters: "ks_clear_field_filters",
            on_ks_list_header_resize: "_onKsListHeaderResize",
        }),

        init: function (parent, model, renderer, params) {

            this.check = parent.className === "o_content";
            renderer.check = this.check;
            if(this.check) {
            this.ks_list_view_data = params.ks_lvm_data ? params.ks_lvm_data.ks_lvm_user_mode_data : false;
            this._super.apply(this, arguments);
            this.ks_lvm_mode = parent.className === "o_content";
            renderer.ks_lvm_mode = this.ks_lvm_mode;
            this.ks_lvm_mode = true;
            this.ksViewID = params.ks_lvm_data.ksViewID;
            this.ks_advance_search_refresh = false;
            this.ks_start_date = undefined;
            this.ks_end_date = undefined;
            this.ks_start_date_id = undefined;
            this.ks_end_date_id = undefined;
            this.ks_remove_popup_flag = false;
            this.ks_toggle = 0;
            this.ks_fields_data_dirty = {};
            this.ks_fields_data = params.ks_lvm_data && params.ks_lvm_data.ks_lvm_user_table_result ? params.ks_lvm_data.ks_lvm_user_table_result.ks_fields_data : false;



            if(!this.ks_fields_data) this.ks_fields_data = renderer.ks_fields_data;
            this.ks_field_list = Object.values(this.ks_fields_data).sort((a, b) => a.ks_field_order - b.ks_field_order);

            this.ks_table_data = params.ks_lvm_data && params.ks_lvm_data.ks_lvm_user_table_result ? params.ks_lvm_data.ks_lvm_user_table_result.ks_table_data : false;
            this.ks_lvm_user_mode_data = params.ks_lvm_data ? params.ks_lvm_data.ks_lvm_user_mode_data : false;
            this.ks_is_restore_flag = false;
            this.ks_editable = this.mode === "edit";
            this.ks_autocomplete_data = {};
            this.ks_autocomplete_data_result = {};
            this.ks_field_filter = {};
            this.ks_list_default_domain = false;
            }
            else{
                this._super.apply(this, arguments);
            }
        },

        renderButtons: function(){
            if(this.check){
            this._super.apply(this, arguments);
            if (this.$buttons){
                this.$buttons.on('click', '.ks_hide_show_checkbox', this._onKsFieldActiveClick.bind(this));
                this.$buttons.on('click', 'span.ks_editable', this._onKsSpanFieldEditableClick.bind(this));
                this.$buttons.on('focusout', 'input.ks_editable', this._onKsInputFieldEditableFocusout.bind(this));
                this.$buttons.on('click', '.cancel_button', this._onKsCancelButtonClick.bind(this));
                this.$buttons.on('hide.bs.dropdown', '#ks_dropdown', this._onKsHideLvmDropDown.bind(this));
                this.$buttons.on('click', '.restore_button', this.ks_confirm_restoreData.bind(this));
                this.$buttons.on('click', '.refresh_button', this.ks_reload_list_view.bind(this));
                this.$buttons.on('keyup', '#myInput', this.ks_searchBar.bind(this));
                this.$buttons.on('click', '.copy_button', this._onKsDuplicateRecord.bind(this));
                this.$buttons.on('click', '#mode', this.ks_modeToggle.bind(this));
            }
            }
            else{
                this._super.apply(this, arguments);
            }
        },

        on_attach_callback: function () {
            if(this.check){
            var self = this;
            $(".o_content").addClass("ks_lvm_o_content");
            $(".o_main_content").addClass("ks_lvm_o_main_content");

            this._ks_init_sortable();
             if(self.ks_lvm_user_mode_data.ks_dynamic_list_show === false) {
                      $('#ks_dropdown').hide();
                }else {
                if($(".o_list_button_add"). is(":visible")){
                    $('#ks_dropdown').show();
                }
                }
                 if(self.ks_lvm_mode) {

                if(self.ks_list_view_data.ks_can_edit === true) {
                    if($(".o_list_button_add"). is(":visible")){
                    $('.mode_button').show();
                    }
                } else {
                     $('.mode_button').hide();
                }



            }else{
                if(self.is_ks_editable_on){
                    self.editable = ''
                }
            }


            this._super.apply(this, arguments);
        }
            else{
                this._super.apply(this, arguments);
            }
        },

        on_detach_callback: function(){
            if(this.check){
            $(".o_content").removeClass("ks_lvm_o_content");
            $(".o_main_content").removeClass("ks_lvm_o_main_content");
            this._super.apply(this, arguments);
            }
            else{
                this._super.apply(this, arguments);
            }
        },

            //Overrided _on discard for hiding/showing menu item coming after discard
        _onDiscard: function (ev) {
        ev.stopPropagation(); // So that it is not considered as a row leaving
        var self=this;
        this._discardChanges().then(function(result){
                     $(".mode_button").show();
                    $('#ks_dropdown').show();
                    if(self.ks_editable && !$('#mode').is(':checked')){
                     $('#mode').prop('checked', true);
                     }
                        self.ks_reload_list_view()

                });
    },
//      //Overrided this function to hide or show menu items and making toggle button value to true if it is in editable mode
        _onSaveLine: function (ev) {
        var self = this;
        var recordID = ev.data.recordID;
        this.saveRecord(recordID)
            .done(ev.data.onSuccess)
            .fail(ev.data.onFailure)
            .then(function(result){
                $('#ks_dropdown').show();
                    $('.mode_button').show();
                    if(self.ks_editable && !$('#mode').is(':checked')){
                     $('#mode').prop('checked', true);
                    }
                });
            },

        _isEditable: function () {
        return !this.state.groupedBy.length && this.editable;

        },
        ks_reload_list_view: function(){
            if(this.check){
            var ks_update_params = {};
            ks_update_params["modelName"] = this.modelName;
            ks_update_params["context"] = this.renderer.state.context;
            ks_update_params["ids"] = this.renderer.state.res_ids;
            ks_update_params["offset"] = this.renderer.state.offset;
            ks_update_params["currentId"] = this.renderer.state.res_id;
            ks_update_params["selectRecords"] = this.renderer.selection;
            ks_update_params["groupBy"] = this.renderer.state.groupedBy;
            ks_update_params["domain"] = this.renderer.state.domain;
            this.update(ks_update_params);
            }
        },

        // Initialize LVM data in Database
        ks_initialize_lvm_data: function(){
           if(this.check) {
            var self = this;
            var ks_table_width_px = $("table.o_list_view").innerWidth();
            var ks_table_width_per = +(((ks_table_width_px/ $(window).width()) * 100).toFixed(14));
            return this._rpc({
                route: '/ks_lvm_control/create_list_view_data',
                params: {
                    'ks_model': this.modelName,
                    'ks_editable': this.ks_editable,
                    'ks_view_id': this.ksViewID || false,
                    'ks_table_width_per': ks_table_width_per || 99.45,
                    'ks_fields_data': this.ks_fields_data,
                }
            }).then(function(ks_list_view_data){
                self.ks_table_data = {id: false, ks_table_width: ks_table_width_per || 99.45, ks_editable: this.ks_editable};
                self.ks_reset_list_view(ks_list_view_data).then(function(){
                    self.ks_table_data = self.renderer.ks_user_table_result.ks_table_data;
                    self.ks_fields_data = self.renderer.ks_fields_data;
                    self.ks_field_list = Object.values(self.ks_fields_data).sort((a, b) => a.ks_field_order - b.ks_field_order);
                });
            });
           }
        },

        // Update Field Status in LVM DB.
        ks_update_field_data: function(ks_table_data, ks_field_data, ks_reset_renderer){
           if(this.check){
            var self = this;
            if (!self.ks_table_data){
                return self.ks_initialize_lvm_data();
            }

            var ks_reset_renderer = ks_reset_renderer;
            //            Condition to fetch data or not

            var ks_fetch_options = {
                'ks_model': this.modelName,
                'ks_view_id': this.ksViewID || false,
            }

            if (ks_reset_renderer) framework.blockUI();
            return this._rpc({
                route: '/ks_lvm_control/update_list_view_data',
                params: {
                    'ks_table_data': ks_table_data,
                    'ks_fields_data': ks_field_data,
                    'ks_fetch_options': ks_fetch_options,
                }
            }).then(function(ks_list_view_data){
                if (ks_reset_renderer) {
                    self.ks_reset_list_view(ks_list_view_data);
                    framework.unblockUI();
                };
            });
            }
        },

        ks_modeToggle: function(ev) {
            if(this.check) {
            var self = this;
            var ks_table_data_list = [];
            this.ks_editable = ev.target.checked;
            if (this.ks_table_data) {
                this.ks_table_data.ks_editable = ev.target.checked;
                ks_table_data_list = [this.ks_table_data]
            };

            this.ks_update_field_data(ks_table_data_list, [], true).then(function(){
                self.mode = self.ks_editable ? "edit" : "readonly";
                self.renderer.editable = self.ks_editable;
                self.editable = self.ks_editable?"top":false;
            });
            }
        },

        ks_reset_list_view: function(render_params){
           if(this.check){
            var self = this;
            if (render_params) {
                var fields_view = render_params.fields_views[this.viewType];
                var action = this.getParent().getCurrentAction();
                var viewParams = {}
                if (action) {
                    var renderer_state = this.renderer.state;
                    renderer_state.domain = self.renderer.ksBaseDomain;
                    viewParams = {
                        action: this.getParent().getCurrentAction(),
                        hasSelectors: true,
                        modelName: action.res_model,
                        context: renderer_state.context,
                        domain: renderer_state.domain,
                        groupBy: renderer_state.groupedBy || [],
                        searchQuery: {
                            context: renderer_state.context,
                            domain: renderer_state.domain,
                            groupBy: renderer_state.groupedBy || [],
                            orderedBy: renderer_state.orderedBy || [],
                            offset : renderer_state.offset
                        },
                    };
                }
                return self._ks_update_renderer(fields_view, viewParams)
            }

            return $.when();
            }
        },

        ks_remove_popup_domain: function(ks_options) {
                if(this.check){
                var self = this;
                var ks_i;
                var key;
                var key_array;

                if(ks_options.data.ksDiv!==undefined) {
                    key_array = ks_options.data.ksDiv.id.split("_value")
                    key = key_array[0];
                } else {
                    key = event.target.id;
                }

                if(self.renderer.ks_field_domain_dict[key]!==undefined){
                    if(self.renderer.ks_field_domain_dict[key].length === 1 || ks_options.data.ksfieldtype === "date" || ks_options.data.ksfieldtype === "datetime") {
                         delete self.renderer.ks_field_domain_dict[key]
                         for(ks_i = 0;ks_i < self.renderer.ks_key_fields.length; ks_i++) {
                            if(key === self.renderer.ks_key_fields[ks_i]) {
                                   break;
                            }
                    }

                if(ks_options.data.ksDiv!==undefined) {
                        $("#"+ks_options.data.ksDiv.id).remove()
                } else {
                        $("#"+$(ks_options.data.event.target).parent().children()[$(ks_options.data.event.target).parent().children().length-2].id).remove();
                }

                self.renderer.ks_key_fields.splice(ks_i, 1);
                self.ks_remove_popup_flag = true;
                self.Ks_update_advance_search_controller(false);
                }
                else {
                        for(var j = 0; j < self.renderer.ks_field_domain_dict[key].length; j++) {
                            if(self.renderer.ks_field_domain_dict[key][j] !== '|') {
                                if(ks_options.data.ksDiv!==undefined) {
                                    if(self.renderer.ks_field_domain_dict[key][j][2] === ks_options.data.ksDiv.innerText) {
                                       self.renderer.ks_field_domain_dict[key].splice(j,1)
                                       self.renderer.ks_field_domain_dict[key].splice(0, 1);
                                       break;
                                    }
                                } else {
                                        self.renderer.ks_field_domain_dict[key].splice(j,1)
                                        self.renderer.ks_field_domain_dict[key].splice(0, 1);
                                        break;
                                }
                            }
                        }
                        if(ks_options.data.ksDiv!==undefined) {
                            $("#"+ks_options.data.ksDiv.id).remove()
                        } else {
                            $("#"+$(ks_options.data.event.target).parent().children()[$(ks_options.data.event.target).parent().children().length-2].id).remove();
                        }
                        self.ks_remove_popup_flag=true;
                        self.Ks_update_advance_search_controller(false);
                }
            } else {
                    self.ks_remove_popup_flag=true;
                    self.Ks_update_advance_search_controller(false);
            }
            }
        },

        Ks_update_advance_search_controller: function(ks_options) {
            if(this.check) {
            var self = this;
            if(self.ks_remove_popup_flag === true) {
                var ks_advance_search_params = {};
                ks_advance_search_params["modelName"] = self.renderer.state.model;
                ks_advance_search_params["context"] = self.renderer.state.context;
                ks_advance_search_params["ids"] = self.renderer.state.res_ids;
                ks_advance_search_params["offset"] = self.renderer.state.offset;
                ks_advance_search_params["currentId"] = self.renderer.state.res_id;
                ks_advance_search_params["selectRecords"] = self.renderer.selection
                ks_advance_search_params["groupBy"] = self.renderer.state.groupedBy
                self.renderer.ks_field_domain_list = [];

                for(var j = 0;j < self.renderer.ks_key_fields.length; j++) {
                   self.renderer.ks_field_domain_list = self.renderer.ks_field_domain_list.concat(self.renderer.ks_field_domain_dict[self.renderer.ks_key_fields[j]]);
                }
                self.ks_remove_popup_flag=false;
                ks_advance_search_params["ksDomain"] = self.renderer.ks_field_domain_list;
                if(self.renderer.state.domain.length === 0) {
                    self.renderer.ksBaseDomain = []
                }
                if(self.renderer.ksBaseDomain === null && (self.renderer.ksDomain ===null || self.renderer.ksDomain.length===0) && self.renderer.state.domain.length) {
                    self.renderer.ksBaseDomain = self.renderer.state.domain
                }
                if(self.renderer.ksBaseDomain.length !== 0 || self.renderer.ks_field_domain_list.length !== 0 ) {
                    ks_advance_search_params["domain"] = self.renderer.ksBaseDomain.concat(self.renderer.ks_field_domain_list)
                } else {
                    ks_advance_search_params["domain"] = []
                }
                self.renderer.ksDomain = ks_advance_search_params["ksDomain"]
                self.update(ks_advance_search_params,undefined);
            }
            else {
                    var ks_val_flag = false;
                    if(ks_options.data.ks_val){
                       ks_val_flag = ks_options.data.ks_val.trim()!==0
                    } else {
                       ks_val_flag = $('#'+ks_options.data.KsSearchId).val().trim() !== 0
                    }

                    if(Number(ks_val_flag)) {
                    self.ks_advance_search_refresh = true;
                    var ks_search_value = ks_options.data.ks_val || $('#'+ks_options.data.KsSearchId).val().trim();
                    var ks_advance_search_type = ks_options.data.ksfieldtype;
                    var ks_selection_values = [];
                    var ks_advance_search_params ={};
                    self.renderer.ks_field_domain_list=[];
                    self.ks_key_insert_flag = false;
                    var ks_data_insert_flag = false;
                    var ks_value = ks_options.data.KsSearchId.split("_lvm_start_date")
                    ks_advance_search_params["groupBy"] = self.renderer.state.groupedBy
                    ks_advance_search_params["modelName"] = self.renderer.state.model;
                    ks_advance_search_params["context"] = self.renderer.state.context;
                    ks_advance_search_params["ids"] = self.renderer.state.res_ids;
                    ks_advance_search_params["offset"] = self.renderer.state.offset;
                    ks_advance_search_params["currentId"] = self.renderer.state.res_id;
                    ks_advance_search_params["selectRecords"] = self.renderer.selection

                     if(ks_value.length === 1) {
                         ks_value = ks_options.data.KsSearchId.split("_lvm_end_date")
                         if(ks_value.length === 2)
                             ks_options.data.KsSearchId = ks_value[0];
                     }
                     else {
                         ks_options.data.KsSearchId = ks_value[0];
                     }

                     for(var ks_sel_check = 0; ks_sel_check < self.renderer.ks_key_fields.length; ks_sel_check++) {
                         if(ks_options.data.KsSearchId === self.renderer.ks_key_fields[ks_sel_check]) {
                               ks_data_insert_flag = true;
                         }
                     }

                     if((ks_data_insert_flag === false) || (ks_data_insert_flag === true && (ks_advance_search_type === "many2one" || ks_advance_search_type === "many2many"))) {
                           if(!(ks_advance_search_type === "datetime" || ks_advance_search_type === "date")) {
                                if(this.renderer.ks_key_fields.length === 0) {
                                   if(ks_advance_search_type === 'monetary' || ks_advance_search_type === 'integer' || ks_advance_search_type === 'float') {
                                         try{
                                                var currency = self.getSession().get_currency(self.renderer.ks_list_view_data.currency_id);
                                                var formatted_value = fieldUtils.parse.float(ks_search_value || 0, {digits: currency && currency.digits});
                                                ks_search_value  =  formatted_value
                                                self.renderer.ks_key_fields.push(ks_options.data.KsSearchId);
                                            } catch {
                                                    self.do_notify(
                                                    _t("Please enter a valid number")
                                                    );
                                            }
                                   } else {
                                            self.renderer.ks_key_fields.push(ks_options.data.KsSearchId);
                                   }
                                } else {
                                   for(var key_length = 0; key_length < self.renderer.ks_key_fields.length; key_length++) {
                                         if((self.renderer.ks_key_fields[key_length] === ks_options.data.KsSearchId)) {
                                              self.ks_key_insert_flag = true;
                                              break;
                                         }
                                    }
                                   if(!(self.ks_key_insert_flag)) {
                                         if(ks_advance_search_type === 'monetary' || ks_advance_search_type === 'integer' || ks_advance_search_type === 'float') {
                                                 try{
                                                        var currency = self.getSession().get_currency(self.renderer.ks_list_view_data.currency_id);
                                                        var formatted_value = fieldUtils.parse.float(ks_search_value || 0, {digits: currency && currency.digits});
                                                        ks_search_value  =  formatted_value
                                                        self.renderer.ks_key_fields.push(ks_options.data.KsSearchId);
                                                    } catch {
                                                            self.do_notify(
                                                            _t("Please enter a valid number")
                                                            );
                                                    }
                                         } else {
                                            self.renderer.ks_key_fields.push(ks_options.data.KsSearchId);
                                         }
                                   }
                               }
                           }

                     if(ks_advance_search_type === "datetime" || ks_advance_search_type === "date") {
                          if(ks_options.data.ksFieldIdentity === ks_options.data.KsSearchId + '_lvm_start_date lvm_start_date') {
                               self.ks_start_date = ks_search_value;
                               self.ks_start_date_id = ks_options.data.KsSearchId;
                          }else {
                                self.ks_end_date = ks_search_value;
                                self.ks_end_date_id=ks_options.data.KsSearchId
                          }

                          if(ks_advance_search_type==="datetime" || ks_advance_search_type==="date") {
                               if(ks_options.data.ksFieldIdentity === ks_options.data.KsSearchId+'_lvm_end_date lvm_end_date') {
                                    if(self.ks_start_date_id === self.ks_end_date_id) {
                                        self.renderer.ks_field_domain_dict[self.ks_start_date_id] = [[self.ks_start_date_id,'>=', self.ks_start_date], [self.ks_end_date_id,'<=', self.ks_end_date]]
                                        if(self.renderer.ks_key_fields.length === 0) {
                                            self.renderer.ks_key_fields.push(self.ks_start_date_id);
                                        }
                                        else {
                                             for(var key_length = 0;key_length < self.renderer.ks_key_fields.length; key_length++) {
                                                if(!(self.renderer.ks_key_fields[key_length] === ks_options.data.KsSearchId)) {
                                                    self.renderer.ks_key_fields.push(self.ks_start_date_id);
                                                    break;
                                                }
                                             }
                                        }
                                    }
                               }
                          }
                     } else if(ks_advance_search_type === 'selection') {
                          if(ks_search_value === "Select a Selection") {
                                 for(var j=0;j<self.renderer.ks_key_fields.length;j++) {
                                      self.renderer.ks_field_domain_list = self.renderer.ks_field_domain_list.concat(self.renderer.ks_field_domain_dict[self.renderer.ks_key_fields[j]]);
                                 }
                                ks_advance_search_params["ksDomain"] = self.renderer.ks_field_domain_list;
                                if(self.renderer.state.domain.length === 0) {
                                    self.renderer.ksBaseDomain = []
                                }
                                ks_advance_search_params["domain"] = self.renderer.ksBaseDomain.concat(self.renderer.ks_field_domain_list)
                                self.renderer.ksDomain = ks_advance_search_params["ksDomain"]
                                self.update(ks_advance_search_params,undefined);
                          } else {

                                // obtaining values of selection
                                ks_selection_values = self.renderer.state.fields[ks_options.data.KsSearchId].selection;

                                //setting values for selection
                                for(var i = 0; i < ks_selection_values.length; i++) {
                                    if(ks_selection_values[i][1] === ks_search_value) {
                                        ks_search_value = ks_selection_values[i][0];
                                    }
                                }
                                self.renderer.ks_field_domain_dict[ks_options.data.KsSearchId] = [[ks_options.data.KsSearchId,'=', ks_search_value]]
                          }
                     } else if (ks_advance_search_type === "many2one" || ks_advance_search_type === "many2many") {
                            if(self.renderer.ks_field_domain_dict[ks_options.data.KsSearchId] === undefined)
                                 self.renderer.ks_field_domain_dict[ks_options.data.KsSearchId] = [[ks_options.data.KsSearchId, "ilike", ks_search_value]]
                            else
                                 self.renderer.ks_field_domain_dict[ks_options.data.KsSearchId].push([ks_options.data.KsSearchId, "ilike", ks_search_value])

                            if(self.renderer.ks_field_domain_dict[ks_options.data.KsSearchId].length>1) {
                                self.renderer.ks_field_domain_dict[ks_options.data.KsSearchId].unshift("|")
                            }
                            ks_advance_search_params["ids"] = self.initialState.res_id;
                     } else if(ks_advance_search_type === 'monetary' || ks_advance_search_type === 'integer' || ks_advance_search_type === 'float') {
                                        self.renderer.ks_field_domain_dict[ks_options.data.KsSearchId] = [[ks_options.data.KsSearchId,'=', ks_search_value]]

                     } else {
                            self.renderer.ks_field_domain_dict[ks_options.data.KsSearchId] = [[ks_options.data.KsSearchId, "ilike", ks_search_value]]
                     }

                    if(ks_advance_search_type === "datetime" || ks_advance_search_type === "date") {
                        if(ks_options.data.ksFieldIdentity === ks_options.data.KsSearchId+'_lvm_end_date lvm_end_date') {
                             for(var j=0; j < self.renderer.ks_key_fields.length; j++) {
                               this.renderer.ks_field_domain_list = self.renderer.ks_field_domain_list.concat(self.renderer.ks_field_domain_dict[self.renderer.ks_key_fields[j]]);
                        }
                        ks_advance_search_params["ksDomain"] = self.renderer.ks_field_domain_list;
                        if(self.renderer.state.domain.length === 0) {
                            self.renderer.ksBaseDomain = []
                        }
                        ks_advance_search_params["domain"] = self.renderer.ksBaseDomain.concat(self.renderer.ks_field_domain_list)
                        self.renderer.ksDomain = ks_advance_search_params["ksDomain"]
                        self.update(ks_advance_search_params,undefined);
                        self.ks_start_date = undefined;
                        self.ks_end_date = undefined;
                        self.ks_start_date_id = undefined;
                        self.ks_end_date_id = undefined;
                    }
                }
                else {
                       if(ks_advance_search_type === 'monetary' || ks_advance_search_type === 'integer' || ks_advance_search_type === 'float') {
                            if(!(isNaN(ks_search_value))) {
                               for(var j = 0; j < self.renderer.ks_key_fields.length; j++) {
                                  self.renderer.ks_field_domain_list = self.renderer.ks_field_domain_list.concat(self.renderer.ks_field_domain_dict[self.renderer.ks_key_fields[j]]);
                               }
                            ks_advance_search_params["ksDomain"] = self.renderer.ks_field_domain_list;
                            if(self.renderer.state.domain.length === 0) {
                                  self.renderer.ksBaseDomain = []
                            }
                            ks_advance_search_params["domain"] = self.renderer.ksBaseDomain.concat(self.renderer.ks_field_domain_list)
                            self.renderer.ksDomain = ks_advance_search_params["ksDomain"]
                            self.update(ks_advance_search_params,undefined);
                            }
                            else{
                                    if(self.renderer.state.domain.length === 0) {
                                        self.renderer.ksBaseDomain = []
                                    }
                                    ks_advance_search_params["domain"] = self.renderer.ksDomain || []
                                    self.update(ks_advance_search_params,undefined);
                            }
                       } else {
                            for(var j = 0; j < self.renderer.ks_key_fields.length; j++) {
                                  self.renderer.ks_field_domain_list = self.renderer.ks_field_domain_list.concat(self.renderer.ks_field_domain_dict[self.renderer.ks_key_fields[j]]);
                               }
                            ks_advance_search_params["ksDomain"] = self.renderer.ks_field_domain_list;
                            if(self.renderer.state.domain.length === 0) {
                                self.renderer.ksBaseDomain = []
                            }
                            ks_advance_search_params["domain"] = self.renderer.ksBaseDomain.concat(self.renderer.ks_field_domain_list)
                            self.renderer.ksDomain = ks_advance_search_params["ksDomain"]
                            self.update(ks_advance_search_params,undefined);
                       }
                }
            } else {
                      for(var j=0;j<self.renderer.ks_key_fields.length;j++) {
                         self.renderer.ks_field_domain_list = self.renderer.ks_field_domain_list.concat(self.renderer.ks_field_domain_dict[self.renderer.ks_key_fields[j]]);
                      }
                      ks_advance_search_params["ksDomain"] = self.renderer.ks_field_domain_list;
                      if(self.renderer.state.domain.length === 0) {
                            self.renderer.ksBaseDomain = []
                      }
                      ks_advance_search_params["domain"] = self.renderer.ksBaseDomain.concat(self.renderer.ks_field_domain_list)
                      self.renderer.ksDomain = ks_advance_search_params["ksDomain"]
                      self.update(ks_advance_search_params,undefined);
                   }
            }
                    else {
                        self.ks_advance_search_refresh = true;
                        var ks_search_value = $('#'+ks_options.data.KsSearchId).val().trim();
                        var ks_advance_search_type = ks_options.data.ksfieldtype;
                        var ks_selection_values = [];
                        var ks_advance_search_params ={};
                        self.renderer.ks_field_domain_list=[];
                        self.ks_key_insert_flag = false;
                        var ks_data_insert_flag = false;
                        var ks_value = ks_options.data.KsSearchId.split("_lvm_start_date")

                        ks_advance_search_params["modelName"] = self.renderer.state.model;
                        ks_advance_search_params["context"] = self.renderer.state.context;
                        ks_advance_search_params["ids"] = self.renderer.state.res_ids;
                        ks_advance_search_params["offset"] = self.renderer.state.offset;
                        ks_advance_search_params["currentId"] = self.renderer.state.res_id;
                        ks_advance_search_params["selectRecords"] = self.renderer.selection
                        ks_advance_search_params["groupBy"] = []

                        for(var j=0;j<self.renderer.ks_key_fields.length;j++) {
                          self.renderer.ks_field_domain_list = self.renderer.ks_field_domain_list.concat(self.renderer.ks_field_domain_dict[self.renderer.ks_key_fields[j]]);
                        }
                        ks_advance_search_params["ksDomain"] = self.renderer.ks_field_domain_list;
                        if(self.renderer.state.domain.length === 0) {
                            self.renderer.ksBaseDomain = []
                        }
                        ks_advance_search_params["domain"] = self.renderer.ksBaseDomain.concat(self.renderer.ks_field_domain_list)
                        self.renderer.ksDomain = ks_advance_search_params["ksDomain"]
                        self.update(ks_advance_search_params,undefined);
                   }
                }
                }
        },

        ks_searchBar : function(e) {
            if(this.check){
            var ks_input = e.target.value.toUpperCase();
            _.map($(".ks_columns_list").children(), function($field){
                $field.style.display = $field.dataset.ks_columns_name.toUpperCase().indexOf(ks_input) > -1 ? "" : "none";
            })
            }
        },

        ks_confirm_restoreData: function(event) {
            if(this.check){
            var self = this;
            Dialog.confirm(this, _t("Are you sure you want to restore to Odoo default View?"),{
                confirm_callback: function () {
                    self.ks_is_restore_flag = true;
                    self.ksResetLvmData();
                }
            });
            }
        },

        ksResetLvmData: function(){
            if(this.check){
            var self = this;
            if(this.ks_table_data){
                return this._rpc({
                    route: '/ks_lvm_control/ks_reset_list_view_data',
                    params: {
                        'ks_model': this.modelName,
                        'ks_view_id': this.ksViewID || false,
                        'ks_lvm_table_id': this.ks_table_data.id
                    }
                }).then(function(ks_list_view_data){
                    self.ks_table_data = false;
                    self.ks_reset_list_view(ks_list_view_data).then(function(){
                        self.KsResetControllerData();
                    });
                });
            }

            return $.when();
            }
        },

        KsResetControllerData: function(){
            if(this.check){
            var self = this;
            this.ks_table_data = this.renderer.ks_user_table_result.ks_table_data;
            this.ks_fields_data = this.renderer.ks_fields_data;
            this.ks_field_list = Object.values(this.ks_fields_data).sort((a, b) => a.ks_field_order - b.ks_field_order);

            this.ks_lvm_user_mode_data = false;
            if($(".ks_columns").length){
                $(".ks_columns_list").remove();
                $(".ks-text-center").remove();
                var $ks_column_list = QWeb.render("ks_list_view_fields_selection_list",{widget:this});
                $(".ks_columns").append($ks_column_list);
                self._ks_init_sortable();

            }
            this.ks_editable = this.renderer.mode!=="readonly";
            $("#mode").prop('checked', this.ks_editable);
            this.editable= this.mode==="edit" ? "top" : false;
            }
        },

        _onKsListHeaderResize: function(option){
            if(this.check){
            var self = this;
            var data = option.data || {};
            var ks_to_update_field_data = [];

            var table_width = $("table.o_list_view").innerWidth();
            if(self.ks_table_data) self.ks_table_data.ks_table_width = +(((table_width/ $(window).width()) * 100).toFixed(14));
            var ks_table_data = self.ks_table_data ? [self.ks_table_data] : [];

            _.each($('.tableFloatingHeaderOriginal th'), function(field){
                var ks_field_data = self.ks_fields_data[$(field).data().name];
                if(ks_field_data){
                    ks_field_data.ks_width = table_width > 0 ? +((($(field).innerWidth() * 100) / table_width).toFixed(14)) : 0.0;
                    ks_to_update_field_data.push(ks_field_data);
                }
            });

            self.ks_update_field_data(ks_table_data, ks_to_update_field_data, false);
            if (self.ks_table_data) self.ks_reload_list_view();
            }
        },

        _onKsFieldActiveClick: function(event){
            if(this.check){
            event.stopPropagation();
            var self = this;

            if(session.ks_toggle_color) {
                    $("input:checked + .ks_slider").css("background-color",session.ks_toggle_color);
                    $("input:not(:checked) + .ks_slider").css("background-color","");
                 }
            var ks_field_data = this.ks_fields_data[event.target.dataset.field_name];
            ks_field_data.ksShowField = event.target.checked;
            self.ks_update_field_data([],[ks_field_data], true)
            }
        },

        _onKsSpanFieldEditableClick: function(event){
            if(this.check){
            event.stopPropagation();
            var self = this;
            var ks_field_id = event.target.dataset.fieldId;
            var $field_span_el = $(event.target);
            var $field_input_el = $('input.ks_editable[data-field-id=' + ks_field_id + ']');
            var name = this.ks_fields_data[ks_field_id].ks_columns_name;
            $field_input_el.val(name);
            $field_span_el.hide();
            $field_input_el.removeClass("d-none");
            $field_input_el.focus();
            $(".cancel_button").removeClass("d-none");
            }
        },

        _onKsInputFieldEditableFocusout: function(event){
            if(this.check){
            event.stopPropagation();
            var self = this;
            var ks_field_id = event.target.dataset.fieldId;
            var $field_span_el = $('span.ks_editable[data-field-id=' + ks_field_id + ']');
            var $field_input_el = $(event.target)
            var name = this.ks_fields_data[ks_field_id].ks_columns_name;
            var input_val = $field_input_el.val();

            if(input_val.length !== 0){
                $field_span_el.text(input_val);
                self.ks_fields_data_dirty[ks_field_id] = _.extend({}, self.ks_fields_data_dirty[ks_field_id], {
                    ks_columns_name: input_val,
                    id: self.ks_fields_data[ks_field_id].id,
                })
            }
            $field_span_el.show();
            $field_input_el.addClass("d-none");
            }
        },

        _onKsCancelButtonClick: function(event){
            if(this.check){
            event.stopPropagation();
            var self = this;
            _.map(Object.keys(self.ks_fields_data_dirty),function(ks_field_id){
                var $field_span_el = self.$el.find('span.ks_editable[data-field-id=' + ks_field_id + ']');
                var name = self.ks_fields_data[ks_field_id].ks_columns_name;
                $field_span_el.text(name);
            });
            self.ks_fields_data_dirty = {};
            $(".cancel_button").addClass("d-none");
            }
        },

        _onKsHideLvmDropDown: function(event){
            if(this.check){
            event.stopPropagation();
            var self = this;

            // Box Hide Reset View
            $(".cancel_button").addClass("d-none");
            $("#myInput").val("");
            _.map($(".ks_columns_list").children(), function($field){
                $field.style.display = "";
            })

            if (!event.hasOwnProperty("clickEvent")) return false;

            // Handle BS hide : Write Dirty Data
            if(!$(".ks_lvm_dd").has(event.clickEvent.target).length>0){
                if(Object.keys(self.ks_fields_data_dirty).length>0 && !self.ks_is_restore_flag){
                    var ks_update_field_list = [];
                    _.map(self.ks_fields_data_dirty, function(value,key){
                        ks_update_field_list.push(value);
                        self.ks_fields_data[key]['ks_columns_name'] = value['ks_columns_name'];
                    })
                    self.ks_update_field_data([], ks_update_field_list, true).then(function(){
                        self.ks_fields_data_dirty = {};
                    });
                }
                self.ks_is_restore_flag = false;
            }
            return !$(".ks_lvm_dd").has(event.clickEvent.target).length>0;
            }
        },

        _ks_update_renderer: function(fields_view, viewParams){
            if(this.check){
            var self = this;
            var View = view_registry.get(this.viewType);
            var view = new View(fields_view, _.extend({}, viewParams));
            var rendererScrollTop = this.$el.scrollTop();
            var localState = false;
            if (this.renderer && this.renderer.getLocalState) {
                localState = this.renderer.getLocalState();
            }
            var oldRenderer = this.renderer;

            return self._ks_init_renderer(view, this.model, fields_view).then(function (renderer) {
                var defs = [];
                var $ks_fragment = $('<div>', {
                    class: 'ks_view_renderer',
                });
                defs.push(renderer.appendTo($('.ks_lvm_o_content .o_view_controller')));
                return $.when.apply($, defs).then(function(){
                    oldRenderer.destroy();
                    self.renderer = renderer;
                });

            });
            }
        },

        _ks_init_renderer: function(view, model, fields_view){
            if(this.check){
            var self = this;

            var Renderer = view.config.Renderer;
            return $.when(view._loadData(model), ajax.loadLibs(view)).then(function (handle) {
                var model = view.getModel();
                var state = model.get(handle);
                self.handle = handle;
                self.model = model;
                model.setParent(self);
                var params = _.extend({}, view.rendererParams, {
                    noContentHelp: undefined,
                    'ks_lvm_data': fields_view.ks_lvm_user_data || false,
                    'ks_lvm_mode': true,
                });
                var renderer = new Renderer(self, state, params);
                return renderer;
            });
            }
        },

        _ks_init_sortable: function() {
            if(this.check){
            var self = this;
            $( ".ks_columns_list" ).sortable({
                axis: 'y',
                update: function(event, ui) {
                    self._ks_update_fields_order(event, ui);
                }
            });
            if(session.ks_toggle_color) {
                $("input:checked + .ks_slider").css("background-color",session.ks_toggle_color);
            }
            $("#mode").prop('checked', this.ks_editable);
            }
        },

        _ks_update_fields_order(event, ui){
            if(this.check){
            var self = this;
            var sort_counter = 0;
            _.map($(".ks_columns_list").children(), function($field){
                    self.ks_fields_data[$field.dataset.field_name].ks_field_order = sort_counter;
                    sort_counter += 1;
            })
            self.ks_update_field_data([], Object.values(self.ks_fields_data), true);
            }
        },

        _onKsDuplicateRecord : function() {
            if(this.check){
            var self = this;
            this._rpc({
                route: '/ks_lvm_control/ks_duplicate_list_records',
                params: {
                    'ks_model': this.modelName,
                    'ks_record_ids': this.getSelectedIds() || [],
                }
            }).then(function(res){
                $('.copy_button').hide();
                self.reload();
            });
            }
        },


        // Duplicate Record button Hide/Active
        _onSelectionChanged: function (event) {
            if(this.check){
            this._super.apply(this,arguments);
            var ks_button = $('.copy_button');
            this.renderer.selection.length !== 0 ? ks_button.show() : ks_button.hide();
            }
        },

    });

});


