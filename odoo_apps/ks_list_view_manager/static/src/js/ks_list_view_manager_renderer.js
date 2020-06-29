odoo.define('ks_list_view_manager.renderer', function (require) {

"use strict";

var core = require('web.core');
var _t = core._t;
var ListRenderer = require('web.ListRenderer');
var session = require('web.session');
var AbstractView = require('web.AbstractView');
var QWeb = core.qweb;
var BasicController = require('web.BasicController');
var datepicker = require("web.datepicker");
var fieldUtils = require('web.field_utils');
var config = require('web.config');
var pyUtils = require('web.py_utils');
var ks_basic_view = require('web.BasicView');

    ListRenderer.include({

        events: _.extend({}, ListRenderer.prototype.events, {
            "keyup .custom-control-searchbar-advance" : "ks_advance_searchbar",
            "change .custom-control-searchbar-change" : "ks_change_event",
            "click .ks_remove_popup" : "ks_remove_popup_domain",
            'hide.datetimepicker' : function(event){
                this.ks_on_date_filter_change("ks_"+event.target.id);
            }
        }),

        init: function (parent, state, params) {
            var self = this;

            this.ks_lvm_mode = params.ks_lvm_mode || false;
            self.restoreInVisibility = [];
            self.restoreName = [];
            self.restoreColumnsDescription = [];
            self.ks_duplicate_data = [];
            self.ks_call_flag=1;
            self.ks_datepicker_flag=0;
            self._super.apply(this,arguments);

            self.ks_lvm_data = params.ks_lvm_data ? params.ks_lvm_data : false;
            self.ks_user_table_result = params.ks_lvm_data && params.ks_lvm_data.ks_lvm_user_table_result ? params.ks_lvm_data.ks_lvm_user_table_result : false;
            self.ks_list_view_data = params.ks_lvm_data ? params.ks_lvm_data.ks_lvm_user_mode_data : false;
            self.userMode = params.ks_lvm_data ? params.ks_lvm_data.ks_lvm_user_mode_data.list_view_data : false;

            self.ks_fields_data = self.ks_user_table_result.ks_fields_data ? self.ks_user_table_result.ks_fields_data : self.ksComputeFieldData(params.arch, state.fields);
            self.ks_field_domain_dict={}
            self.ks_key_fields=[]
            self.ks_field_domain_list=[]
            self.ksDomain=null;
            self.ksBaseDomain=null
            self.ks_allow_search = true;
            self.ksbaseFlag=false;
            self.ks_trigger_up_flag=false;
            self.ks_focus_flag = false;
            self.ks_blur_flag  = true;
            self.ks_restore_data = false;
            self.ks_autocomplete_data = {};
            self.ks_autocomplete_data_result = {};
            self.ks_refreshed = false;
            self.ks_previous_columns_length;
            self.ks_is_resizer = false;
            self.is_ks_sort_column = false;
            self.ks_styles = [];
            self.ks_restore_data_arch = [];
            self.ks_set_width_flag = false;
            self.ks_set_Width;
            self.ks_one_2many = false;
            self.is_ks_editable_on = false;
            self.is_toggle_event = 0;
            self.ks_is_reloaded = true;
            self.ks_is_restore_flag = false;
            self.ks_avg_width = 0;
            self.ks_odoo_default_header_width = {};

            this.ks_count = 0;
            this.ks_mode_count=0;
        },

        _getNumberOfCols: function () {
            if(!this.ks_lvm_mode) return this._super.apply(this, arguments);
            var ks_columns = this._super();
            ks_columns +=1;

            return ks_columns;
        },

        _renderHeader: function (isGrouped) {
            if(!this.ks_lvm_mode) return this._super.apply(this, arguments);
            var self = this;

            if(self.columns.length) {
                if(self.columns[self.columns.length-1].attrs.name === "activity_exception_decoration") {
                    self.columns.splice(self.columns.length-1,1)
                }
            }
            var $ks_header = self._super(isGrouped);
            self.ks_allow_search = true;
            self.ks_field_popup = {};
            if(self.ksDomain!=null) {
                for(var i=0; i < self.ksDomain.length; i++) {
                    if(!(self.ksDomain[i] === '|')) {
                        if(self.ks_field_popup[self.ksDomain[i][0]] === undefined) {
                            self.ks_field_popup[self.ksDomain[i][0]]=[self.ksDomain[i][2]]
                        } else {
                            self.ks_field_popup[self.ksDomain[i][0]].push(self.ksDomain[i][2])
                        }
                    }
                }
            }
            if(!(this.getParent().$el.hasClass("o_field_one2many")|| this.getParent().$el.hasClass("o_field_many2many")))
                if(this.$el.parents().find(".o_modal_header").length === 0) {
                    for(var ks_colour = 0 ; ks_colour < $ks_header[0].children[0].children.length; ks_colour++) {
                        $($ks_header[0].children[0].children[ks_colour]).addClass("bg-primary")
                        $($ks_header[0].children[0].children[ks_colour]).addClass("ks_wrap");
                    }
                }

            self.ks_call_flag=1;
            if(session.ks_serial_number) {
                var $th = $('<th>').css("width","1");
                $th.addClass("bg-primary")
                $th.addClass("ks_wrap");
            }

            if (self.mode !== 'edit') {
                if(session.ks_serial_number) {
                    if(!(this.getParent().$el.hasClass("o_field_one2many")|| this.getParent().$el.hasClass("o_field_many2many")))
                        $ks_header.find("tr").prepend($th.html('S.No'));
                }

                if(!(this.getParent().$el.hasClass("o_field_one2many")|| this.getParent().$el.hasClass("o_field_many2many")))
                    if(this.$el.parents().find(".o_modal_header").length === 0) {
                        $ks_header.find("tr").addClass("bg-primary");
                    }
            }

            if(self.ks_list_view_data.ks_can_advanced_search === true && self.$el.parents(".o_field_one2many").length === 0 ) {
                var $tr = $('<tr>')
                .append(_.map(self.columns, self.ks_textBox.bind(self)));

                if (self.hasSelectors) {
                    $tr.prepend($('<th>'));
                }
                $tr.addClass('hide-on-modal')

                if(session.ks_serial_number) {
                    $tr.prepend($('<th>'));
                }
            }

            self.ks_field_popup = {}
            $ks_header.append($tr);
            return $ks_header
        },

        _renderView: function () {
            var self = this;
            if(self.ks_list_view_data.ks_can_advanced_search === true && self.$el.parents(".o_field_one2many").length === 0) {
                self.noContentHelp = ''
            }

            return this._super.apply(this, arguments).then(function(){
                if(self.ks_lvm_mode) {
                    const table = self.el.getElementsByTagName('table')[0];
                    if (table) {
                        self.ks_set_width_according_to_result($(table));
                    }
                }
                self.on_custom_attach_callback();

            });

        },

        _renderFooter: function (isGrouped) {
            if(!this.ks_lvm_mode) return this._super.apply(this, arguments);
            var $ks_footer = this._super(isGrouped);
            if(session.ks_serial_number) {
                $ks_footer.find("tr").prepend($('<td>'));
            }
            return $ks_footer;
        },

        _renderGroupRow: function (group, groupLevel) {
           if(!this.ks_lvm_mode) return this._super.apply(this, arguments);
           var $ks_row =  this._super(group, groupLevel);

           if (this.mode !== 'edit' || this.hasSelectors) {
                if(session.ks_serial_number) {
                    $ks_row.find("th.o_group_name").after($('<td>'));
                }
           }

           return $ks_row;
        },

        _renderGroups: function (data, groupLevel) {
            if(!this.ks_lvm_mode) return this._super.apply(this, arguments);
            var self = this;
            var _self = this;
            var result = [];

            groupLevel = groupLevel || 0;

            var $tbody = $('<tbody>');
            _.each(data, function (group) {
                 if (!$tbody) {
                    $tbody = $('<tbody>');
                 }
                 $tbody.append(self._renderGroupRow(group, groupLevel));
                 if (group.data.length) {
                    result.push($tbody);

                    // render an opened group
                    if (group.groupedBy.length) {
                        // the opened group contains subgroups
                        result = result.concat(self._renderGroups(group.data, groupLevel + 1));
                    } else{
                        // the opened group contains records
                        var $ks_records = _.map(group.data, function (ks_record,index) {
                        //the opened group contains records
                            if (_self.mode !== 'edit' || _self.hasSelectors) {
                                if(session.ks_serial_number) {
                                    if(!(self.getParent().$el.hasClass("o_field_one2many") || self.getParent().$el.hasClass("o_field_many2many")))
                                        return self._renderRow(ks_record).prepend($('<th>').html(index+1));
                                } else {
                                    return self._renderRow(ks_record);
                                }
                            } else {
                                return self._renderRow(ks_record);
                            }

                        });
                        result.push($('<tbody>').append($ks_records));
                    }
                    $tbody = null;
                 }
            });
            if ($tbody) {
                result.push($tbody);
            }

            return result;
        },

        _renderRow: function (record) {
            if(!this.ks_lvm_mode) return this._super.apply(this, arguments);
            var $ks_row = this._super.apply(this, arguments);

            if(session.ks_serial_number) {
                if (this.mode !== 'edit' && this.state.groupedBy.length === 0) {

                    var ks_index = this.state.data.findIndex(function(event) {
                        return record.id === event.id
                    })

                    if (ks_index !== -1) {
                         if(!(this.getParent().$el.hasClass("o_field_one2many") || this.getParent().$el.hasClass("o_field_many2many")))
                            $ks_row.prepend($('<th>').html(ks_index+1));
                    }
                }
            }
            return $ks_row;
        },

        _onSelectRecord: function (event) {
            if(!this.ks_lvm_mode) return this._super.apply(this, arguments);
            this._super.apply(this, arguments);
            var checkbox = $(event.currentTarget).find('input');
            var $selectedRow = $(checkbox).closest('tr')

            if($(checkbox).prop('checked')) {
                $selectedRow.addClass('ks_highlight_row');
            }
            else {
                $selectedRow.removeClass('ks_highlight_row')
            }
        },

        _onToggleSelection: function (event) {
            if(!this.ks_lvm_mode) return this._super.apply(this, arguments);
           this._super.apply(this, arguments);
           var ks_is_checked = $(event.currentTarget).prop('checked') || false;
           if(ks_is_checked) {
                this.$('tbody .o_list_record_selector').closest('tr').addClass('ks_highlight_row')
           } else {
                this.$('tbody .o_list_record_selector').closest('tr').removeClass('ks_highlight_row')
           }
        },


        on_custom_attach_callback: function () {
            var self = this;
            self._onRendererDomReady();

            if(session.ks_header_color) this._ks_set_list_view_color(session.ks_header_color);

            var ks_header_children = $(self.$el.find("thead tr.bg-primary")).children();

            //setting header color
            if(this.$el.parents().find(".o_modal_header").length === 0) {
                if(session.ks_header_color) {
                    if(!(this.getParent().$el.hasClass("o_field_one2many")|| this.getParent().$el.hasClass("o_field_many2many"))) {
                        for (var i = 0; i < ks_header_children.length; i++) {
                            ks_header_children[i].style.setProperty("background-color",session.ks_header_color,"important");
                        }
                        var ks_header_search_children = self.$el.find(".ks_advance_search_row")

                        for(var i = 0; i < ks_header_search_children.length; i++) {
                            ks_header_search_children[i].style.setProperty("background-color","#EEEEEE","important");
                        }
                    }
                }
            } else {
                $(this.$el.find("thead tr.bg-primary")).removeClass("bg-primary");
                for(var i =0; i < this.$el.find("thead th.bg-primary").length; i++) {
                    $($(this.$el.find("thead th.bg-primary"))[i]).css("background-color","")
                }
            }

            if(self.$el.find("th.o_many2many_tags_cell").length){
                var ks_many2many_badge_width = self.$el.find(".o_field_widget.o_field_many2manytags .badge .o_badge_text").innerWidth();
                var ks_many2many_tag_width = self.$el.find("th.o_many2many_tags_cell").innerWidth();
                if(ks_many2many_tag_width <= 222){
                    self.$el.find(".o_field_widget.o_field_many2manytags .badge .o_badge_text").css("max-width",String(self.ks_avg_width - 15)+"px");
                    self.$el.find(".o_field_widget.o_field_many2manytags").css("max-width",String(self.ks_avg_width - 15)+"px");
                } else {
                    self.$el.find(".o_field_widget.o_field_many2manytags .badge .o_badge_text").css("max-width",String(ks_many2many_tag_width)+"px");
                    self.$el.find(".o_field_widget.o_field_many2manytags").css("max-width",String(ks_many2many_tag_width)+"px");
                }
            }
        },

        ks_on_date_filter_change: function(ks_widget_key){
            var self = this;
            var ks_date_widget = this[ks_widget_key];

            if(ks_date_widget){
                var target = ks_date_widget.el;
                if(ks_date_widget.getValue()){
                    this.trigger_up("Ks_update_advance_search_renderer",{
                        ksFieldName: target.parentElement.dataset.ksField,
                        KsSearchId: target.parentElement.id,
                        ksfieldtype: target.parentElement.dataset.fieldType,
                        ksFieldIdentity: target.parentElement.dataset.fieldIdentity,
                        ks_val: ks_date_widget.getValue().toISOString(),
                    });

                    if(!(target.parentElement.id.indexOf("_lvm_end_date") > 0)) {
                        $('#'+target.parentElement.id).parent().addClass("ks_date_main");
                        $($('#'+target.parentElement.id).parent().parent().children()[1]).addClass("ks_date_inner");
                        $($($('#'+target.parentElement.id).parent().parent().children()[1])[0]).prop("style","");
                        $($('#'+target.parentElement.id).parent().parent().children()[1]).removeClass("d-none");
                        $($($('#'+target.parentElement.id).parent().parent().children()[1]).children()[0]).removeClass("d-none");
                    }
                };
            }
        },

        // TODO : Find if this can be done in more appropriate way
        _ks_set_list_view_color: function(ks_color){
            if($("tr[class='bg-primary']")){
                for(var i=0; i < $("tr[class='bg-primary']").length; i++) {
                    $("tr[class='bg-primary']")[i].style.setProperty("background-color",session.ks_header_color,"important");
                }
            }

            if($("th[class='bg-primary']")){
                for(var i=0; i < $("th[class='bg-primary']").length; i++) {
                    $("th[class='bg-primary']")[i].style.setProperty("background-color",session.ks_header_color,"important");
                }
            }

            if($("th[class='o_column_sortable bg-primary']")){
                for(var i=0; i < $("th[class='o_column_sortable bg-primary']").length; i++) {
                    $("th[class='o_column_sortable bg-primary']")[i].style.setProperty("background-color",session.ks_header_color,"important");
                }
            }

            if($("th[class='o_list_record_selector bg-primary']")){
                for(var i=0; i < $("th[class='o_list_record_selector bg-primary']").length; i++) {
                    $("th[class='o_list_record_selector bg-primary']")[i].style.setProperty("background-color",session.ks_header_color,"important");
                }
            }

            if($("th[class='o_list_record_delete bg-primary']")){
                for(var i=0; i < $("th[class='o_list_record_delete bg-primary']").length; i++) {
                    $("th[class='o_list_record_delete bg-primary']")[i].style.setProperty("background-color",session.ks_header_color,"important");
                }
            }

            if($("th[class='o_column_sortable o-sort-down bg-primary']")){
                for(var i=0; i < $("th[class='o_column_sortable o-sort-down bg-primary']").length; i++) {
                    $("th[class='o_column_sortable o-sort-down bg-primary']")[i].style.setProperty("background-color",session.ks_header_color,"important");
                }
            }

            if($("th[class='o-sort-up o_column_sortable bg-primary']")){
                for(var i=0; i < $("th[class=' o-sort-up o_column_sortable bg-primary']").length; i++) {
                    $("th[class='o-sort-up o_column_sortable bg-primary']")[i].style.setProperty("background-color",session.ks_header_color,"important");
                }
            }

            var ks_header_search_children = $(this.$el.find("thead tr.hide-on-modal")).children()
            for(var i = 0; i < ks_header_search_children.length; i++) {
                ks_header_search_children[i].style.setProperty("background-color","#EEEEEE","important");
            }
        },

        ks_fetch_autocomplete_data: function (field,type,value,ks_one2many_relation) {
            var self = this;

            return self._rpc({
                model: 'user.mode',
                method: 'ks_get_autocomplete_values',
                args: [self.state.model,field,type,value,ks_one2many_relation],
            })
        },

        ksComputeFieldData: function(arch,fields){
            var ks_field_list = {};
            //            Making Field List
            var sort_counter = arch.children.length;
            _.map(fields, function(x,y){
                    if (y !== "activity_exception_decoration"){
                        ks_field_list[y]= {
                            ks_columns_name:x.string,
                            ksShowField: false,
                            field_name: y,
                            ks_width: 0,
                            ks_field_order: sort_counter
                        }
                    }
            })
            // Assigning visible/invisible from arch
            sort_counter = 0;
            _.map(arch.children,function(x){
                let invis = x.attrs.modifiers.column_invisible || x.attrs.optional === "hide";
                if(ks_field_list.hasOwnProperty(x.attrs.name)){
                    _.extend(ks_field_list[x.attrs.name],{
                        ksShowField: !invis,
                        ks_field_order: sort_counter,
                        ks_columns_name: x.attrs.string || ks_field_list[x.attrs.name].ks_columns_name
                    });
                    sort_counter+=1;
                }else if (x.attrs.name){
                    ks_field_list[x.attrs.name] = {
                        ks_columns_name: x.attrs.string || "Undefined",
                        ksShowField: !invis,
                        field_name: x.attrs.name,
                        ks_width: 0,
                        ks_field_order: sort_counter
                    }
                }
            })
            return ks_field_list;
        },

        ks_textBox: function(node) {
            var self = this;
            if(node.tag === "field") {
                if(self.state.fields[node.attrs.name].store === true && !(self.state.fields[node.attrs.name].type === "one2many" || self.state.fields[node.attrs.name].type === "many2many")) {
                    var ks_name = node.attrs.name;
                    var ks_fields = self.state.fields[ks_name];
                    var ks_selection_values = []
                    var ks_description;
                    var ks_field_type;
                    var $ks_from;
                    var ks_field_identity;
                    var ks_identity_flag=false;
                    var ks_field_id=ks_name;
                    var ks_is_hide = true;
                    var ks_widget_flag = true;
                    if (node.attrs.widget) {
                        ks_description = self.state.fieldsInfo.list[ks_name].Widget.prototype.description;
                    }
                    if(ks_fields) {
                        ks_field_type = self.state.fields[ks_name].type;

                        if(ks_field_type === "selection") {
                            ks_selection_values = self.state.fields[ks_name].selection;
                        }
                        if (ks_description === undefined) {
                            ks_description = node.attrs.string || ks_fields.string;
                        }
                    }

                    var $th = $('<th>').addClass("ks_advance_search_row ");
                    if(ks_field_type === "date" || ks_field_type === "datetime"){
                        if(self.ks_call_flag > 1){
                            $th.addClass("ks_fix_width");
                        }
                    }

                    if(ks_field_type === "date" || ks_field_type === "datetime"){
                         if(!(self.ks_call_flag > 1)) {
                               self.ks_call_flag += 1;
                               $ks_from = self.ks_textBox(node);
                               ks_identity_flag = true
                        }
                        if(self.ks_call_flag == 2 && ks_identity_flag == false) {
                               ks_field_id = ks_name+"_lvm_end_date"
                               ks_field_identity = ks_field_id+" lvm_end_date"
                        } else {
                               ks_field_id = ks_name+"_lvm_start_date"
                               ks_field_identity = ks_field_id+" lvm_start_date"
                        }
                    }

                    var $input =$(QWeb.render("ks_list_view_advance_search", {
                        ks_id : ks_field_id,
                        ks_description : ks_description,
                        ks_type:ks_field_type,
                        ks_field_identifier : ks_field_identity,
                        ks_selection: ks_selection_values
                    }));

                    if((ks_field_type==="date" || ks_field_type==="datetime" ) && (self.ks_call_flag==2 && ks_identity_flag == false)) {
                        if(self.state.domain.length === 0){
                            $input.addClass("d-none");
                            $th.addClass("ks_date_inner");
                        }

                        if(!(self.state.domain.length === 0 )) {
                            if(Object.values(self.ks_field_popup) !== undefined){
                                for(var ks_hide = 0; ks_hide < Object.keys(self.ks_field_popup).length; ks_hide++) {
                                    if((Object.keys(self.ks_field_popup)[ks_hide] === ks_name)){
                                            ks_is_hide=false
                                            break
                                    }
                                }
                                if(self.ksDomain) {
                                    if(ks_is_hide === true) {
                                        $input.addClass("d-none");
                                        $th.addClass("d-none");
                                    }
                                     else{
                                        $th.addClass("ks_date_inner");
                                    }
                                }
                                else {
                                    $input.addClass("d-none");
                                    $th.addClass("d-none");
                                }
                            }
                        }
                    }

                    if(self.ksDomain != null && self.ksDomain.length) {
                        if(self.ksDomain[self.ksDomain.length-1] === self.state.domain[self.state.domain.length-1]) {
                            if(ks_field_type === "date" || ks_field_type === "datetime") {
                                for(var ks_add_span = 0; ks_add_span < Object.keys(self.ks_field_popup).length; ks_add_span++) {
                                    if(Object.keys(self.ks_field_popup)[ks_add_span] === ks_name) {
                                        for(var ks_add_span_inner = 0; ks_add_span_inner < Object.values(self.ks_field_popup)[ks_add_span].length-1; ks_add_span_inner++) {

                                            var $div = $('<div>').addClass("ks_inner_search")
                                            $div.attr('id',ks_name+'_value'+ks_add_span_inner)
                                            var $span = $('<span>');
                                            if(ks_field_type === "datetime") {
                                              $span = $span.addClass("ks_date_chip_ellipsis");
                                            }
                                            $span.attr('id',ks_name+'_ks_span'+ks_add_span_inner)

                                            var $i = $('<i>').addClass("fa fa-times")
                                            $i.addClass('ks_remove_popup');

                                            if(self.ks_call_flag == 2 && ks_identity_flag==false) {
                                                $span.text(Object.values(self.ks_field_popup)[ks_add_span][1])
                                                $span.attr("title",Object.values(self.ks_field_popup)[ks_add_span][1]);
                                                $input.prepend($div);
                                                $input.find("#"+Object.keys(self.ks_field_popup)[ks_add_span]+"_value"+ks_add_span_inner).prepend($i);
                                                $input.find("#"+Object.keys(self.ks_field_popup)[ks_add_span]+"_value"+ks_add_span_inner).prepend($span)
                                            } else {
                                                $input.addClass("ks_date_main");
                                                $span.text(Object.values(self.ks_field_popup)[ks_add_span][0]);
                                                $span.attr("title",Object.values(self.ks_field_popup)[ks_add_span][0]);
                                                $input.prepend($div);
                                                $input.find("#"+Object.keys(self.ks_field_popup)[ks_add_span]+"_value"+ks_add_span_inner).prepend($i);
                                                $input.find("#"+Object.keys(self.ks_field_popup)[ks_add_span]+"_value"+ks_add_span_inner).prepend($span);
                                            }
                                        }
                                    }
                                }
                            }else if(ks_field_type === "selection") {
                                for(var ks_add_span = 0; ks_add_span < Object.keys(self.ks_field_popup).length; ks_add_span++) {
                                    if(Object.keys(self.ks_field_popup)[ks_add_span] === ks_name) {
                                        for(var ks_add_span_inner = 0; ks_add_span_inner < Object.values(self.ks_field_popup)[ks_add_span].length; ks_add_span_inner++) {
                                            var value;
                                            var $div = $('<div>').addClass("ks_inner_search")
                                            $div.attr('id',ks_name+'_value'+ks_add_span_inner)

                                            var $span = $('<span>').addClass("ks_advance_chip");
                                            $span.attr('id',ks_name+'_ks_span'+ks_add_span_inner)
                                            $span.addClass("ks_advance_chip_ellipsis");

                                            var $i = $('<i>').addClass("fa fa-times")
                                            $i.addClass('ks_remove_popup');

                                            for(var sel=0; sel < ks_selection_values.length; sel++) {
                                                if(ks_selection_values[sel][0] === Object.values(self.ks_field_popup)[ks_add_span][ks_add_span_inner]) {
                                                    value = ks_selection_values[sel][1];
                                                }
                                            }

                                            $span.text(value)
                                            $span.attr("title",value);
                                            $input.prepend($div);
                                            $input.find("#"+Object.keys(self.ks_field_popup)[ks_add_span]+"_value"+ks_add_span_inner).prepend($i);
                                            $input.find("#"+Object.keys(self.ks_field_popup)[ks_add_span]+"_value"+ks_add_span_inner).prepend($span)
                                        }
                                    }
                                }
                            }else {
                                   for(var ks_add_span=0; ks_add_span < Object.keys(self.ks_field_popup).length; ks_add_span++) {
                                        if(Object.keys(self.ks_field_popup)[ks_add_span] === ks_name) {
                                            for(var ks_add_span_inner=0;ks_add_span_inner < Object.values(self.ks_field_popup)[ks_add_span].length;ks_add_span_inner++) {

                                                var $div = $('<div>').addClass("ks_inner_search")
                                                $div.attr('id',ks_name+'_value'+ks_add_span_inner)

                                                var $span = $('<span>').addClass("ks_advance_chip");

                                                if(!(ks_field_type === "date" || ks_field_type === "datetime")) {
                                                    $span.addClass("ks_advance_chip_ellipsis");
                                                }


                                                $span.attr('id',ks_name+'_ks_span'+ks_add_span_inner)
                                                var $i = $('<i>').addClass("fa fa-times")

                                                $i.addClass('ks_remove_popup');
                                                if(ks_field_type === 'monetary' || ks_field_type === 'integer' || ks_field_type === 'float') {
                                                    var currency = self.getSession().get_currency(self.ks_list_view_data.currency_id);
                                                    var formatted_value = fieldUtils.format.float(Object.values(self.ks_field_popup)[ks_add_span][ks_add_span_inner] || 0, {digits: currency && currency.digits});
                                                    $span.text(formatted_value);
                                                    $span.attr('title',formatted_value);

                                                } else {
                                                    $span.text(Object.values(self.ks_field_popup)[ks_add_span][ks_add_span_inner])
                                                    $span.attr('title',Object.values(self.ks_field_popup)[ks_add_span][ks_add_span_inner]);
                                                }
                                                 if(!(ks_field_type === 'many2one'|| ks_field_type === 'many2many' || ks_field_type === 'one2many'))
                                                    $input.find('input').removeAttr('placeholder');
                                                $input.prepend($div);
                                                $input.find("#"+Object.keys(self.ks_field_popup)[ks_add_span]+"_value"+ks_add_span_inner).prepend($i);
                                                $input.find("#"+Object.keys(self.ks_field_popup)[ks_add_span]+"_value"+ks_add_span_inner).prepend($span)
                                            }
                                        }
                                   }
                            }
                        }
                    }

                    if(self.ksDomain!=null && self.ksDomain.length) {
                            if(!(self.ksDomain[self.ksDomain.length-1] === self.state.domain[self.state.domain.length-1])) {
                                    delete self.ks_field_domain_dict
                                    delete self.ksDomain
                                    self.ksBaseDomain = []
                                    self.ks_field_domain_dict = {}
                                    self.ks_key_fields.splice(0,self.ks_key_fields.length)
                                    self.ks_field_domain_list.splice(0,self.ks_field_domain_list.length)
                            }
                        }


                    if(ks_field_type === "date" || ks_field_type === "datetime") {
                        for(var i = 0; i < self.state.domain.length; i++) {
                            if(ks_field_identity.split("_lvm_end_date")[0] === self.state.domain[i][0] || ks_field_identity.split("_lvm_start_date")[0] === self.state.domain[i][0]){
                                ks_widget_flag = false
                                break;
                            }
                        }
                    }

                    if(ks_widget_flag && ks_field_type === "date") {
                        var ks_date_picker_widget = new (datepicker.DateWidget)(this);
                        ks_date_picker_widget.appendTo($input.find('.custom-control-searchbar-change')).then((function () {
                            ks_date_picker_widget.$el.addClass("ks_btn_middle_child o_input");
                            ks_date_picker_widget.$el.find("input").attr("placeholder", "Search");
                        }).bind(this));

                        var widget_key = "ks_" + ks_date_picker_widget.el.id;
                        self[widget_key] = ks_date_picker_widget;
                    }


                    if(ks_widget_flag && ks_field_type === "datetime") {
                        var ks_date_picker_widget = new (datepicker.DateTimeWidget)(this);
                        ks_date_picker_widget.appendTo($input.find('.custom-control-searchbar-change')).then((function () {
                            ks_date_picker_widget.$el.addClass("ks_btn_middle_child o_input");
                            ks_date_picker_widget.$el.find("input").attr("placeholder", "Search");
                        }).bind(this));

                        var widget_key = "ks_" + ks_date_picker_widget.el.id;
                        self[widget_key] = ks_date_picker_widget;
                    }


                    if(self.ksDomain!=null && this.ksDomain.length) {
                        if(self.ksDomain.length === self.state.domain.length) {
                            for(var i = 0; i <self.state.domain.length; i++) {
                                if(!(self.state.domain[i] === self.ksDomain[i])) {
                                    self.ksbaseFlag = true
                                }
                            }
                        }

                        if(self.ksbaseFlag === true) {
                            self.ksBaseDomain = self.state.domain
                            self.ksbaseFlag=false
                        }
                    }

                    if((self.ksDomain === null || self.ksDomain ===undefined || self.ksDomain.length === 0) && self.state.domain.length) {
                         self.ksBaseDomain = self.state.domain
                    }
                    if((self.ksDomain === null || self.ksDomain ===undefined || self.ksDomain.length === 0) && self.state.domain.length === 0) {
                        self.ksBaseDomain = self.state.domain
                    }

                    $th.append($input);
                    if(self.ks_call_flag == 2) {
                        $th.append($ks_from);
                        self.ks_datepicker_flag+=1;
                    }
                    if(self.ks_datepicker_flag == 2) {
                        self.ks_call_flag = 1;
                        self.ks_datepicker_flag = 0;
                    }
                } else {
                      var $th = $('<th>').addClass("ks_advance_search_row ");
                }
                return $th;
            }else {
                return $('<th>').addClass("ks_advance_search_row ");;
            }
        },

        ks_advance_searchbar: function(e) {
            // block of code for Autocomplete
            var self = this;
            var ks_field_type = e.currentTarget.dataset.fieldType;
            var ks_field_name = e.currentTarget.dataset.ks_field_id;
            var ks_one2many_relation;
            var ks_input_val = $(e.currentTarget).val();

            if((!(e.keyCode == 8 || e.keyCode ==13)) && $(e.currentTarget).val().length) {

                if(ks_field_type === "one2many") {
                    ks_one2many_relation = self.state.fields[e.currentTarget.id].relation
                }


                self.ks_fetch_autocomplete_data(e.currentTarget.id,ks_field_type,$(e.currentTarget).val(),ks_one2many_relation)
                .then(function(ks_auto_Data){

                    self.ks_autocomplete_data_result = ks_auto_Data

                    if(!(ks_field_type === "date" || ks_field_type === "datetime" || ks_field_type === "selection")) {
                        var ks_unique_data = {}
                        self.ks_autocomplete_data[e.currentTarget.id] = [];

                        if(ks_field_type === 'one2many') {
                            for(var i = 0; i < self.ks_autocomplete_data_result.length; i++) {

                                if(!(ks_unique_data[self.ks_autocomplete_data_result[i]])){
                                    self.ks_autocomplete_data[e.currentTarget.id].push(String(self.ks_autocomplete_data_result[i]));
                                    ks_unique_data[self.ks_autocomplete_data_result[i]] = true;
                                }
                            }
                        } else if(ks_field_type === 'many2many' || ks_field_type === 'many2one'){
                            for(var i = 0; i < self.ks_autocomplete_data_result.length; i++) {

                                if(!(ks_unique_data[self.ks_autocomplete_data_result[i][e.currentTarget.id][1]])){
                                    self.ks_autocomplete_data[e.currentTarget.id].push(String(self.ks_autocomplete_data_result[i][e.currentTarget.id][1]));
                                    ks_unique_data[self.ks_autocomplete_data_result[i][e.currentTarget.id][1]] = true;
                                }
                            }
                        } else {
                            for(var i = 0; i < self.ks_autocomplete_data_result.length; i++) {

                                if(!(ks_unique_data[self.ks_autocomplete_data_result[i][e.currentTarget.id]])){
                                    self.ks_autocomplete_data[e.currentTarget.id].push(String(self.ks_autocomplete_data_result[i][e.currentTarget.id]));
                                    ks_unique_data[self.ks_autocomplete_data_result[i][e.currentTarget.id]] = true;
                                }
                            }
                        }


                        $("#"+e.currentTarget.id).autocomplete({
                            source: self.ks_autocomplete_data[e.currentTarget.id]
                        });
                    }
                });
            }
            if(e.keyCode == 8 && this.ks_allow_search) {
                if(event.target.parentNode.children.length!==1) {
                    this.trigger_up("ks_remove_domain",{"event":e})
                    this.ks_allow_search = false;
                }
            }
            if(e.keyCode == 13 && this.ks_allow_search) {
                this.trigger_up("Ks_update_advance_search_renderer",{ksFieldName: e.currentTarget.dataset.ksField,KsSearchId:e.currentTarget.id,ksfieldtype:e.currentTarget.dataset.fieldType});
                this.ks_allow_search = false;
            }
        },

        ks_change_event: function(e) {
            if(e.currentTarget.dataset.fieldType !== "datetime" && e.currentTarget.dataset.fieldType !== 'date') {
                this.trigger_up("Ks_update_advance_search_renderer",{ksFieldName: e.currentTarget.dataset.ksField,KsSearchId:e.currentTarget.id,ksfieldtype:e.currentTarget.dataset.fieldType,ksFieldIdentity:e.currentTarget.dataset.fieldIdentity});
            }
        },

        ks_remove_popup_domain: function(e) {

            var div =e.currentTarget.closest('.ks_inner_search')
            this.trigger_up("ks_remove_domain",{ksDiv: div,ksfieldtype:e.currentTarget.parentElement.parentElement.children[1].dataset.fieldType,});
        },


        _onRendererDomReady : function () {
            var self = this;
            function sticky(){
                self.$el.find("table.o_list_view").each(function () {
                        $(this).stickyTableHeaders({scrollableArea:  $(".o_content")[0], fixedOffset: 0.1});
                });

                if(!self.state.groupedBy.length) {
                    self.$el.find("table.o_list_view").ksResizableColumns({
                        update: function($col_target) {
                           self.trigger_up('on_ks_list_header_resize', {
                                ks_width: $col_target.parent().innerWidth(),
                                ks_field_name: $col_target.parent().data().name,
                            });
                        }
                    });
                }
            }

            function fix_body(position){
                 $("body").css({
                   'position': position,
                });
            }

            if(self.$el){
//                self.$el.parents('.o_field_one2many').length===0
                if(this.ks_lvm_mode){
                        sticky();
                        fix_body("fixed");
                        $(window).unbind('resize', sticky).bind('resize', sticky);
                        self.$el.css("overflow-x","visible");
                }
                else{
                    fix_body("relative");
                }
            }
            $("div[class='o_sub_menu']").css("z-index",4);
        },

        // setting size of columns
        ks_set_width_according_to_result: function($ks_table) {
            var self = this;
            var ks_fields_data_list = self.getParent().ks_fields_data || false;
            var ks_table_data = self.getParent().ks_table_data || false;
            if(ks_fields_data_list && ks_table_data && ks_table_data.ks_table_width > 0){
                if($ks_table.offset()) {

                    var ks_table_percent = ks_table_data.ks_table_width;
                    var ks_table_pixel = (ks_table_percent/100) * $(window).width();
                    $ks_table.innerWidth(ks_table_pixel);

                    _.each($ks_table.find('th'), function(field){
                        var ks_field_data = ks_fields_data_list[$(field).data().name];
                        if(ks_field_data && parseInt(ks_field_data.ks_width)!==0){
                            var ks_width_pix = (ks_field_data.ks_width * ks_table_pixel) / 100;
                            $(field).width(ks_width_pix);
                        }
                    })
                }

                for(var i = 0; i < $(".ks_advance_search_row").length; i++) {
                    if(self.$el.find(".ks_advance_search_row")[i]){
                        self.$el.find(".ks_advance_search_row")[i].style.setProperty("width","")
                    }
                }

                if(self.ks_one_2many){
                    self.ks_one_2many = false;
                }
            }
        },

    });


});



