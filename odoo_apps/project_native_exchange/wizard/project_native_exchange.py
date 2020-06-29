
import logging
import base64

from odoo import api, fields, models, _

from datetime import date, datetime, timedelta

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
DATE_LENGTH = len(date.today().strftime(DATE_FORMAT))
DATETIME_LENGTH = len(datetime.now().strftime(DATETIME_FORMAT))

_logger = logging.getLogger(__name__)

import xml.etree.ElementTree as ET


class ProjectNativeExchangeImportTaskLine(models.TransientModel):

    _name = 'project.native.exchange.import.task.line'

    name = fields.Char(string='Field', readonly=True)
    seq_line = fields.Integer(string='Seq.', readonly=True)
    imp_value = fields.Char(string='imp value')
    xml_field = fields.Char(string='xml name', readonly=True)
    xml_value = fields.Char(string='xml value', readonly=True)
    imp_type = fields.Char(string='imp type', readonly=True)
    import_id = fields.Many2one('project.native.exchange.import', 'Import', required=True)

    _order = 'seq_line'

class ProjectNativeExchangeImportPrjLine(models.TransientModel):

    _name = 'project.native.exchange.import.prj.line'

    name = fields.Char(string='Field', readonly=True)
    imp_value = fields.Char(string='imp value')
    xml_field = fields.Char(string='xml name', readonly=True)
    xml_value = fields.Char(string='xml value', readonly=True)
    imp_type = fields.Char(string='imp type', readonly=True)
    import_id = fields.Many2one('project.native.exchange.import', 'Import', required=True, readonly=True)




class ProjectNativeExchangeImport(models.TransientModel):
    _name = "project.native.exchange.import"

    name = fields.Char(string='File Name')
    file_load = fields.Binary(string='XML File')
    project_id = fields.Many2one('project.project', 'Project', readonly=True)
    errors = fields.Text('Errors',  readonly=True)

    seq_xml_task = fields.Integer(string='Seq XML Task', default=0)

    import_project_line_ids = fields.One2many('project.native.exchange.import.prj.line', 'import_id', string='Prj Lines')
    import_task_line_ids = fields.One2many('project.native.exchange.import.task.line', 'import_id',
                                           string='Task Lines')

    def func_mapper(self, value, data):

        exchange_tool = self.env['project.native.exchange.tool']

        if value["func"] == "str":
            return data

        if value["func"] == "str_plus_date":
            return '{} - {}'.format( data, fields.Datetime.now())

        if value["func"] == "int":
            return int(data)

        if value["func"] == "schedule_mode":
            schedule_mode = exchange_tool.xml_schedule_mode(value=data, direct="from_xml")
            return schedule_mode

        if value["func"] == "datetime":
            dt_date = exchange_tool.project_date_tool(value=data, type_con="from_string")
            str_date = fields.Datetime.to_string(dt_date)
            return str_date

        if value["func"] == "bool":
            data_bool = exchange_tool.xml_bool(value=data, direct="from_xml")
            return data_bool

        if value["func"] == "auto_manual":
            data_ma = exchange_tool.xml_auto_manual(value=data, direct="from_xml")
            return data_ma

        if value["func"] == "constraint_type":
            data_constraint_type = exchange_tool.xml_constraint_type(value=data, direct="from_xml")
            return data_constraint_type

        return False

    def parse_project(self, root, nsmap, xml_import=False):

        # Parse - Project
        xml_parse_prj_fields = {
            "name": {"xml": "Name" ,"func" :"str_plus_date"},
            "scheduling_type": {"xml": "ScheduleFromStart", "func": "schedule_mode"},
            "date_start": {"xml": "StartDate", "func": "datetime"},
            "date_end": {"xml": "FinishDate", "func": "datetime"},
        }

        project_model = self.env['project.project']
        project_values = {}

        for key, value in xml_parse_prj_fields.items():

            xml_data = root.find('n:' + value["xml"] + '', namespaces=nsmap)

            if xml_data is not None:
                imp_value = self.func_mapper(value, xml_data.text)

                prj_line_values = {
                    'name': key,
                    'imp_value': '{}'.format(imp_value),
                    'xml_field': value["xml"],
                    'xml_value': xml_data.text,
                    'imp_type': value["func"]

                }

                if not xml_import:
                    self.write({'import_project_line_ids': [(0, 0, prj_line_values)]})

                    # if key == "name":
                    #     self.write({ 'name': '{}'.format(imp_value),})

                if xml_import:
                    project_values[key] = imp_value

        if xml_import:

            if project_values["scheduling_type"] == "backward":
                project_values["date_start"] = None

            if project_values["scheduling_type"] == "forward":
                project_values["date_end"] = None

            project_id = project_model.create(project_values).id

            if project_id:
                self.write({
                    'project_id': project_id,
                })



    def task_get_seq(self, task_obj=None, project_task=None, parent_value=None, parent_before=None):

        if project_task["sorting_level"] > parent_before["sorting_level"]:

            if project_task["sorting_level"] > 1:
                task_obj.write({
                    'parent_id': parent_before["p_id"]
                })

            parent_value["p_id"] = parent_before["p_id"]
            parent_value["sorting_level"] = parent_before["sorting_level"]

            return parent_value

        if project_task["sorting_level"] == parent_before["sorting_level"]:

            if project_task["sorting_level"] > 1:
                task_obj.write({
                    'parent_id': parent_value["p_id"]
                })

            return False

        if project_task["sorting_level"] < parent_before["sorting_level"]:
            parent_value["p_id"] = task_obj.id
            parent_value["sorting_level"] = project_task["sorting_level"]

            return parent_value

        return False



    def parse_task(self, root, nsmap, xml_import=False, project_id=False):

        project_task_model = self.env['project.task']
        exchange_tool = self.env['project.native.exchange.tool']

        xml_parse_task_fields = {
            "0_UID": {"xml": "UID", "func": "int"},
            "0_ID": {"xml": "ID", "func": "int"},
            "name": {"xml": "Name", "func": "str"},
            "active": {"xml": "Active", "func": "bool"},
            "schedule_mode": {"xml": "Manual", "func": "auto_manual"},
            "0_OutlineNumber": {"xml": "OutlineNumber", "func": "str"},
            "sorting_level": {"xml": "OutlineLevel", "func": "int"},
            "date_start": {"xml": "Start", "func": "datetime"},
            "date_end": {"xml": "Finish", "func": "datetime"},
            "color_gantt_set": {"xml": "ColorGanttSet", "func": "bool"},
            "color_gantt": {"xml": "ColorGantt", "func": "str"},
            "is_milestone": {"xml": "Milestone", "func": "bool"},
            "on_gantt": {"xml": "OnGantt", "func": "bool"},
            "constrain_type": {"xml": "ConstraintType", "func": "constraint_type"},
            "constrain_date": {"xml": "ConstraintDate", "func": "datetime"},
        }

        xml_tasks = root.find('n:Tasks', namespaces=nsmap)
        counter = 0
        project_tasks_list = []
        predecesors_tasks = {}
        tags_project = {}
        stage_task = {}

        for xml_task in list(xml_tasks):

            counter += 1
            project_task_values = {}

            # Task Data
            for key, value in xml_parse_task_fields.items():  # get data by fields from xml

                xml_data = xml_task.find('n:' + value["xml"] + '', namespaces=nsmap)

                if xml_data is not None:
                    imp_value = self.func_mapper(value, xml_data.text)

                    task_line_values = {
                        'name': key,
                        'imp_value': '{}'.format(imp_value),
                        'xml_field': value["xml"],
                        'xml_value': xml_data.text,
                        'imp_type': value["func"],
                        'seq_line': counter,
                    }

                    if not xml_import and counter == self.seq_xml_task:
                        self.write({'import_task_line_ids': [(0, 0, task_line_values)]})

                    if xml_import:
                        project_task_values[key] = imp_value

            if xml_import:
                project_tasks_list.append(project_task_values)

                # Tag

                xml_tag_ids = xml_task.findall('n:TaskTag', namespaces=nsmap)
                if xml_tag_ids:
                    xml_parse_tag_ids_fields = {
                        "Tag_UID": {"xml": "TagUID", "func": "int"},
                        "name": {"xml": "TagName", "func": "str"},
                        "color": {"xml": "TagColor", "func": "int"},

                    }

                    tag_ids_values = []
                    for xml_tag_id in list(xml_tag_ids):
                        tag_ids_data = {}
                        for key, value in xml_parse_tag_ids_fields.items():  # get data by fields from xml
                            tag_id_data = xml_tag_id.find('n:' + value["xml"] + '', namespaces=nsmap)
                            if tag_id_data is not None:
                                tag_id_value = self.func_mapper(value, tag_id_data.text)
                                tag_ids_data[key] = tag_id_value

                        tag_ids_values.append(tag_ids_data)

                    tags_project[project_task_values["0_UID"]] = tag_ids_values

                # PredecesorLink

                xml_predecesor_links = xml_task.findall('n:PredecessorLink', namespaces=nsmap)
                if xml_predecesor_links:

                    xml_parse_predecesor_fields = {
                        "P_UID": {"xml": "PredecessorUID", "func": "int"},
                        "type": {"xml": "Type", "func": "int"},
                        "lag_qty": {"xml": "LinkLag", "func": "int"},
                        "lag_type": {"xml": "LagFormat", "func": "int"},
                    }

                    predecesor_values = []
                    for xml_predecesor_link in list(xml_predecesor_links):

                        predecesors_data = {}
                        for key, value in xml_parse_predecesor_fields.items():  # get data by fields from xml

                            xml_predecesor_data = xml_predecesor_link.find('n:' + value["xml"] + '', namespaces=nsmap)

                            if xml_predecesor_data is not None:
                                xml_predecesor_value = self.func_mapper(value, xml_predecesor_data.text)

                                predecesors_data[key] = xml_predecesor_value

                        predecesor_values.append(predecesors_data)

                    predecesors_tasks[project_task_values["0_UID"]] = predecesor_values

                # Stage
                xml_stageid = xml_task.findall('n:StageID', namespaces=nsmap)
                if xml_stageid:
                    xml_parse_stage_fields = {
                        "id": {"xml": "ID", "func": "int"},
                        "name": {"xml": "Name", "func": "str"}
                    }
                    stage_data = {}
                    for xml_stage_id in xml_stageid:
                        for key, value in xml_parse_stage_fields.items():  # get data by fields from xml

                            xml_stage_data = xml_stage_id.find('n:' + value["xml"] + '', namespaces=nsmap)

                            if xml_stage_data is not None:
                                xml_stage_value = self.func_mapper(value, xml_stage_data.text)
                                stage_data[key] = xml_stage_value

                    stage_task[project_task_values["0_UID"]] = stage_data

        parent_value = {}
        parent_before = {}
        project_task_id_uid = {}
        project_task_seq = []
        for project_task in project_tasks_list:

            o_uid = project_task.pop('0_UID', None)

            if "name" not in project_task.keys():
                project_task["name"] = "Import Auto Name"

            if o_uid != 0:

                project_task.pop('0_ID', None)
                project_task.pop('0_OutlineNumber', None)
                project_task["project_id"] = project_id

                dt_date_start = fields.Datetime.from_string(project_task["date_start"])
                dt_date_end = fields.Datetime.from_string(project_task["date_end"])

                dt_delta = None
                if dt_date_end and dt_date_start:
                    dt_delta = dt_date_end - dt_date_start
                    dt_delta = dt_delta.total_seconds()

                project_task["plan_duration"] = dt_delta

                task_obj = project_task_model.create(project_task)
                task_id = task_obj.id

                project_task_seq.append({
                    "id": task_id,
                    "seq": project_tasks_list.index(project_task)
                })

                project_task_id_uid[o_uid] = task_id

                # Znaja tolko otstupi i seq - mozem vostonovit derevo
                if not parent_before:

                    parent_value["p_id"] = task_id
                    parent_value["sorting_level"] = project_task["sorting_level"]

                    parent_before["p_id"] = task_id
                    parent_before["sorting_level"] = project_task["sorting_level"]

                else:

                    new_parent_value = self.task_get_seq(task_obj=task_obj, project_task=project_task,
                                                         parent_value=parent_value,
                                                         parent_before=parent_before)
                    if new_parent_value:
                        parent_value = new_parent_value

                    parent_before["p_id"] = task_id
                    parent_before["sorting_level"] = project_task["sorting_level"]

            ######

        if xml_import:

            # TAG
            project_tags = self.env['project.tags']
            for key, values in tags_project.items():
                for tag_element in values:

                    project_tag_search = project_tags.search([('name', '=', tag_element["name"])])

                    if project_tag_search:

                        tag_id = tag_element["Tag_UID"]

                    else:

                        tag_project_to_db = {
                            "name": tag_element["name"],
                            "color": tag_element["color"],

                        }

                        tag_id = project_tags.create(tag_project_to_db).id

                    tag_rel_id = [(4, tag_id)]

                    p_task_id = project_task_id_uid[key]
                    p_task_search = self.env['project.task'].search([('id', '=', p_task_id)])

                    p_task_search.write({"tag_ids": tag_rel_id})

            # predecesors_tasks
            #
            project_task_predecessor_model = self.env['project.task.predecessor']
            for key, values in predecesors_tasks.items():
                for predecesor_link in values:
                    p_task_id = project_task_id_uid[key]
                    if predecesor_link["P_UID"] in project_task_id_uid.keys():
                        p_parent_task_id = project_task_id_uid[predecesor_link["P_UID"]]
                        p_type = exchange_tool.xml_predecessor_type(value=predecesor_link["type"],
                                                                    direct="from_xml")
                        p_lag_type = exchange_tool.xml_lag_format(value=predecesor_link["lag_type"],
                                                                  direct="from_xml")
                        p_lag_qty = exchange_tool.xml_link_lag(value_format=predecesor_link["lag_type"],
                                                               value_data=predecesor_link["lag_qty"],
                                                               direct="from_xml")

                        predecesor_value_to_db = {
                            "task_id": p_task_id,
                            "parent_task_id": p_parent_task_id,
                            "type": p_type,
                            "lag_type": p_lag_type,
                            "lag_qty": p_lag_qty,
                        }

                        project_task_predecessor_model.create(predecesor_value_to_db)

            # Stage
            for key, values in stage_task.items():
                stage_name = values["name"]

                if key in project_task_id_uid.keys():
                    task_id = project_task_id_uid[key]
                    task_obj = project_task_model.browse(task_id)

                    task_stage_exist = self.env['project.task.type'].search([('name', '=', stage_name)], limit=1)

                    if task_stage_exist:
                        stage_id = task_stage_exist.id
                    else:
                        stage_val = {
                            "name": stage_name,
                        }

                        stage_id = self.env['project.task.type'].create(stage_val).id

                    task_obj.write({'stage_id': stage_id})

            return project_task_id_uid

        return False



    def action_parse(self):

        xml_data = base64.b64decode(self.file_load)
        root = ET.fromstring(xml_data)
        nsmap = {'n': 'http://schemas.microsoft.com/project'}

        self.import_project_line_ids.unlink()
        self.import_task_line_ids.unlink()

        # Project - only parse for view
        self.parse_project(root, nsmap)

        # Task - only parse for view
        self.parse_task(root, nsmap)

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
        }



    def action_import(self):
        """
        """

        xml_data = base64.b64decode(self.file_load)
        root = ET.fromstring(xml_data)
        nsmap = {'n': 'http://schemas.microsoft.com/project'}

        # Project
        self.parse_project(root, nsmap, xml_import=True)

        # Tasks
        if self.project_id:
            self.parse_task(root, nsmap, xml_import=True, project_id=self.project_id.id)

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
        }


class ProjectNativeExchange(models.TransientModel):
    _name = "project.native.exchange"

    project_id = fields.Many2one('project.project', 'Project')
    name = fields.Char(string='File Name', default='project_exchange.xml')
    file_save = fields.Binary(string='XML File', readonly=True)
    errors = fields.Text('Errors')



    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id:
            self.name = '{} - {}.xml'.format(self.project_id.name, fields.Datetime.now())



    def get_data_xml(self, project_id):

        exchange_tool = self.env['project.native.exchange.tool']

        project_name = project_id.display_name

        current_date = exchange_tool.project_date_tool()
        creation_date = exchange_tool.project_date_tool(value=fields.Datetime.from_string(project_id.create_date),
                                                        type_con="to_string")
        start_date = exchange_tool.project_date_tool(value=fields.Datetime.from_string(project_id.date_start),
                                                     type_con="to_string")
        finish_date = exchange_tool.project_date_tool(value=fields.Datetime.from_string(project_id.date_end),
                                                      type_con="to_string")
        write_date = exchange_tool.project_date_tool(value=fields.Datetime.from_string(project_id.write_date),
                                                     type_con="to_string")

        schedule_from_start = exchange_tool.xml_schedule_mode(project_id.scheduling_type)

        project = ET.Element("Project", xmlns="http://schemas.microsoft.com/project")
        ET.SubElement(project, "SaveVersion").text = "14"
        ET.SubElement(project, "Name").text = project_name
        ET.SubElement(project, "CreationDate").text = creation_date
        ET.SubElement(project, "LastSaved").text = write_date
        ET.SubElement(project, "ScheduleFromStart").text = schedule_from_start
        ET.SubElement(project, "StartDate").text = start_date
        ET.SubElement(project, "FinishDate").text = finish_date
        ET.SubElement(project, "CurrentDate").text = current_date

        currency_digits = str(project_id.currency_id.decimal_places)  # "2"
        currency_symbol = u'{}'.format(project_id.currency_id.symbol)  # "$"
        currency_code = project_id.currency_id.name  # "USD"

        ET.SubElement(project, "CurrencyDigits").text = currency_digits
        ET.SubElement(project, "CurrencySymbol").text = currency_symbol
        ET.SubElement(project, "CurrencyCode").text = currency_code
        ET.SubElement(project, "CurrencySymbolPosition").text = "0"

        OutlineCodes = ET.SubElement(project, "OutlineCodes")
        WBSMasks = ET.SubElement(project, "WBSMasks")
        ExtendedAttributes = ET.SubElement(project, "ExtendedAttributes")
        Calendars = ET.SubElement(project, "Calendars")
        Tasks = ET.SubElement(project, "Tasks")
        Resources = ET.SubElement(project, "Resources")
        Assignments = ET.SubElement(project, "Assignments")

        self.env['project.task'].do_sorting(project_id.id)

        p_tasks = self.env['project.task'].search([('project_id', '=', project_id.id)], order="sorting_seq asc")

        p_task_list = []
        for p_task in p_tasks:

            p_task_list.append(p_task.id)

            task = ET.Element('Task')

            ET.SubElement(task, "UID").text = '{}'.format(p_task.id)  # 1
            ET.SubElement(task, "ID").text = '{}'.format(p_task_list.index(p_task.id) + 1)  # 1
            ET.SubElement(task, "Name").text = p_task.display_name  # "Test Task"

            taks_active = exchange_tool.xml_bool(p_task.active)
            ET.SubElement(task, "Active").text = taks_active

            taks_manual_auto = exchange_tool.xml_auto_manual(p_task.schedule_mode)
            ET.SubElement(task, "Manual").text = taks_manual_auto

            ET.SubElement(task, "OutlineNumber").text = '{}'.format(p_task_list.index(p_task.id) + 1)
            ET.SubElement(task, "OutlineLevel").text = '{}'.format(p_task.sorting_level + 1)

            t_start_date = exchange_tool.project_date_tool(value=fields.Datetime.from_string(p_task.date_start),
                                                           type_con="to_string")
            t_finish_date = exchange_tool.project_date_tool(value=fields.Datetime.from_string(p_task.date_end),
                                                            type_con="to_string")

            t_duration = timedelta(seconds=p_task.duration)

            iso8601duration = exchange_tool.to_iso8601(t_duration)

            ET.SubElement(task, "Start").text = t_start_date  # "2017-11-28T08:00:00"
            ET.SubElement(task, "Finish").text = t_finish_date  # "2017-11-28T08:00:00"
            ET.SubElement(task, "Duration").text = iso8601duration  # "PT72H0M0S"
            ET.SubElement(task, "ManualStart").text = t_start_date  # "2017-11-28T08:00:00"
            ET.SubElement(task, "ManualFinish").text = t_finish_date  # "2017-11-28T08:00:00"
            ET.SubElement(task, "ManualDuration").text = iso8601duration  # "PT72H0M0S"

            ET.SubElement(task, "RemainingDuration").text = iso8601duration  # "PT72H0M0S"

            ET.SubElement(task, "RemainingDuration").text = iso8601duration  # "PT72H0M0S"

            #
            is_milestone = exchange_tool.xml_bool(p_task.is_milestone)
            ET.SubElement(task, "Milestone").text = is_milestone

            on_gantt = exchange_tool.xml_bool(p_task.on_gantt)
            ET.SubElement(task, "OnGantt").text = on_gantt

            ET.SubElement(task, "ConstraintType").text = exchange_tool.xml_constraint_type(value=p_task.constrain_type,
                                                                                           direct="to_xml")

            if p_task.constrain_date:
                o_constrain_date = exchange_tool.project_date_tool(
                    value=fields.Datetime.from_string(p_task.constrain_date),
                    type_con="to_string")
                ET.SubElement(task, "ConstraintDate").text = o_constrain_date
            #

            ET.SubElement(task, "ColorGanttSet").text = exchange_tool.xml_bool(value=p_task.color_gantt_set,
                                                                               direct="to_xml")
            ET.SubElement(task, "ColorGantt").text = '{}'.format(p_task.color_gantt)

            for predecessor in p_task.predecessor_ids:
                PredecessorLink = ET.Element('PredecessorLink')

                pre_lag_type = predecessor.lag_type
                pre_lag_qty = predecessor.lag_qty

                ET.SubElement(PredecessorLink, "PredecessorUID").text = '{}'.format(predecessor.parent_task_id.id)
                ET.SubElement(PredecessorLink, "Type").text = exchange_tool.xml_predecessor_type(value=predecessor.type,
                                                                                                 direct="to_xml")
                ET.SubElement(PredecessorLink, "LinkLag").text = exchange_tool.xml_link_lag(value_format=pre_lag_type,
                                                                                            value_data=pre_lag_qty,
                                                                                            direct="to_xml")
                ET.SubElement(PredecessorLink, "LagFormat").text = exchange_tool.xml_lag_format(value=pre_lag_type,
                                                                                                direct="to_xml")

                task.append(PredecessorLink)

            # Tag
            for task_tag_id in p_task.tag_ids:
                task_tag = ET.Element('TaskTag')
                ET.SubElement(task_tag, "TagUID").text = '{}'.format(task_tag_id.id)
                ET.SubElement(task_tag, "TagName").text = '{}'.format(task_tag_id.name)
                ET.SubElement(task_tag, "TagColor").text = '{}'.format(task_tag_id.color)
                task.append(task_tag)

            # Stage
            if p_task.stage_id.id:
                StageID = ET.Element('StageID')
                ET.SubElement(StageID, "ID").text = '{}'.format(p_task.stage_id.id)
                ET.SubElement(StageID, "Name").text = '{}'.format(p_task.stage_id.name)
                task.append(StageID)

            Tasks.append(task)

        return project



    @api.multi
    def action_export(self):
        """
            Function is called from view
        """
        exchange_tool = self.env['project.native.exchange.tool']
        project = self.project_id

        if project:
            xml_data = self.get_data_xml(project)
            xml_data1 = exchange_tool.prettify(xml_data)
            xml_data2 = base64.b64encode(xml_data1)

            self.write({
                'file_save': xml_data2,
            })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
        }

