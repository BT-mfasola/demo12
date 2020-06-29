odoo.define('ks_odoo11_web_listview_sticky_header.stick_header', function (require) {
'use strict';
    var ListView = require('web.ListRenderer');
    var ks_session = require('web.session');

    var old_render = ListView.prototype._renderView;
    ListView.prototype._renderView = function(){
        var  $self=this;
        var res = old_render.call(this);
        var o_content_area = $(".o_content")[0];


        function sticky(){
            $self.$el.find("table.o_list_view").each(function () {
                    $(this). ({scrollableArea: o_content_area, fixedOffset: 0.1});
                        $self.$el.find('table').resizableColumns();
               });
           }

        function fix_body(position){
             $("body").css({
               'position': position,
            });
        }


        if(this.ks_lvm_mode)){
                sticky();
                fix_body("fixed");
                $(window).unbind('resize', sticky).bind('resize', sticky);
                this.$el.css("overflow-x","visible");
        }
        else{
            fix_body("relative");
        }

        var ks_header_children = $(this.$el.find("thead tr.bg-primary")).children();
        if(ks_session.ks_header_color) {
            for (var i = 0; i < ks_header_children.length; i++) {
                        ks_header_children[i].style.setProperty("background-color",ks_session.ks_header_color,"important");
            }
            var ks_header_search_children = $(this.$el.find("thead tr.hide-on-modal")).children()

            for(var i = 0; i < ks_header_search_children.length; i++) {
                ks_header_search_children[i].style.setProperty("background-color","#EEEEEE","important");
            }
        }

        $("div[class='o_sub_menu']").css("z-index",4);

        var ks_rev_index = 0;

        $self.ks_set_width_according_to_result();

        $self.ks_is_resizer = false;
        $self.is_ks_sort_column = false;

        var ks_header_children = $self.$el.find("thead tr.bg-primary").children();
        // setting header color
        if(ks_session.ks_header_color) {
            for (var i = 0; i < ks_header_children.length; i++) {
                ks_header_children[i].style.setProperty("background-color",ks_session.ks_header_color,"important");
            }
            var ks_header_search_children = $self.$el.find(".ks_advance_search_row")

            for(var i = 0; i < ks_header_search_children.length; i++) {
                ks_header_search_children[i].style.setProperty("background-color","#EEEEEE","important");
            }
        }

        $self.ks_restore_data_flag = false;
        $self.ks_styles = [];
        // setting minimum width of the columns
        return res;
    }
});
