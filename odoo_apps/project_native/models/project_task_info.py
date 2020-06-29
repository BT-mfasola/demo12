from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)  # Need for message in console.


class ProjectTaskInfo(models.Model):
    _name = 'project.task.info'

    name = fields.Char("Name")
    task_id = fields.Many2one('project.task', 'Task', ondelete='cascade')
    start = fields.Char("Start")
    end = fields.Char("End")
    left_up = fields.Char("Left Up")
    left_down = fields.Char("Left Down")
    right_up = fields.Char("Right Up")
    right_down = fields.Char("Right Down")
    show = fields.Boolean("Show", default=False)

class ProjectTask(models.Model):
    _name = 'project.task'
    _inherit = 'project.task'

    info = fields.Integer(string='Info', default=False)
    info_ids = fields.One2many('project.task.info', 'task_id', 'Info Value')


    def _task_info_add(self, task, vals, info_name):

        if "info_vals" in task.keys() and task["info_vals"]:
            info_data = task["info_vals"]
            info_data["name"] = info_name
            task_info_lines = [(0, 0, info_data)]
            vals["info_ids"] = task_info_lines
        return vals

    def _task_info_remove(self, info_name):
        domain = [('name', '=', info_name)]
        result = self.env['project.task.info'].sudo().search(domain)
        if result:
            result.unlink()












