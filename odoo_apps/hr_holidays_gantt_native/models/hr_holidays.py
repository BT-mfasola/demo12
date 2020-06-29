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
from odoo.exceptions import  Warning
from pdb import set_trace as bp

from itertools import groupby
from operator import itemgetter

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__) # Need for message in console.


class HolidaysRequest(models.Model):
    _name = "hr.leave"
    _inherit = ['hr.leave']

    #Sorting
    sorting_seq = fields.Integer(string='Sorting Seq.')
    sorting_level = fields.Integer('Sorting Level', default=0)
    sorting_level_seq = fields.Integer('Sorting Level Seq.', default=0)


    #Gantt
    on_gantt = fields.Boolean("Task name on gantt", default=True)


    @api.model
    def childs_get(self, ids_field_name, ids, fields):

        test = "OK"
        return test



