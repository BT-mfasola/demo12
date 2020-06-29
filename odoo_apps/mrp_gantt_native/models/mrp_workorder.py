# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
import math
from lxml import etree

_logger = logging.getLogger(__name__) # Need for message in console.


class MrpWorkorder(models.Model):
    _name = "mrp.workorder"
    _inherit = ['mrp.workorder']

    #Sorting
    sorting_seq = fields.Integer(string='Sorting Seq.')
    sorting_level = fields.Integer('Sorting Level', default=0)
    sorting_level_seq = fields.Integer('Sorting Level Seq.', default=0)


    #Gantt
    is_milestone = fields.Boolean("Mark as Milestone", default=False)
    on_gantt = fields.Boolean("Task name on gantt", default=False)

    #MRP

    duration_gantt = fields.Integer(
        'Gantt Duration', compute='_float_time_convert',
        readonly=True, store=True)

    @api.one
    @api.depends('duration')
    def _float_time_convert(self):

        val_m = int(math.floor(self.duration)*60)
        val_s = int(round((self.duration % 1) * 60))
        self.duration_gantt = val_m + val_s


    @api.model
    def childs_get(self, ids_field_name, ids, fields):

        test = "OK"
        return test



