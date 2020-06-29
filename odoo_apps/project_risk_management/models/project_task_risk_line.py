# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

class ProjectTaskRiskLine(models.Model):
    _name = "project.task.risk.line"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'rating.mixin']

    @api.depends(
        'task_id',
        'risk_id',
        'task_id.name',
        'risk_id.name',
    )
    def _compute_name_task(self):
        for line in self:
            line.name = str(line.task_id.name) + '/' + str(line.risk_id.name)

    name = fields.Char(
        string='Title', 
        track_visibility='always', 
        required=True,
        compute="_compute_name_task", 
    )

    task_id = fields.Many2one(
        'project.task',
        string="Task",

    )
    category_id = fields.Many2one(
        'project.risk.category',
        'Category',
        required=True,
    )
    risk_id = fields.Many2one(
        'project.risk',
        'Risk',
        required=True,
    )
    type_id = fields.Many2one(
        'project.risk.type',
        'Risk Type',
        required=True,
    )
    probality = fields.Float(
        string='Probablity(%)',
    )
    response_id = fields.Many2one(
        'project.risk.response',
        'Risk Response',
        required=True,
    )
    description = fields.Char(
        string='Description'
    )
    task_project_id = fields.Many2one(
        'project.project',
        'Project',
        related='task_id.project_id',
    )

    @api.onchange('risk_id')
    def _onchange_risk_line(self):
        for rec in self:
            rec.type_id = rec.risk_id.type_id.id
            rec.response_id = rec.risk_id.response_id.id
            rec.category_id = rec.risk_id.category_id.id
            rec.description = rec.risk_id.name
            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
   
    

