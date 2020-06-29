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


class Project(models.Model):
    _inherit = "project.project"

    @api.model
    def _tz_get(self):
        return [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')]

    @api.model
    def _get_scheduling_type(self):
        value = [
            ('forward', _('Forward')),
            ('backward', _('Backward')),
            ('manual', _('Manual')),
        ]
        return value

    @api.model
    def _get_duration_picker(self):
        value = [
            ('day', _('Day')),
            ('second', _('Second')),
            ('day_second', _('Day Second'))
        ]
        return value

    use_calendar = fields.Boolean(name="Use Calendar",help="Set Calendat in Setting Tab", default=True)

    scheduling_type = fields.Selection('_get_scheduling_type',
                                       string='Scheduling Type',
                                       required=True,
                                       default='forward')

    date_start = fields.Datetime(string='Starting Date',
                                 default=fields.Datetime.now,
                                 help="Date Start for Auto Mode",
                                 index=True, copy=False)

    date_end = fields.Datetime(string='Ending Date', default=fields.datetime.now() + timedelta(days=1),
                               index=True, copy=False)

    task_default_duration = fields.Integer(string='Task Duration', default=86400,
                                           help="Default Task Duration", )

    task_default_start = fields.Integer(string='Task Start (UTC)', default=28800,
                                        help="Default Task Start after midnight, UTC - without Time Zone", )

    task_default_start_end = fields.Char(string='Task Start (tz)', readonly=True, compute='_compute_default_start_end',
                                         help="Default Task Start after midnight, with user Time Zone", )

    # humanize duration
    duration_scale = fields.Char(string='Duration Scale', default='d,h', help="You can set: y,mo,w,d,h,m,s,ms")
    duration_picker = fields.Selection('_get_duration_picker', string='Duration Picker', default=None, help="Empty it is Hide: day and second")
    duration_work_scale = fields.Char(string='Duration Work Scale', default='h', help="You can set: y,mo,w,d,h,m,s,ms")

    tz = fields.Selection(_tz_get, string='Timezone', default=lambda self: self._context.get('tz'),
                          help="Time Zone")
    tz_offset = fields.Char(compute='_compute_tz_offset', string='Timezone offset', invisible=True)

    cp_shows = fields.Boolean(name="Critical Path", help="Critical Path Shows", default=True)
    cp_detail = fields.Boolean(name="Critical Path Detail", help="Critical Path Shows Detail on Gantt", default=False)



    @api.depends('tz')
    def _compute_tz_offset(self):
        for project in self:
            project.tz_offset = datetime.now(pytz.timezone(project.tz or 'GMT')).strftime('%z')

    @api.depends("task_default_start", "task_default_duration")
    def _compute_default_start_end(self):

        for proj in self:

            tz_name = self.env.context.get('tz') or self.env.user.tz
            date_end_str = ''

            if tz_name:
                user_tz = pytz.timezone(tz_name)

                date_start = fields.Datetime.from_string(fields.Datetime.now())
                date_start = date_start.replace(hour=0, minute=0, second=0)
                date_start = date_start + timedelta(seconds=proj.task_default_start)

                date_end = date_start + timedelta(seconds=proj.task_default_duration)

                date_start_tz = date_start.replace(tzinfo=pytz.utc).astimezone(user_tz)
                date_end_tz = date_end.replace(tzinfo=pytz.utc).astimezone(user_tz)

                date_end_str = 'UTC= {} -> {}, TZ= {} -> {}'.format(fields.Datetime.to_string(date_start),
                                                                    fields.Datetime.to_string(date_end),
                                                                    fields.Datetime.to_string(date_start_tz),
                                                                    fields.Datetime.to_string(date_end_tz)
                                                                    )

            proj.task_default_start_end = date_end_str


class ProjectTaskPredecessor(models.Model):
    _name = 'project.task.predecessor'

    @api.model
    def _get_link_type(self):
        value = [
            ('FS', _('Finish to Start (FS)')),
            ('SS', _('Start to Start (SS)')),
            ('FF', _('Finish to Finish (FF)')),
            ('SF', _('Start to Finish (SF)')),

        ]
        return value

    task_id = fields.Many2one('project.task', 'Task', ondelete='cascade')
    parent_task_id = fields.Many2one('project.task', 'Parent Task', required=True, ondelete='restrict',
                                     domain="[('project_id','=', parent.project_id)]")
    type = fields.Selection('_get_link_type',
                            string='Type',
                            required=True,
                            default='FS')

    @api.model
    def _get_lag_type(self):
        value = [
            ('minute', _('minute')),
            ('hour', _('hour')),
            ('day', _('day')),
            ('percent', _('percent')),
        ]
        return value

    lag_qty = fields.Integer(string='Lag', default=0)
    lag_type = fields.Selection('_get_lag_type',
                                string='Lag type',
                                required=True,
                                default='day')

    _sql_constraints = [
        ('project_task_link_uniq', 'unique(task_id, parent_task_id, type)', 'Must be unique.'),

    ]



    @api.multi
    def unlink(self):

        parent_task_id = self.parent_task_id
        res = super(ProjectTaskPredecessor, self).unlink()

        if res:
            search_if_parent = self.env['project.task.predecessor'].sudo().search_count(
                [('parent_task_id', '=', parent_task_id.id)])

            if not search_if_parent:
                parent_task_id.write({
                    'predecessor_parent': 0
                })

        return res



class ProjectTaskNative(models.Model):
    _name = 'project.task'
    _inherit = 'project.task'

    @api.model
    def _get_schedule_mode(self):
        value = [
            ('auto', _('Auto')),
            ('manual', _('Manual')),
        ]
        return value

    @api.model
    def _get_constrain_type(self):
        value = [
            ('asap', _('As Soon As Possible')),
            ('alap', _('As Late As Possible')),
            ('fnet', _('Finish No Earlier Than')),
            ('fnlt', _('Finish No Later Than')),
            ('mso', _('Must Start On')),
            ('mfo', _('Must Finish On')),
            ('snet', _('Start No Earlier Than')),
            ('snlt', _('Start No Later Than')),
        ]
        return value

    @api.model
    def _default_date_end(self):

        date_end = fields.Datetime.from_string(fields.Datetime.now())
        date_end = date_end.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_end + timedelta(days=1)

        if 'default_project_id' in self._context:
            project_id = self._context['default_project_id']

            project = self.env['project.project'].browse(project_id)

            if project.task_default_duration != 0 and project.task_default_start != 0:
                date_end = fields.Datetime.from_string(fields.Datetime.now())
                date_end = date_end.replace(hour=0, minute=0, second=0, microsecond=0)
                date_end = date_end + timedelta(seconds=project.task_default_start + project.task_default_duration)

        return date_end

    @api.model
    def _default_date_start(self):

        date_start = fields.Datetime.from_string(fields.Datetime.now())
        date_start = date_start.replace(hour=0, minute=0, second=0, microsecond=0)
        if 'default_project_id' in self._context:
            project_id = self._context['default_project_id']

            project = self.env['project.project'].browse(project_id)

            if project.task_default_start != 0:
                date_start = date_start + timedelta(seconds=project.task_default_start)

        return date_start



    @api.model
    def _get_fixed_calc_type(self):
        value = [
            ('duration', _('Duration')),
            ('work', _('Work')),

        ]
        return value

    fixed_calc_type = fields.Selection('_get_fixed_calc_type',
                                       string='Calc Type',
                                       required=True,
                                       default='work')

    # link
    predecessor_ids = fields.One2many('project.task.predecessor', 'task_id', 'Links')
    predecessor_count = fields.Integer(compute='_compute_predecessor_count', string='Predecessor Count', store=True)
    predecessor_parent = fields.Integer(compute='_compute_predecessor_count', string='Predecessor parent', store=True)


    # Gantt
    is_milestone = fields.Boolean("Mark as Milestone", default=False)
    on_gantt = fields.Boolean("Task name on gantt", default=False)
    date_finished = fields.Datetime('Done Date')

    # info - autoplanning
    duration = fields.Integer(
        'Duration',
        compute='_compute_duration',
        readonly=True, store=True)

    # scheduler
    schedule_mode = fields.Selection('_get_schedule_mode',
                                     string='Schedule Mode',
                                     required=True,
                                     default='manual')

    # constrain
    constrain_type = fields.Selection('_get_constrain_type',
                                      string='Constraint Type',
                                      required=True,
                                      default='asap')
    constrain_date = fields.Datetime('Constraint Date')

    plan_action = fields.Integer(compute='_compute_plan_action', string='Plan Action', store=True)
    plan_duration = fields.Integer(string='Plan Value', default=86400)

    # redefine default
    date_start = fields.Datetime(string='Starting Date',
                                 default=_default_date_start,
                                 index=True, copy=False)

    date_end = fields.Datetime(string='Ending Date', default=_default_date_end,
                               index=True, copy=False)

    # color

    color_gantt_set = fields.Boolean("Set Color Task", default=False)
    color_gantt = fields.Char(
        string="Color Task Bar",
        help="Choose your color for Task Bar",
        default="rgba(170,170,13,0.53)"
    )

    # humanize duration
    duration_scale = fields.Char(string='Duration Scale', related="project_id.duration_scale", readonly=True, )
    duration_picker = fields.Selection(string='Duration Picker', related="project_id.duration_picker", readonly=True,)
    duration_work_scale = fields.Char(string='Duration Work Scale', related="project_id.duration_work_scale", readonly=True, )


    def update_date_end(self, stage_id):
        #Disable remove (end date) when stage change,
        return {}


    @api.onchange('user_id')
    def _onchange_user(self):
        if self.user_id:
            # self.date_start = fields.Datetime.now()
            # task.detail_plan_ids.unlink()
            pass

    @api.multi
    def _get_summary_date(self):

        for task in self.sorted(key='sorting_level', reverse=True):

            if task.child_ids:

                date_start = []
                date_end = []

                for child in task.child_ids:
                    if child.child_ids:

                        summary_date_start = child.summary_date_start
                        summary_date_end = child.summary_date_end

                        if summary_date_start:
                            date_start.append(summary_date_start)

                        if summary_date_end:
                            date_end.append(summary_date_end)

                    else:

                        if child.date_start:
                            date_start.append(child.date_start)

                        if child.date_end:
                            date_end.append(child.date_end)

                if date_start:
                    task.summary_date_start = min(date_start,
                                                  key=lambda x: x if fields.Datetime.from_string(x) else None)

                if date_end:
                    task.summary_date_end = max(date_end, key=lambda x: x if fields.Datetime.from_string(x) else None)

    summary_date_start = fields.Datetime(compute='_get_summary_date', string="Summary Date Start")
    summary_date_end = fields.Datetime(compute='_get_summary_date', string="Summary Date End")

    p_loop = fields.Boolean("Loop Detected")


    @api.onchange('project_id')
    def _onchange_project(self):
        if hasattr(super(ProjectTaskNative, self), '_onchange_project'):
            if self._origin.id:
                if self.env['project.task.predecessor'].search(
                        ['|', ('task_id', '=', self._origin.id), ('parent_task_id', '=', self._origin.id),
                         (('parent_task_id', '=', self._origin.id))], limit=1):
                    raise UserError(_(
                        'You can not change a Project for task.\nPlease Delete - Predecessor: for parent or child.'))

                if self.search([('parent_id', '=', self._origin.id)], limit=1):
                    raise UserError(_(
                        'You can not change a Project for Task.\nPlease Delete or Remove - sub tasks first.'))

            super(ProjectTaskNative, self)._onchange_project()


    @api.depends("predecessor_ids")
    def _compute_predecessor_count(self):

        for task in self:
            for predecessor in task.predecessor_ids:
                predecessor.parent_task_id.write({
                    'predecessor_parent': 1,
                })

            search_if_parent = self.env['project.task.predecessor'].sudo().search_count(
                [('parent_task_id', '=', task.id)])
            task.update({
                'predecessor_count': len(task.predecessor_ids),
                'predecessor_parent': search_if_parent,
            })



    @api.model
    def scheduler_plan(self, project_id):

        search_project = self.env['project.project'].sudo().search([('id', '=', project_id)], limit=1)
        scheduling_type = search_project.scheduling_type

        if scheduling_type == "manual":
            raise UserError(_(
                'Not work in manual mode. Please set in project: Backwork or Forward'))

        # project_task_scheduler.py
        self._scheduler_plan_start_calc(project=search_project)

        # self.do_sorting(project_id=project_id)

        self._summary_work(project_id=project_id)
        self._scheduler_plan_complite(project_id=project_id, scheduling_type=scheduling_type)

        return True


    def _scheduler_plan_complite(self, project_id, scheduling_type):

        # Calculate data start/stop for project.

        search_tasks = self.env['project.task'].sudo().search([('project_id', '=', project_id)])

        if scheduling_type == "forward":
            date_list_end = []
            for task in search_tasks:
                var_data = {}
                var_data['plan_action'] = False
                task.sudo().write(var_data)

                if task.date_end:
                    date_list_end.append(fields.Datetime.from_string(task.date_end))

            if date_list_end:
                new_prj_date_end = max(date_list_end)
                self.env['project.project'].sudo().browse(int(project_id)).write({
                    'date_end': new_prj_date_end,
                })

        if scheduling_type == "backward":
            date_list_start = []
            for task in search_tasks:
                var_data = {}
                var_data['plan_action'] = False
                task.sudo().write(var_data)

                if task.date_start:
                    date_list_start.append(fields.Datetime.from_string(task.date_start))

            if date_list_start:
                new_prj_date_start = min(date_list_start)
                self.env['project.project'].sudo().browse(int(project_id)).write({
                    'date_start': new_prj_date_start,
                })


    def _summary_work(self, project_id):

        search_tasks = self.env['project.task'].sudo().search(
            ['&', ('project_id', '=', project_id), ('child_ids', '!=', False)])

        for task in search_tasks:
            var_data = {}
            if task.schedule_mode == "auto":
                var_data["date_start"] = task.summary_date_start
                var_data["date_end"] = task.summary_date_end

                if task.summary_date_end and task.summary_date_start:
                    diff = fields.Datetime.from_string(task.summary_date_end) - fields.Datetime.from_string(
                        task.summary_date_start)
                    var_data["plan_duration"] = diff.total_seconds()

                    # var_data["duration"] = diff.total_seconds()

                task.sudo().write(var_data)


    @api.depends("predecessor_ids.task_id", "predecessor_ids.type", "constrain_type", "constrain_date", "plan_duration",
                 "duration", "project_id.scheduling_type", "task_resource_ids.name")
    def _compute_plan_action(self):
        for task in self:
            task.plan_action = True


    @api.depends('date_end', 'date_start')
    def _compute_duration(self):
        for task in self:

            if task.date_end and task.date_start:
                diff = fields.Datetime.from_string(task.date_end) - fields.Datetime.from_string(task.date_start)
                duration = diff.total_seconds()
            else:
                duration = 0.0

            task.duration = duration


    @api.multi
    def unlink(self):

        if self.search([('parent_id', 'in', self.ids)], limit=1):
            raise UserError(_(
                'You can not delete a Parent Task.\nPlease Delete - sub tasks first.'))
        return super(ProjectTaskNative, self).unlink()



    def conv_sec_tofloat(self, sec, type="sec"):

        if type == "sec":
            tde = timedelta(seconds=sec)
        if type == "hrs":
            tde = timedelta(hours=sec)

        return tde.total_seconds() / timedelta(hours=1).total_seconds()


    @api.constrains('parent_id', 'child_ids')
    def _check_subtask_level(self):
        pass
        # for task in self:
        #     if task.parent_id and task.child_ids:
        #         raise ValidationError(_('Task %s cannot have several subtask levels.' % (task.name,)))



