from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)
import json


class UserSpecific(models.Model):
    _name = "user.specific"
    _description = 'User Specfic Information'

    model_name = fields.Char(String="Name")
    user_id = fields.Many2one('res.users', string='User')
    ks_action_id = fields.Char(String="Action Id")
    ks_table_width = fields.Float(String="table Width")
    ks_editable = fields.Boolean(string="Editable List Mode")
    fields = fields.One2many("user.fields", "fields_list", "Fields Information")

    @api.model
    def check_user_exists(self, model_name, uid, ks_action_id):
        ks_user_table_result = {'ks_fields_data': False, 'ks_table_data': False}

        user_exists = self.env['user.specific'].search([
            ('model_name', '=', model_name),
            ('ks_action_id', '=', ks_action_id),
            ('user_id', '=', uid)
        ], limit=1)

        if user_exists:
            ks_user_table_result['ks_fields_data'] = dict([(x['field_name'], x) for x in user_exists.fields.read(
                ['ksShowField', 'field_name', 'ks_invisible', 'ks_field_order', 'ks_columns_name', 'ks_width'])])
            ks_user_table_result['ks_table_data'] = user_exists.read(['ks_table_width', 'ks_editable'])[0]

        return ks_user_table_result


    @api.model
    def updating_data(self, model_name, fields_name, uid, ks_action_id, ks_table_width):
        view = self.env['user.specific'].search([
            ('model_name', '=', model_name),
            ('ks_action_id', '=', ks_action_id),
            ('user_id', '=', uid)
        ], limit=1)
        vals = {
            'model_name': model_name,
            'user_id': uid,
            'ks_action_id': ks_action_id,
            'ks_table_width': ks_table_width,
        }
        if not view:
            view = self.create(vals)
        else:
            view.write(vals)
            view.fields.unlink()
        for rec in fields_name:
            # 'ks_required': rec['ks_required'],
            # 'ks_readonly': rec['ks_readonly'],
            vals_2 = {
                'field_name': rec['fieldName'],
                'ksShowField': rec['ksShowField'],
                'ks_field_order': rec['ks_field_order'],
                'ks_invisible': rec['ks_invisible'],
                'ks_columns_name': rec['ks_Columns_name'],
                'fields_list': view.id,
                'ks_width': rec['ks_col_width']
            }
            self.env['user.fields'].create(vals_2)

    @api.model
    def restoring_to_default(self, model_name, uid, ks_action_id):
        user_exists = self.env['user.specific'].search([
            ('model_name', '=', model_name),
            ('ks_action_id', '=', ks_action_id),
            ('user_id', '=', uid)
        ], limit=1)
        if user_exists:
            user_exists.fields.unlink()
            user_exists.unlink()


class Userfields(models.Model):
    _name = "user.fields"
    _description = 'User Specfic Fields'
    field_name = fields.Char(String="Name", required="True")
    ksShowField = fields.Boolean(default=True, string="Show Field in list")
    ks_field_order = fields.Integer(String="Name")
    ks_invisible = fields.Boolean(default=False, string="Show invisible columns")
    # ks_required = fields.Boolean(default=False, string="Show required Columns")
    # ks_readonly = fields.Boolean(default=False, string="Show readonly Columns")
    fields_list = fields.Many2one(
        'user.specific', "User Specific Fields"
    )
    ks_columns_name = fields.Char(String="Columns Name")
    ks_width = fields.Char(String="Field Width")


class KsUserStandardSpecific(models.Model):
    _name = "ks.user.standard.specific"

    _description = 'User Standards Specfic Information'

    model_name = fields.Char(String="Name")

    user_id = fields.Many2one('res.users', string='User')

    ks_table_width = fields.Integer(String="table Width")

    ks_action_id = fields.Char(String="Action Id")

    fields = fields.One2many(
        "ks.user.standard.fields", "fields_list", "Fields Information"
    )

    # Function revoked at each time list view is loaded
    @api.model
    def check_user_exists(self, model_name, uid, ks_action_id):
        user_exists = self.env['ks.user.standard.specific'].search([
            ('model_name', '=', model_name),
            ('ks_action_id', '=', ks_action_id),
            ('user_id', '=', uid)
        ], limit=1)
        if user_exists:
            # 'ks_required','ks_readonly'
            return user_exists.fields.read(
                ['ksShowField', 'field_name', 'ks_invisible', 'ks_columns_name', 'ks_width', ]) + user_exists.read(
                ['ks_table_width'])
        else:
            return False

    @api.model
    def updating_data(self, model_name, fields_name, uid, ks_action_id, ks_table_width):
        view = self.env['ks.user.standard.specific'].search([
            ('model_name', '=', model_name),
            ('ks_action_id', '=', ks_action_id),
            ('user_id', '=', uid)
        ], limit=1)
        vals = {
            'model_name': model_name,
            'user_id': uid,
            'ks_action_id': ks_action_id,
            'ks_table_width': ks_table_width,
        }
        if not view:
            view = self.create(vals)

        else:
            view.write(vals)
            view.fields.unlink()
        for rec in fields_name:
            # 'ks_required': rec['ks_required'],
            # 'ks_readonly': rec['ks_readonly'],
            vals_2 = {
                'field_name': rec['fieldName'],
                'ksShowField': rec['ksShowField'],
                'ks_field_order': rec['ks_field_order'],
                'ks_invisible': rec['ks_invisible'],
                'ks_columns_name': rec['ks_Columns_name'],
                'fields_list': view.id,
                'ks_width': rec['ks_col_width']
            }
            self.env['ks.user.standard.fields'].create(vals_2)

    @api.model
    def restoring_to_default(self, model_name, uid, ks_action_id):
        user_exists = self.env['ks.user.standard.specific'].search([
            ('model_name', '=', model_name),
            ('ks_action_id', '=', ks_action_id),
            ('user_id', '=', uid)
        ], limit=1)
        if user_exists:
            user_exists.fields.unlink()
            user_exists.unlink()


class KsUserStandardFields(models.Model):
    _name = "ks.user.standard.fields"
    _description = 'User Specific Standard fields'
    field_name = fields.Char(String="Name", required="True")
    ksShowField = fields.Boolean(default=True, string="Show Field in list")
    ks_field_order = fields.Integer(String="Name")
    ks_invisible = fields.Boolean(default=False, string="Show invisible columns")
    # ks_required = fields.Boolean(default=False, string="Show required Columns")
    # ks_readonly = fields.Boolean(default=False, string="Show readonly Columns")
    fields_list = fields.Many2one(
        'ks.user.standard.specific', "User Specific Fields"
    )
    ks_columns_name = fields.Char(String="Columns Name")
    ks_width = fields.Char(String="Field Width")


class UserMode(models.Model):
    _name = "user.mode"
    model_name = fields.Char(String="Name")
    _description = 'User Mode'
    user_id = fields.Many2one('res.users', string='User')

    ks_action_id = fields.Char(String="Action Id")

    editable = fields.Char(string="Define user editable mode")

    @api.model
    def check_user_mode(self, ks_model_name, uid, ks_action_id):
        ks_list_view_data = {
            'ks_can_edit': self.env.user.has_group('ks_list_view_manager.ks_list_view_manager_edit_and_read'),
            'ks_dynamic_list_show': self.env.user.has_group('ks_list_view_manager.ks_list_view_manager_dynamic_list'),
            'ks_can_advanced_search': self.env.user.has_group(
                'ks_list_view_manager.ks_list_view_manager_advance_Search'),
            'currency_id': self.env.user.company_id.currency_id.id,
        }
        user_exists = self.env['user.mode'].search([
            ('model_name', '=', ks_model_name),
            ('ks_action_id', '=', ks_action_id),
            ('user_id', '=', uid)
        ], limit=1)
        if user_exists:
            ks_list_view_data['list_view_data'] = user_exists.read(['editable'])
        else:
            ks_list_view_data['list_view_data'] = False

        return ks_list_view_data

    @api.model
    def updating_mode(self, ks_model_name, uid, mode, ks_action_id):
        view = self.env['user.mode'].search([
            ('model_name', '=', ks_model_name),
            ('ks_action_id', '=', ks_action_id),
            ('user_id', '=', uid)
        ], limit=1)
        vals = {
            'model_name': ks_model_name,
            'user_id': uid,
            'editable': mode,
            'ks_action_id': ks_action_id,
        }
        if not view:
            self.create(vals)

        else:
            view.write(vals)

    @api.model
    def ks_get_autocomplete_values(self, model, field, type, value, ks_one2many_relation):
        if ks_one2many_relation:
            relation_name = self.env[ks_one2many_relation]._rec_name
            ids = self.env[model].search([(relation_name, 'ilike', value)], limit=10).ids
            return self.env[model].search([(field, 'in', ids)]).mapped(field + ".name")
        else:
            return self.env[model].search_read([(field, 'ilike', value)], [field])


class KsHttp(models.AbstractModel):
    _inherit = 'ir.http'

    # Set Config parameter value to the session.
    def session_info(self):
        rec = super(KsHttp, self).session_info()
        rec['ks_toggle_color'] = self.env['ir.config_parameter'].sudo().get_param('ks_toggle_color_field_change')
        rec['ks_header_color'] = self.env['ir.config_parameter'].sudo().get_param('ks_header_color_field_change')
        rec['ks_serial_number'] = self.env['ir.config_parameter'].sudo().get_param('ks_serial_number')
        return rec


class KsResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ks_toggle_color_field_change = fields.Char(string='Toggle Color',
                                               config_parameter='ks_toggle_color_field_change')

    ks_header_color_field_change = fields.Char(string='Header Color',
                                               config_parameter='ks_header_color_field_change')

    ks_serial_number = fields.Boolean(string="Serial Number", config_parameter='ks_serial_number')

