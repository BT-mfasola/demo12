# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)  # Need for message in console.




class ResourceAps(models.Model):
    _inherit = 'resource.resource'

    resource_task_ids = fields.One2many('project.task.resource.link', 'resource_id', 'Resources')