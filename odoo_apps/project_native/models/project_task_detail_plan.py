# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
from lxml import etree

import datetime
from dateutil import tz
import pytz
import time
from string import Template
from datetime import datetime, timedelta
from odoo.exceptions import Warning
from pdb import set_trace as bp

from itertools import groupby
from operator import itemgetter

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)  # Need for message in console.


class ProjectTaskDetailPlan(models.Model):
    _name = 'project.task.detail.plan'

    @api.model
    def _get_type(self):
        value = [
            ('cut', _('Cut of DateTime')),
            ('attendance', _('Attendance')),]
        return value

    @api.one
    @api.depends('resource_id', 'name_att')
    def _compute_name(self):
        self.name = "{} - {}".format(self.name_att or "", self.resource_id.name or "",)

    name = fields.Char("Name", default=_compute_name, compute='_compute_name', readonly=True, Store=True,)

    task_id = fields.Many2one('project.task', 'Task',  readonly=True,)
    type_level = fields.Selection('_get_type',
                                  string='Type',
                                  readonly=True, )

    data_from = fields.Datetime("Date From",  readonly=True,)
    data_to = fields.Datetime("Date To",  readonly=True,)
    duration = fields.Integer(string='Duration',  readonly=True,)
    iteration = fields.Integer(string='iteration',  readonly=True,)
    name_att = fields.Char("Name att", readonly=True,)
    resource_id = fields.Many2one('resource.resource', 'Resource', readonly=True,)

    color_gantt_set = fields.Boolean("Set Color Task", default=True)
    color_gantt = fields.Char(
        string="Color",
        Store=True,
        default="rgba(170,170,13,0.53)",
        compute='_compute_color_gantt'
    )

    schedule_mode = fields.Selection([ ('auto', 'Auto'), ('manual', 'Manual')],
                                     string='Schedule Mode',
                                     default='auto',  readonly=True,)

    data_aggr = fields.Date("Date Aggr.", readonly=True, )

    @api.depends('type_level')
    def _compute_color_gantt(self):
        for plan in self:
            if plan.type_level == "cut":
                plan.color_gantt ="rgba(190,170,23,0.53)"



class ProjectTask(models.Model):
    _name = 'project.task'
    _inherit = 'project.task'

    @api.depends("detail_plan_ids")
    def _compute_detail_plan_count(self):

        for task in self:
            detail_plan_work = 0
            for detail_plan_id in task.detail_plan_ids:
                detail_plan_work = detail_plan_work + detail_plan_id.duration

            task.update({
                'detail_plan_count': len(task.detail_plan_ids),
                'detail_plan_work': detail_plan_work,
            })

    detail_plan_count = fields.Integer(compute='_compute_detail_plan_count', string='Detail plan Count', store=True)
    detail_plan_ids = fields.One2many('project.task.detail.plan', 'task_id', 'Detail Plan', ondelete='cascade')
    detail_plan = fields.Boolean(name="Detail Plan", help="Allow Save Detail Plan", default=False)
    detail_plan_work = fields.Integer(compute='_compute_detail_plan_count', string='Detail plan work', store=True)

    def _add_detail_plan(self, calendar_level):
        task_detail_lines = []

        for level in calendar_level:

            resource_id = False
            if level["res_ids"] and level["res_ids"] != -1:

                resource_id = level["res_ids"]


            value = {
                    "name": level["name"],
                    "type_level": level["type"],
                    "data_from": level["date_from"],
                    "data_to": level["date_to"],
                    "duration": level["interval"].total_seconds(),
                    "iteration": level["iteration"],
                    "name_att": level["name"],
                    "data_aggr": level["date_from"].date(),
                    "resource_id" : resource_id
                }

            task_detail_lines.append((0, 0, value), )
        return task_detail_lines



class Project(models.Model):
    _inherit = "project.project"

    detail_plan = fields.Boolean(name="Detail Plan", help="Allow Save Detail Plan", default=False)
