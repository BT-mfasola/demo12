# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__) # Need for message in console.


class ProjectTaskCriticalPath(models.Model):
    _name = 'project.task'
    _inherit = 'project.task'

    critical_path = fields.Boolean(name="Critical Path", help="is Critical Path", default=False, readonly=True)
    # critical path
    cp_shows = fields.Boolean(string='Critical Path', related="project_id.cp_shows", readonly=True, )
    cp_detail = fields.Boolean(string='Critical Path Detail', related="project_id.cp_detail", readonly=True, )


    def _critical_path_calc(self, task):
        task["critical_path"] = False
        task["info_vals"] = False
        value = {}

        need_key = ["soon_date_start", "soon_date_end", "late_date_start", "late_date_end"]

        if all(key in task for key in need_key):
            if task["late_date_start"] and task["soon_date_start"]:
                soon_date_start = fields.Datetime.from_string(task["soon_date_start"])
                late_date_start = fields.Datetime.from_string(task["late_date_start"])
                start = ((late_date_start - soon_date_start).total_seconds()) / 3600
                value["left_up"] = task["soon_date_start"]
                value["left_down"] = task["late_date_start"]
                value["start"] = "{:.2f}".format(start)
                if start <= 0:
                    task["critical_path"] = True

            if task["late_date_end"] and task["soon_date_end"]:
                soon_date_end = fields.Datetime.from_string(task["soon_date_end"])
                late_date_end = fields.Datetime.from_string(task["late_date_end"])
                end = ((late_date_end - soon_date_end).total_seconds()) / 3600
                value["right_up"] = task["soon_date_end"]
                value["right_down"] = task["late_date_end"]
                value["end"] = "{:.2f}".format(end)
                if end <= 0:
                    task["critical_path"] = True

            if value:
                task["info_vals"] = value

        return task


    # @api.model
    # def critical_path_hide(self, project_id):
    #
    #     test = "OK"
    #     return test





