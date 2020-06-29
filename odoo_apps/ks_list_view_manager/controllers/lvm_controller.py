import json

from odoo import http
import logging

_logger = logging.getLogger(__name__)
from odoo.http import request
from odoo.addons.web.controllers.main import DataSet
from lxml import etree as etree


class LvmController(DataSet, http.Controller):

    @http.route(['/web/dataset/call_kw', '/web/dataset/call_kw/<path:path>'], type='json', auth="user")
    def call_kw(self, model, method, args, kwargs, path=None):
        call_kw_result = super(LvmController, self).call_kw(model, method, args, kwargs, path)
        if method == "load_views" and call_kw_result.get('fields_views').get('list'):
            ks_list_view_id = call_kw_result["fields_views"]["list"].get("view_id")

            self.ks_prepare_lvm_list_data(call_kw_result, model, ks_list_view_id)
        return call_kw_result

    def ks_prepare_lvm_list_data(self, original_list_data, model, ks_list_view_id):
        list_view_data = original_list_data.get('fields_views').get('list')

        if ks_list_view_id:
            list_view_data['ks_lvm_user_data'] = self.ks_fetch_lvm_data(model, ks_list_view_id)

            if list_view_data['ks_lvm_user_data']['ks_lvm_user_table_result']['ks_fields_data']:
                self.ks_process_arch(list_view_data, original_list_data.get('fields'))
        else:
            user_mode_data = request.env['user.mode'].check_user_mode(model, request.env.user.id, False)
            user_mode_data['ks_can_advanced_search'] = False
            user_mode_data['ks_can_edit'] = False
            user_mode_data['ks_dynamic_list_show'] = False
            ks_lvm_user_data = {
                'ks_lvm_user_mode_data': user_mode_data
            }
            list_view_data['ks_lvm_user_data'] = ks_lvm_user_data

    def ks_fetch_lvm_data(self, model, ks_view_id=False):
        ks_lvm_user_data = {}
        user_mode_model = request.env['user.mode']
        user_specific_model = request.env['user.specific']

        user_mode_data = user_mode_model.check_user_mode(model, request.env.user.id, ks_view_id)

        ks_user_table_result = user_specific_model.check_user_exists(model, request.env.user.id, ks_view_id)

        ks_lvm_user_data['ks_lvm_user_table_result'] = ks_user_table_result
        ks_lvm_user_data['ks_lvm_user_mode_data'] = user_mode_data
        ks_lvm_user_data['ksViewID'] = ks_view_id
        return ks_lvm_user_data

    @http.route('/ks_lvm_control/user_lvm_data', type='json', auth="user")
    def ks_fetch_lvm_data_controller(self, model, ks_view_id=False):
        return self.ks_fetch_lvm_data(model, ks_view_id)

    @http.route('/ks_lvm_control/update_list_view_data', type='json', auth="user")
    def update_list_view_data(self, ks_table_data, ks_fields_data, ks_fetch_options):
        for ks_table in ks_table_data:
            request.env['user.specific'].browse(ks_table.get('id')).write(ks_table)

        for ks_field in ks_fields_data:
            request.env['user.fields'].browse(ks_field.get('id')).write(ks_field)

        if ks_fetch_options:
            return self.ks_generate_arch_view(ks_fetch_options.get('ks_model'), ks_fetch_options.get('ks_view_id'))

    @http.route('/ks_lvm_control/ks_generate_arch_view', type='json', auth="user")
    def ks_generate_arch_view(self, ks_model, ks_view_id):
        ks_view_data = request.env[ks_model].load_views([(ks_view_id, 'list')])
        self.ks_prepare_lvm_list_data(ks_view_data, ks_model, ks_view_id)
        return ks_view_data

    @http.route('/ks_lvm_control/create_list_view_data', type='json', auth="user")
    def create_list_view_data(self, ks_model, ks_editable, ks_view_id, ks_table_width_per, ks_fields_data):
        list_view_record = request.env['user.specific'].create({
            'model_name': ks_model,
            'user_id': request.env.uid,
            'ks_action_id': ks_view_id,
            'ks_table_width': ks_table_width_per,
            'ks_editable': ks_editable,
        })

        for rec in ks_fields_data.values():
            rec.update({"fields_list": list_view_record.id})
            request.env['user.fields'].create(rec)

        return self.ks_generate_arch_view(ks_model, ks_view_id)
        # Removing Fields that are not in view anymore

    def check_fields(self, table_id, fields_list, ks_field_list):
        for r_field in filter(lambda x: x not in [x for x in fields_list.keys()], [x['field_name'] for x in ks_field_list.values()]):
            field_rec = ks_field_list.pop(r_field)
            request.env['user.fields'].browse(field_rec.get('id', 0)).sudo().unlink()

        for field in filter(lambda x: not ks_field_list.get(x, False), fields_list.keys()):
            ks_field_list[field] = val = {
                "ks_columns_name": fields_list[field]['string'],
                "ksShowField": False,
                "field_name": field,
                "ks_width": 0,
                "ks_field_order": len(ks_field_list)
            }
            val.update({'fields_list': table_id})
            rec_id = request.env['user.fields'].create(val)
            ks_field_list[field]['id'] = rec_id.id

    def ks_process_arch(self, list_view_data, fields_list):
        # We make default fields as readonly in List View
        ks_default_field_list = ["id", "create_uid", "create_date", "write_uid", "write_date", "__last_update"]

        # Rejected Field List (This field wont be shown in dropdown menu)
        ks_reject_field_list = ["activity_exception_decoration"]

        node = etree.fromstring(list_view_data['arch'])
        ks_field_list = list_view_data['ks_lvm_user_data']['ks_lvm_user_table_result']['ks_fields_data']
        LvmController.check_fields(self, list_view_data['ks_lvm_user_data']['ks_lvm_user_table_result']['ks_table_data']['id'], fields_list, ks_field_list)

        # Checking if user allowed to edit/read table
        if list_view_data['ks_lvm_user_data']['ks_lvm_user_mode_data']['ks_can_edit']:
            if list_view_data['ks_lvm_user_data']['ks_lvm_user_table_result']['ks_table_data']['ks_editable']:
                node.set('editable', 'top')
            elif node.get("editable"):
                node.attrib.pop("editable")

        # Setting all fields to invisible
        for field_node in node.getchildren():
            field_node.set('invisible', '1')
            if field_node.get('modifiers'):
                modifiers = json.loads(field_node.get('modifiers'))
                if not modifiers.get('column_invisible'):
                    modifiers.update({'column_invisible': True})
                    field_node.set('modifiers', json.dumps(modifiers))
            if field_node.get("name") in ks_field_list:
                if field_node.get("name") and not ks_field_list[field_node.get("name")]['ksShowField'] and field_node.tag != "field":
                    node.remove(field_node)
            else:
                ks_field_list[field_node.get("name")] = val = {
                    "ks_columns_name": field_node.attrib['name'],
                    "ksShowField": False,
                    "field_name": field_node.get("name"),
                    "ks_width": 0,
                    "ks_field_order": len(ks_field_list)
                }
                rec_id = request.env['user.fields'].create(val)
                ks_field_list[field_node.get("name")]['id'] = rec_id.id

        # Only showing selected fields to visible
        for field_name in [x['field_name'] for x in ks_field_list.values() if x['ksShowField']]:
            if list(filter(lambda x: x.get('name') == field_name, node.getchildren())):
                for field_node in list(filter(lambda x: x.get('name') == field_name, node.getchildren())):
                    field_node.set('invisible', '0')
                    field_node.set('string', ks_field_list[field_name]['ks_columns_name'])

                    if field_node.get('modifiers'):
                        modifiers = json.loads(field_node.get('modifiers'))
                        if modifiers.get('column_invisible'):
                            modifiers.update({'column_invisible': False})
                            field_node.set('modifiers', json.dumps(modifiers))

                    if field_node.get('optional'):
                        field_node.attrib.pop('optional')

            else:
                field_node = etree.Element('field', attrib={'name': field_name, 'invisible': '0',
                                                            'string': ks_field_list[field_name]['ks_columns_name']})
                node.append(field_node)
                list_view_data['fields'][field_name] = fields_list[field_name]

        # Sorting Process : Remove Old Nodes -> Insert Sorted Nodes again
        sorted_node_fields = sorted(node.getchildren(), key=lambda x: ks_field_list[x.get('name')]['ks_field_order'])
        for field_node in node.getchildren():
            node.remove(field_node)

        for field_node in sorted_node_fields:
            # Updating Default fields to readonly.
            if field_node.get("name") in ks_default_field_list:
                if field_node.get('modifiers'):
                    modifiers = json.loads(field_node.get('modifiers'))
                    modifiers["readonly"] = True
                    field_node.set('modifiers', json.dumps(modifiers))
                else:
                    field_node.set('modifiers', json.dumps({"readonly": True}))

            if field_node.get("name") not in ks_reject_field_list:
                node.append(field_node)

        list_view_data['arch'] = etree.tostring(node, pretty_print=True, encoding='unicode')

    @http.route('/ks_lvm_control/ks_duplicate_list_records', type='json', auth="user")
    def ks_duplicate_list_records(self, ks_model, ks_record_ids):
        for rec_id in ks_record_ids:
            request.env[ks_model].browse(rec_id).copy()

    @http.route('/ks_lvm_control/ks_reset_list_view_data', type='json', auth="user")
    def ks_reset_list_view_data(self, ks_model, ks_view_id, ks_lvm_table_id):
        ks_lvm_user_specific = request.env['user.specific'].browse(ks_lvm_table_id)
        ks_lvm_user_specific.fields.sudo().unlink()
        ks_lvm_user_specific.sudo().unlink()
        ks_view_data = request.env[ks_model].load_views([(ks_view_id, 'list')])
        ks_view_data['fields'].update(ks_view_data['fields_views']['list']['fields'])
        ks_view_data['fields_views']['list']['fields'] = ks_view_data['fields']
        self.ks_prepare_lvm_list_data(ks_view_data, ks_model, ks_view_id)
        return ks_view_data
