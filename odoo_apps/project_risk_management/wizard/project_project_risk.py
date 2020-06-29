# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

from odoo import models,fields,api,_

class ProjectRiskTask(models.TransientModel):
    _name = 'project.project.risk.incident'

    @api.model
    def _default_project(self):
        project_task = self.env['project.task'].browse(self._context.get('active_id'))
        if project_task:
            return project_task.project_id.id
    
    risk_task_image = fields.Binary(
        'Incident Photo', 
    )
    description = fields.Text(
        string='Description',
        required=True
    )
    name = fields.Char(
        string='Risk Incident', 
        required=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Assigned to',
        default=lambda self: self.env.uid,
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        default=_default_project,
        required=True
    )
  

    @api.multi
    def create_project_risk_incedent(self):
        for rec in self:
            active_id = rec._context.get('active_id')
            task_vals = {
            'name':rec.name,
            'project_id': rec.project_id.id,
            'is_task_incident':True,
            'image':rec.risk_task_image,
            'description':rec.description,
            }
            task = self.env['project.task'].create(task_vals)
            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
   

     
        