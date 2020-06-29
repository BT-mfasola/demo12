odoo.define('web_gantt_native.TimeLineArrowDraw', function (require) {
    "use strict";


    function LinkWrapper (prop) {

        var LinkWrapper = $('<div class="gantt_timeline_link_wrapper" class="gantt_timeline_link_wrapper_'+prop.dir+'"></div>');
            LinkWrapper.css({'top': prop.top + "px"});
            LinkWrapper.css({'left': prop.left + "px"});
            LinkWrapper.css({'width': prop.width + "px"});
            LinkWrapper.css({'height': prop.height + "px"});

            if (prop["align_center"]){
                LinkWrapper.css({'text-align': "center"});
                prop.left = prop.left-2;
            }

            if (prop["align"]){
                 LinkWrapper.css({'text-align': "left"});
            }

            if ( !prop["align_center"]  && !prop.align && prop.critical_path){

                    LinkWrapper.css({'box-shadow': "0 0 2px 1px #b4aaaa6e"});
            }

            LinkWrapper.css({'left': prop.left + "px"});
            return LinkWrapper

    }

    function LinkCircle (path) {

        var cycleL = $('<i class="fa fa-circle" style="font-size: 8px;"></i>');
        cycleL.css({'vertical-align': 4 +"px"});



        if (path.critical_path){
            cycleL.css({'color': '#f36952'});
        }else{
            cycleL.css({'color': path.color});
        }


        return cycleL;
    }

    function LinkLine (prop, type ) {

        var Px = $('<div class="gantt_timeline_link_'+prop.dir+'"></div>');

        Px.css({'background-color': prop.color});
        Px.css({'width': prop.width + "px"});
        Px.css({'height': prop.height + "px"});

            // if (prop.critical_path){
            //     Px.css({'box-shadow': "0 0 2px 1px #f30b0b6e"});
            // }
        if (prop.mark) {
            var P_type = $('<div class="gantt_timeline_link_type"></div>');

            if (prop.p_loop){
                P_type.addClass("fa fa-undo");
                P_type.css({'color': '#f39a27'});

            }else{
                P_type.text(prop.type);
                P_type.css({'color': prop.color});
            }

            Px.append(P_type);
        }

        return Px
    }

    function LinkArrow (path) {

        var caret = $('<i class="fa fa-caret-'+path.dir+'" style="font-size: 12px;"></i>');
        caret.css({'vertical-align': 1 +"px"});

        if (path.critical_path){
            caret.css({'color': '#f36952'});
        }else{
            caret.css({'color': path.color});
        }

        return caret
    }

    function LinkStartPoint (prop) {

        var path = {"top": 0, "left": 0, "width": 0, "height": 0, "color": prop.color, "type": prop.type, "dir": 0,
        "align_center" : 1};

        path.critical_path = prop.critical_path;
        path.width = 8;
        path.height = 16;
        path.dir = "S1";
        path.top = prop.from_obj_top + path.width/2 + 2;

        if (prop.type === "FF" || prop.type === "FS") {
            path.left = prop.from_obj_left + prop.margin_stop+2;
        }

        if (prop.type === "SS" || prop.type === "SF") {
            path.left = prop.from_obj_left - prop.margin_start;
        }

        return path;

    }

    function LinkEndPoint(prop) {

        var path = {"top": 0, "left": 0, "width": 0, "height": 0, "color": prop.color, "type": prop.type, "dir": 0,
        "align_center" : 0, "dirY": prop.directionY, "critical_path": prop.critical_path };


        if (prop.type === "FF" || prop.type === "SF") {

            path.left = prop.to_obj_left + prop.margin_stop + 7;
            path.width = 10;
            path.height = 16;
            path.align = 1;
            path.dir = "left";

            if (prop.directionY === "up") {
                path.top = prop.to_obj_top+prop.margin_arrow_down;
            }
            if (prop.directionY === "down") {
                path.top = prop.to_obj_top+prop.margin_arrow_top;
            }

        }


        if (prop.type === "SS" || prop.type === "FS") {

            path.top = prop.to_obj_top;
            path.left = prop.to_obj_left - prop.margin_start -7;
            path.width = 10;
            path.height = 16;
            path.dir = "right";
            path.align = 1;

            if (prop.directionY === "up") {
                   path.top = prop.to_obj_top+prop.margin_arrow_down;
            }
            if (prop.directionY === "down") {
                   path.top = prop.to_obj_top+prop.margin_arrow_top;
            }
        }




        return path;

    }

    function CalcStep(prop, from, to) {

        var step = undefined;

        if (to.top < from.top){
            //go up
            if (to.left - from.left > 10){
                //go right
                if (prop.type === "SS")  {
                    step = ["up", "right"];
                }

                if (prop.type === "SF")  {
                    step = ["up", "right", "up", "left"];
                }

                if (prop.type === "FS") {
                    step = ["up", "right"];
                }


            }

            else{
                //go left

                if (prop.type === "SS")  {
                    step = ["up", "left", "up", "right"];
                }

                if (prop.type === "SF")  {
                    step = ["up", "left"];
                }

                if (prop.type === "FS") {
                    step = ["up", "left","up", "right"];
                }


            }


             if (to.left > from.left ) {


                 if (prop.type === "FF") {
                     step = ["up", "right", "up", "left"];
                 }
             }else{

                 if (prop.type === "FF") {
                     step = ["up", "left"];
                 }
             }

            // if (to.left === from.left){
            //     step = ["up"];
            // }
        }

        if (to.top > from.top ){
            //go down
            if (to.left > from.left){
                //go right

                if (prop.type === "SS")  {
                    step = ["down", "right"];
                }

                if (prop.type === "SF")  {
                    step = ["down", "right", "down", "left"];
                }


                if (prop.type === "FS") {
                    step = ["down", "right"];
                }
                if (prop.type === "FF") {
                    step = ["down", "right", "down", "left"];
                }
            }

            else{
                //go left

                if (prop.type === "SS")  {
                    step = ["down", "left", "down", "right"];
                }

                if (prop.type === "SF")  {
                    step = ["down", "left"];
                }

                if (prop.type === "FS") {
                    step = ["down", "left","down", "right"];
                }
                if (prop.type === "FF") {
                    step = ["down", "left"];
                }

            }
        }

        return step;

    }

    function CalcPath(prop, from, to, dir, step, mark) {

         var path = {"top": 0, "left": 0, "width": 0, "height": 0, "color": prop.color, "type": prop.type, "dir": 0,
        "align_center" : 0, "mark" : mark};

         path.critical_path = prop.critical_path;
         path.p_loop = prop.p_loop;


         if (path.critical_path){
             path.color = '#f36952';
             // prop.color = '#9a0b02';
         }

         // var margin_to_top = 10;
        var k_lft = 4;

        if (dir === "up"){

            if (to) {

                if (step === 0) {
                    path.top = to.top + 7;
                    path.left = from.left + 3;
                    path.height = (from.top - path.top) + 4;
                } else{

                    path.top = to.top+7;
                    path.left = to.left - 7;
                    if (prop.type === "FF" || prop.type === "SF"){
                        path.left = to.left + 10;
                    }

                    path.height = (from.top - path.top) + 2;
                }

                path.width = prop.line_size;

            } else{

                path.top = from.top - 10;
                path.left = from.left + 3;
                path.width = prop.line_size;
                path.height = 20;

            }
        }

        if (dir === "down"){

            if (to) {

                if (step === 0) {
                    path.top = from.top+10;
                    path.left = from.left + 3;

                    path.height = (to.top - path.top) + 7;
                } else{
                    path.top = from.top;
                    path.left = to.left - 7;
                    if (prop.type === "FF" || prop.type === "SF"){
                        path.left = to.left + 10;
                    }

                    path.height = (to.top - path.top) + 7;
                }

                path.width =  prop.line_size;


            } else{
                path.top = from.top+10;
                path.left = from.left+ 3;
                path.width = prop.line_size;
                path.height =  10;
            }




        }


        if (dir === "right"){

            if (to) {
                path.top = from.top;
                if (prop.directionY === "down") {
                    path.top = from.top + from.height;
                }


                path.left = from.left;


                if (step === 0){
                    path.width = (to.left - from.left);
                } else{
                    path.width = (to.left - from.left) + 10;
                }

                if (path.width < 0) {
                    path.width = 0
                }


                path.height = prop.line_size;


            }

        }


        if (dir === "left"){


            if (to) {

                path.top = from.top;
                if (prop.directionY === "down") {
                    path.top = from.top + from.height;
                }


                path.left = to.left - 7;
                if (prop.type === "FF" || prop.type === "SF"){
                    path.left = to.left + 10;
                }
                if (step === 0){
                    path.left = to.left;
                }


                path.width = (from.left - path.left) + 2;
                path.height = prop.line_size;

            }
            else{
                path.top = from.top+5;
                path.left =  from.left + k_lft;
                path.width = prop.line_size;
                path.height =  10;
            }




        }

        return path;

    }


    function drawLink (from_obj, to_obj, type) {

        //FS
        var prop = {
            "from_obj_left": 0,

            "to_obj_left": 0,

            "to_obj_top": 0,
            "from_obj_top": 0,

            "link_dif": 0,
            "color": 0,
            "directionX" : 0,
            "directionY" : 0,
            "type": type
        };

        if (type === "FS") {
            prop.from_obj_left = from_obj.task_stop_pxscale;
            prop.to_obj_left = to_obj.task_start_pxscale;

            prop.to_obj_top = to_obj.y;
            prop.from_obj_top = from_obj.y;

            prop.link_dif = 55;
            prop.color = '#7a7a7a';

        }

        //SS
        if (type === "SS") {
            prop.from_obj_left = from_obj.task_start_pxscale;
            prop.to_obj_left = to_obj.task_start_pxscale;

            prop.to_obj_top = to_obj.y;
            prop.from_obj_top = from_obj.y;

            prop.link_dif = 20;

            prop.color = '#63cbe9';
        }

        //FF
        if (type === "FF") {
            prop.from_obj_left = from_obj.task_stop_pxscale;
            prop.to_obj_left = to_obj.task_stop_pxscale;

            prop.to_obj_top = to_obj.y;
            prop.from_obj_top = from_obj.y;

            prop.link_dif = 20;

            prop.color = '#4cd565';
        }

        //SF
        if (type === "SF") {
            prop.from_obj_left = from_obj.task_start_pxscale;
            prop.to_obj_left = to_obj.task_stop_pxscale;

            prop.to_obj_top = to_obj.y;
            prop.from_obj_top = from_obj.y;

            prop.link_dif = 20;

            prop.color = '#d08d73';
        }

        //directionX
        prop.directionX = "right"; //X = RIGHT
        if ((prop.to_obj_left - prop.from_obj_left) <= prop.link_dif) { //X = LEFT
            prop.directionX = "left";
        }

        //directionY
        prop.directionY = "up"; //Y = UP
        if (prop.to_obj_top > prop.from_obj_top) { //Y = DOWN
            prop.directionY = "down";
        }

        //Critical path
        prop.critical_path = undefined;
        if (from_obj.critical_path && to_obj.critical_path && from_obj.cp_shows){

            prop.critical_path = 1
        }

        prop.p_loop = undefined;
        // if (from_obj.p_loop || to_obj.p_loop){
        //
        //     prop.p_loop = 1
        // }
        if (to_obj.p_loop){

            prop.p_loop = 1
        }


        var LinkWrapperR = [];

        prop["line_size"] = 2;
        prop["margin_stop"] = 5;
        prop["margin_start"] = 12;
        prop["circle_width"] = 8;
        prop["circle_height"] = 16;
        prop["margin_arrow_down"] = 5;
        prop["margin_arrow_top"] = 5;


        var s1 = LinkStartPoint(prop);
        var LinkWrapperS1 = LinkWrapper(s1);
        var S1_cicrcle = LinkCircle(s1);
        LinkWrapperS1.append(S1_cicrcle);
        LinkWrapperR.push(LinkWrapperS1);

        var e1 = LinkEndPoint(prop);
        var LinkWrapperE1 = LinkWrapper(e1);
        var E1_arrow = LinkArrow(e1);

        LinkWrapperE1.append(E1_arrow);
        LinkWrapperR.push(LinkWrapperE1);

        var steps = CalcStep(prop, s1, e1 );

        var paths = [];

        if (steps){

            var steps_i = steps.length;

            if (steps_i === 4){

                paths.push(CalcPath(prop, s1, undefined, steps[0], 0));
                paths.push(CalcPath(prop, paths[0], e1, steps[1], 1, true));
                paths.push(CalcPath(prop, paths[1], e1, steps[2], 2));
                paths.push(CalcPath(prop, paths[2], e1, steps[3], 0));
            }

            if (steps_i === 3){
                paths.push(CalcPath(prop, s1, undefined, steps[0], 0));
                paths.push(CalcPath(prop, paths[0], e1, steps[1], 1, true));
                paths.push(CalcPath(prop, paths[1], e1, steps[2], 0));
            }

            if (steps_i === 1){
                paths.push(CalcPath(prop, s1, e1, steps[0], 0, true));
            }

            if (steps_i === 2){
                paths.push(CalcPath(prop, s1, e1, steps[0], 0,true));
                paths.push(CalcPath(prop, paths[0], e1, steps[1], 0));
            }

            _.each(paths, function(path) {

                LinkWrapperR.push(LinkWrapper(path).append(LinkLine(path)));

            })

        }


        return LinkWrapperR

    }


    return {drawLink: drawLink };

});
