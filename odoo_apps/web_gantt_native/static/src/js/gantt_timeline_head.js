odoo.define('web_gantt_native.TimeLineHead', function (require) {
"use strict";


var core = require('web.core');
var Widget = require('web.Widget');




var GanttTimeLineHead = Widget.extend({
    template: "GanttTimeLine.head",

    init: function(parent, timeScale, timeType, first_scale, second_scale) {
        this._super(parent);

        this.timeScale = timeScale;
        this.timeType = timeType;

        this.first_scale = first_scale;
        this.second_scale = second_scale;
        this.parent = parent;
        this.TODAY = moment();

       // this.record_id = this.record['id']

    },



    start: function(){

        var self = this;
        var el = self.$el;


        var el_scale_primary = el.find('.task-gantt-scale-primary');
        var el_scale_secondary = el.find('.task-gantt-scale-secondary');




        if (this.timeType == 'year_month') {


            _.each(this.first_scale, function(range_date , rdate){


               // var dm =  moment(rdate).format("YYYY");
               //
               //  var monthScale = self.timeScale*range_date.length;
               //
               //
               //
               //  var div_cell = $('<span class="task-gantt-top-column"></span>');
               //      div_cell.css({ width: monthScale + "px" });
               //      div_cell.append($('<span class="task-gantt-scale-month-text">'+dm+'</span>'));
               //
               //      el_scale_primary.append(div_cell);


                _.each(range_date, function(quarter){

                        var div_cell ='';
                        //
                        // var week_string =  moment(quarter).format("MMM");
                        // div_cell = $('<span class="task-gantt-bottom-column">'+week_string+'</span>');
                        div_cell = $('<span class="task-gantt-bottom-column"></span>');
                        div_cell.css({ width: self.timeScale + "px" });
                        div_cell.css({ 'margin-top': -52 + "px" });
                        el_scale_secondary.append(div_cell);
                });

            });

        }





        if (this.timeType == 'quarter') {


            _.each(this.first_scale, function(range_date , rdate){


               // var dm =  moment(rdate).format("YYYY");
               //
               //  var monthScale = self.timeScale*range_date.length;
               //
               //
               //
               //  var div_cell = $('<span class="task-gantt-top-column"></span>');
               //      div_cell.css({ width: monthScale + "px" });
               //      div_cell.append($('<span class="task-gantt-scale-month-text">'+dm+'</span>'));
               //
               //      el_scale_primary.append(div_cell);


                _.each(range_date, function(quarter){

                        var div_cell ='';

                        // var week_string =  moment(quarter).format("Q");
                        // div_cell = $('<span class="task-gantt-bottom-column">'+week_string+'</span>');
                        div_cell = $('<span class="task-gantt-bottom-column"></span>');
                        div_cell.css({ width: self.timeScale + "px" });

                        div_cell.css({ 'margin-top': -52 + "px" });

                        el_scale_secondary.append(div_cell);
                });

            });


        }



        if (this.timeType == 'month_week') {


            _.each(this.first_scale, function(range_date , rdate){


               // var dm =  moment(rdate).format("YYYY");
               //
               //  var monthScale = self.timeScale*range_date.length;
               //
               //  var div_cell = $('<span class="task-gantt-top-column"></span>');
               //      div_cell.css({ width: monthScale + "px" });
               //      div_cell.append($('<span class="task-gantt-scale-month-text">'+dm+'</span>'));
               //
               //      el_scale_primary.append(div_cell);


                _.each(range_date, function(hour){

                        var div_cell ='';

                        // var week_string =  moment(hour).format("W");
                        //div_cell = $('<span class="task-gantt-bottom-column">'+week_string+'</span>');

                        div_cell = $('<span class="task-gantt-bottom-column"></span>');
                        div_cell.css({ width: self.timeScale + "px" });

                        div_cell.css({ 'margin-top': -52 + "px" });

                        el_scale_secondary.append(div_cell);
                });

            });

        }


        if (this.timeType == 'month_day')
        {


            _.each(this.second_scale, function(day){

                var div_cell ='';

                // div_cell = $('<span class="task-gantt-bottom-column">'+moment(day).date()+'</span>');

                div_cell = $('<span class="task-gantt-bottom-column"></span>');
                div_cell.css({ width: self.timeScale + "px" });

                if (moment(day).isoWeekday() === 6 || moment(day).isoWeekday() === 7){
                    div_cell.addClass('task-gantt-weekend-column');
                }
                self.parent.isTODAYline = false;
                if (moment(day).isSame(self.TODAY, 'day')){
                    div_cell.addClass('task-gantt-today-column');
                    self.parent.isTODAYline = true;
                }

                 div_cell.css({ 'margin-top': -52 + "px" });

                return  el_scale_secondary.append(div_cell);

            });

            // _.each(this.first_scale, function(month){
            //
            //
            //          var monthScale = self.timeScale*month.days;
            //
            //          var div_cell = $('<span class="task-gantt-top-column"></span>');
            //
            //           div_cell.css({ width: monthScale + "px" });
            //
            //          div_cell.append($('<span class="task-gantt-scale-month-text">' + month.year + ' - ' + month.month + '</span>'));
            //
            //          return el_scale_primary.append(div_cell);
            //
            // });

        }


        if (this.timeType === 'day_1hour' ||
            this.timeType === 'day_2hour' ||
            this.timeType === 'day_4hour' ||
            this.timeType === 'day_8hour' ) {



            _.each(this.first_scale, function(range_date , rdate){


               // var dm =  moment(rdate).format("Do MMM dd - YY");
               //
               //  var monthScale = self.timeScale*range_date.length;
               //
               //  var div_cell = $('<span class="task-gantt-top-column"></span>');
               //      div_cell.css({ width: monthScale + "px" });
               //      div_cell.append($('<span class="task-gantt-scale-month-text">'+dm+'</span>'));
               //
               //      el_scale_primary.append(div_cell);


                _.each(range_date, function(hour){

                        var div_cell ='';

                       // var hours_string =  moment(hour).format("HH:mm");
                        div_cell = $('<span class="task-gantt-bottom-column"></span>');
                        // div_cell = $('<span class="task-gantt-bottom-column">'+hours_string+'</span>');
                        div_cell.css({ width: self.timeScale + "px" });

                        if (moment(hour).isoWeekday() === 6 || moment(hour).isoWeekday() === 7){
                            div_cell.addClass('task-gantt-weekend-column');
                        }

                        if (moment(hour).isSame(self.TODAY, 'day')){
                            div_cell.addClass('task-gantt-today-column');
                        }

                        div_cell.css({ 'margin-top': -52 + "px" });
                        el_scale_secondary.append(div_cell);

                });


                }
            );

        }
    },


});

return GanttTimeLineHead;

});