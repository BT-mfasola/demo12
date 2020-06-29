# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api

class Project(models.Model):
    _inherit = 'project.project'

    task_count_risk = fields.Integer(compute='_task_count', string='Risk Incident')

    @api.multi
    def _task_count(self):
        for rec in self:
            rec.task_count_risk = self.env['project.task'].search_count([('risk_parent_task_id','in',rec.task_ids.ids)])

    risk_line_ids = fields.One2many(
        'project.risk.line',
        'project_id',
        string='Risk Line',
    )
    
    @api.multi
    def action_view_task(self):
        action = self.env.ref('project_risk_management.action_project_task_incident').read()[0]
        action['domain'] = [('risk_parent_task_id','in',self.task_ids.ids),
        ('is_task_incident', '=', True)]
        return action
   
class ProjectTask(models.Model):
    _inherit = "project.task"

    task_count_risk = fields.Integer(compute='_task_count', string='Task')

    @api.multi
    def _task_count(self):
        for rec in self:
            rec.task_count_risk = self.env['project.task'].search_count([('risk_parent_task_id', 'in', self.ids)])
    
    risk_task_line_ids = fields.One2many(
        'project.task.risk.line',
        'task_id',
        string='Task Risk Line',
        copy=False
    )
    is_task_incident = fields.Boolean(
        string="Task Incident?",
        copy=True,
        default=False,
    )
    risk_task_line_id = fields.Many2one(
        'project.task.risk.line',
        string='Risk Line',
    )
    image = fields.Binary(
        'Incident Photo', 
    )
    risk_parent_task_id = fields.Many2one(
        'project.task',
         string='Orignal Task',
         store=True,
    )

    @api.multi
    def action_view_task(self):
        action = self.env.ref('project_risk_management.action_project_task_incident').read()[0]
        action['domain'] = [('risk_parent_task_id','=',self.id),('is_task_incident', '=', True)]
        return action
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: 