# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

from datetime import datetime, timedelta



_logger = logging.getLogger(__name__)  # Need for message in console.


class ProjectTaskNativeSchedulerCalendar(models.Model):
    _name = 'project.task'
    _inherit = 'project.task'


    # Resource + calendar + leave
    def make_res_cal_leave(self, task_resource_ids, t_params, task_ids):

        project = t_params["project"]
        attendance_ids = t_params["attendance_ids"]
        leave_ids = t_params["leave_ids"]
        cal_id = str(project.resource_calendar_id.id)
        task_res = []


        attendance_ids = self.add_attendance(project.resource_calendar_id, attendance_ids)
        leave_ids = self.add_leave(project.resource_calendar_id, leave_ids)

        if not task_resource_ids:
            task_res.append({
                "calendar_id": cal_id,
                "resource_id": -1,
                "load_factor": 1.0,
                "load_control": "no",
                # "load_control": False
            })

        if task_resource_ids:
            attendance_ids, leave_ids, task_res = self.get_leave_for_resource(task_res, task_resource_ids,
                                                                              attendance_ids, leave_ids, project,
                                                                              task_ids)


        t_params["attendance_ids"] = attendance_ids
        t_params["leave_ids"] = leave_ids

        return cal_id, task_res, t_params


    def get_leave_for_resource(self,task_res, task_resource_ids, attendance_ids, leave_ids, project, task_ids):

        for task_resource in task_resource_ids:
            if task_resource.resource_id:

                cal_obj = task_resource.resource_id.calendar_id

                if cal_obj:
                    # fill cache working time
                    self.add_attendance(cal_obj, attendance_ids)
                    # fill cache leave from calendar
                    self.add_leave(cal_obj, leave_ids, task_resource.resource_id)
                    # fill cache leave from allocate time from other tasks
                    self.add_leave_level(cal_obj, task_resource.resource_id, leave_ids, task_ids)

                    task_res.append({
                        "calendar_id": str(cal_obj.id),
                        "resource_id": task_resource.resource_id.id,
                        "load_factor": task_resource.load_factor,
                        "load_control": task_resource.load_control,
                    })

        return attendance_ids, leave_ids, task_res



    # Leave
    def add_leave_append(self, leave_id, leave_ids):

        leave_ids.append(
            {
                "leave_id": str(leave_id.id),
                "calendar_id": str(leave_id.calendar_id.id),
                "resource_id": str(leave_id.resource_id.id or -1),
                "name": leave_id.name,
                "date_from": leave_id.date_from,
                "date_to": leave_id.date_to,
                "flag_task": None,
                "flag_project": None
            })

        return leave_ids



    def add_leave(self, cal_obj, leave_ids, task_resource=None):

        if not task_resource:
            for leave_id in cal_obj.leave_ids:

                cal_leave_search = list(filter(lambda x: x["leave_id"] == str(leave_id.id), leave_ids))

                if len(cal_leave_search) == 0:
                    leave_ids = self.add_leave_append(leave_id, leave_ids)
        else:
            cal_search = list(filter(lambda x: x["calendar_id"] == str(cal_obj.id), leave_ids))

            if len(cal_search) == 0:

                for leave_id in cal_obj.global_leave_ids:
                    if task_resource.id == leave_id.resource_id.id:
                        leave_ids = self.add_leave_append(leave_id, leave_ids)

        return leave_ids



    # Level
    def add_leave_level(self, cal_id, res_id, leave_ids, task_ids):

        dp_records = self.env['project.task.detail.plan'].sudo().search(
            [('resource_id', '=', res_id.id), ('task_id', 'not in', task_ids)])

        for dp_record in dp_records:
            leave_ids.append(
                {
                    "leave_id": "dp{}".format(dp_record.id),
                    "calendar_id": str(cal_id.id),
                    "resource_id": str(res_id.id),
                    "name": dp_record.name,
                    "date_from": fields.Datetime.to_string(dp_record.data_from),
                    "date_to": fields.Datetime.to_string(dp_record.data_to),
                    "flag_task": None,
                    "flag_project": None
                })

        return leave_ids


    # attendance
    def add_attendance(self, cal_obj, attendance_ids):

        cal_res_search = list(filter(lambda x: x["calendar_id"] == str(cal_obj.id), attendance_ids))

        if len(cal_res_search) == 0:

            for att_id in cal_obj.attendance_ids:
                attendance_ids.append(
                    {
                        "calendar_id": str(att_id.calendar_id.id),
                        "display_name": att_id.display_name,
                        "date_from": fields.Date.from_string(att_id.date_from) if att_id.date_from else False,
                        "date_to": fields.Date.from_string(att_id.date_to) if att_id.date_to else False,
                        "hour_from": att_id.hour_from,
                        "hour_to": att_id.hour_to,
                        "dayofweek": str(att_id.dayofweek),
                    })

        return attendance_ids