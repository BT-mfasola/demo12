odoo.define('web_gantt_native.NativeGanttData', function (require) {
    "use strict";



 function CheckReadOnly(check_fieds, parent_fields, record){
        // var self = this;

        var readonly_fields = [];
        _.each(check_fieds, function (field, field_key ) {

            var readonly_status  = false;
            // var check_field = self.parent.fields[field];
            // var check_state = self.BarRecord["state"];

            var check_field = parent_fields[field];
            var check_state = record["state"];

            var states = check_field["states"];

            if (check_state && states ){

                var where_state = [];

                _.each(states, function (state, key) {

                    var param1 = false;
                    var param2 = false;

                    if (state[0].length === 2){

                        param1 = state[0][0];
                        param2 = state[0][1];
                    }

                    if (param1 === 'readonly'){
                       where_state.push({state : key, param: param2 });
                    }

                    if (param2 === true){
                        readonly_status = true
                    }
                });

                var check_readonly = _.findWhere(where_state,{state: check_state});

                if (readonly_status){
                    if (!check_readonly){
                        readonly_status = false
                    }
                }
                else{
                    if (!check_readonly){
                        readonly_status = true
                    }
                }
            }
            else{
                readonly_status = check_field.readonly
            }

         readonly_fields.push({field : field, readonly: readonly_status });

        });
        return readonly_fields;

    }



    return {
        CheckReadOnly : CheckReadOnly,

    }


});