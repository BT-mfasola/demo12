# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Devintelle Software Solutions (<http://devintellecs.com>).
#
##############################################################################

from odoo import models, fields, api, _
import xlwt
from xlsxwriter.workbook import Workbook
from xlwt import easyxf
from io import StringIO
import base64
from odoo.exceptions import ValidationError


class dev_export(models.Model):
    _name = 'dev.export'
    
    name = fields.Char('Action Name',required="1")
    model_id = fields.Many2one('ir.model', 'Applies to', required="1")
    active = fields.Boolean('Active', default=True)
    
    header_text = fields.Char('Header Text')
    file_name = fields.Char('Excel Sheet Name', required="1",)
    
    relational_field = fields.Many2one('ir.model.fields', string="Sub Model")
    relational_model_id =fields.Many2one('ir.model', string='Relational Field Model')
    relational_fields_ids = fields.One2many('dev.relational.field','export_id',string='Relational Fields',copy=False)
    
    export_fields_ids = fields.One2many('dev.export.fields','export_id', string="Fields", copy=False)
    
    ref_ir_act_window = fields.Many2one('ir.actions.act_window', 'Sidebar action', readonly=True, copy=False,
                                        help="Sidebar action to make this template available on records "
                                             "of the related document model")
#    ref_ir_value = fields.Many2one('ir.values', 'Sidebar Button', readonly=True, copy=False,
#                                   help="Sidebar button to open the sidebar action")
                                   
    template = fields.Selection([('template1','Template-1'),('template2','Template-2')],string='Template',default='template1')
    
    split_sheet = fields.Boolean('Record per sheet')
    
    is_group_by = fields.Boolean('Group By')
    group_by_field_id = fields.Many2one('ir.model.fields', string="Group By Field",copy=False)
    sub_group_by_field_id = fields.Many2one('ir.model.fields',string="Sub Group By", copy=False)
    third_group_by_field_id = fields.Many2one('ir.model.fields',string="Third Group By", copy=False)
    
    
    print_company_detail = fields.Boolean('Print Company Detail', default=True)
    
    
    
    
    #company style Attribute
    
    company_set_font_name = fields.Char('Text Style', default='calibri')
    
    company_set_font_size = fields.Integer('Text Size', default=10)
    company_set_font_color = fields.Char('Text Color', default='black')
    
    company_set_bg_color = fields.Char('Background Color',default='white')
    company_set_bold = fields.Boolean('Bold')
    company_set_italic = fields.Boolean('Italic')
    company_set_underline = fields.Boolean('Underline')
    company_align=fields.Selection([('left','Left'),('center','Center'),('right','Right'),('justify','Justify'),('center_across','Center Across')],string='Text Align',default='left')
    
    company_set_border = fields.Boolean('Border')
    company_set_border_color = fields.Char('Border Color')
    
    #group style Attribute
    
    group_set_font_name = fields.Char('Text Style', default='calibri')
    
    group_set_font_size = fields.Integer('Text Size', default=10)
    group_set_font_color = fields.Char('Text Color', default='black')
    
    group_set_bg_color = fields.Char('Background Color',default='yellow')
    sub_group_set_bg_color = fields.Char('SubGroup Background Color',default='#c6c6c6')
    third_group_set_bg_color = fields.Char('Third Group Background Color',default='#e1e8f4')
    group_set_bold = fields.Boolean('Bold',default=True)
    group_set_italic = fields.Boolean('Italic')
    group_set_underline = fields.Boolean('Underline')
    group_align=fields.Selection([('left','Left'),('center','Center'),('right','Right'),('justify','Justify'),('center_across','Center Across')],string='Text Align',default='left')
    
    group_set_border = fields.Boolean('Border')
    group_set_border_color = fields.Char('Border Color')
    
    
    #header Attribute
    
    header_set_font_name = fields.Char('Text Style', default='calibri')
    
    header_set_font_size = fields.Integer('Text Size', default=15)
    header_set_font_color = fields.Char('Text Color', default='black')
    
    header_set_bg_color = fields.Char('Background Color')
    header_set_bold = fields.Boolean('Bold',default=True)
    header_set_italic = fields.Boolean('Italic')
    header_set_underline = fields.Boolean('Underline')
    header_align=fields.Selection([('left','Left'),('center','Center'),('right','Right'),('justify','Justify'),('center_across','Center Across')],string='Text Align',default='center')
    
    header_set_border = fields.Boolean('Border')
    header_set_border_color = fields.Char('Border Color')
    
    #Label Attributes
    
    label_set_font_name = fields.Char('Text Style', default='calibri')
    
    label_set_font_size = fields.Integer('Text Size', default=10)
    label_set_font_color = fields.Char('Text Color', default='black')
    
    lable_set_bg_color = fields.Char('Background Color', default='#c6c6c6')
    label_set_bold = fields.Boolean('Bold',default=True)
    label_set_italic = fields.Boolean('Italic')
    label_set_underline = fields.Boolean('Underline')
    label_align=fields.Selection([('left','Left'),('center','Center'),('right','Right'),('justify','Justify'),('center_across','Center Across')],string='Text Align',default='center')
    
    label_set_border = fields.Boolean('Border')
    label_set_border_color = fields.Char('Border Color')
    
    
    #Line Label Attribute
    
    line_label_set_font_name = fields.Char('Text Style', default='calibri')
    
    line_label_set_font_size = fields.Integer('Text Size', default=10)
    line_label_set_font_color = fields.Char('Text Color', default='black')
    
    line_lable_set_bg_color = fields.Char('Background Color', default='#c6c6c6')
    line_label_set_bold = fields.Boolean('Bold',default=True)
    line_label_set_italic = fields.Boolean('Italic')
    line_label_set_underline = fields.Boolean('Underline')
    line_label_align=fields.Selection([('left','Left'),('center','Center'),('right','Right'),('justify','Justify'),('center_across','Center Across')],string='Text Align',default='center')
    
    line_label_set_border = fields.Boolean('Border')
    line_label_set_border_color = fields.Char('Border Color')
    line_label_set_height = fields.Float('Line Table Label Height')
    line_label_valign = fields.Selection([('top', 'Top'), ('center', 'Center'), ('bottom', 'Bottom')])
    line_label_text_wrap = fields.Boolean('Text Wrap')
    
    
    #value Attribute
    
    val_set_font_name = fields.Char('Text Style', default='calibri')
    
    val_set_font_size = fields.Integer('Text Size', default=10)
    val_set_font_color = fields.Char('Text Color', default='black')
    
    val_set_bg_color = fields.Char('Background Color')
    val_set_bold = fields.Boolean('Bold')
    val_set_italic = fields.Boolean('Italic')
    val_set_underline = fields.Boolean('Underline')
    val_align=fields.Selection([('left','Left'),('center','Center'),('right','Right'),('justify','Justify'),('center_across','Center Across')],string='Text Align',default='left')
    
    val_set_border = fields.Boolean('Border')
    val_set_border_color = fields.Char('Border Color')
    
    
     #Line val Attribute
    
    line_val_set_font_name = fields.Char('Text Style', default='calibri')
    
    line_val_set_font_size = fields.Integer('Text Size', default=10)
    line_val_set_font_color = fields.Char('Text Color', default='black')
    
    line_val_set_bg_color = fields.Char('Background Color')
    line_val_set_bold = fields.Boolean('Bold')
    line_val_set_italic = fields.Boolean('Italic')
    line_val_set_underline = fields.Boolean('Underline')
    line_val_align=fields.Selection([('left','Left'),('center','Center'),('right','Right'),('justify','Justify'),('center_across','Center Across')],string='Text Align',default='left')
    
    line_val_set_border = fields.Boolean('Border')
    line_val_set_border_color = fields.Char('Border Color')
    is_sum = fields.Boolean('Print Sum')
    
    total_color = fields.Char('Sum Background Color', default='#eaebed')
    total_font_color = fields.Char('Total Font Color', default='black')

    print_counter_column = fields.Boolean('Print Counter Column')
    
    
    @api.onchange('model_id')
    def onchange_model(self):
        if self.model_id:
            self.relational_field = False
            self.is_group_by = False
            self.group_by_field_id = False
            self.relational_model_id = False
            self.export_fields_ids = False
            self.relational_fields_ids = False
            
            
    @api.multi
    def write(self,vals):
        res = super(dev_export,self).write(vals)
        if self.is_group_by:
            count =0
            if self.group_by_field_id:
                for field in self.export_fields_ids:
                    if field.name.name == self.group_by_field_id.name:
                        count +=1
                if count == 0:
                    raise ValidationError(_('Please Add %s field in fields Line !!!')%self.group_by_field_id.field_description)
        return res
    
    @api.model
    def create(self,vals):
        export_id= super(dev_export,self).create(vals)
        count =0
        if export_id.is_group_by:
            if export_id.group_by_field_id:
                for field in export_id.export_fields_ids:
                    if field.name.name == export_id.group_by_field_id.name:
                        count +=1
                if count == 0:
                    raise ValidationError(_('Please Add %s field in fields Line !!!')%export_id.group_by_field_id.field_description)
        return export_id
    
    @api.onchange('is_group_by')
    def change_is_group_by(self):
        if self.is_group_by:
            self.template = 'template1'
    
    @api.onchange('group_by_field_id')
    def change_group_by_field(self):
        if self.group_by_field_id:
            count =0
            for field in self.export_fields_ids:
                if self.group_by_field_id.name == field.name.name:
                    count +=1
            if count == 0:
                raise ValidationError(_('Please Add %s field in fields Line !!!')%self.group_by_field_id.field_description)
    
    
    @api.onchange('sub_group_by_field_id')
    def change_group_by_field(self):
        if self.sub_group_by_field_id:
            count =0
            for field in self.export_fields_ids:
                if self.sub_group_by_field_id.name == field.name.name:
                    count +=1
            if count == 0:
                raise ValidationError(_('Please Add %s field in fields Line !!!')%self.sub_group_by_field_id.field_description)
                
    @api.onchange('third_group_by_field_id')
    def change_group_by_field(self):
        if self.third_group_by_field_id:
            count =0
            for field in self.export_fields_ids:
                if self.third_group_by_field_id.name == field.name.name:
                    count +=1
            if count == 0:
                raise ValidationError(_('Please Add %s field in fields Line !!!')%self.third_group_by_field_id.field_description)
    
#    @api.onchange('relational_model_id')
#    def change_model_id(self):
#        self.relational_fields_ids.unlink()
    
    @api.onchange('relational_field')
    def change_name(self):
#        self.relational_fields_ids
        if self.relational_field:
            if self.relational_field.ttype == 'one2many':
                model_pool= self.env['ir.model']
                model_ids = model_pool.search([('model','=',self.relational_field.relation)],limit=1)
                self.relational_model_id = model_ids.id 
            self.is_group_by = False
            self.group_by_field_id = False  
            self.relational_fields_ids = False
        else:
            self.relational_model_id = False
            self.split_sheet = False
        
                                      
    
    
    @api.multi
    def unlink_excel(self):
        if self.ref_ir_act_window:
            self.ref_ir_act_window.unlink()
        return True
            
    @api.multi
    def export_excel(self):
        if self.ref_ir_act_window:
            self.ref_ir_act_window.unlink()
        ActWindowSudo = self.env['ir.actions.act_window'].sudo()
        view = self.env.ref('dev_export_excel.view_dev_export_wizard_form')
        src_obj = str(self.model_id.model)
        button_name = _('Export %s') % self.name
        action = ActWindowSudo.create({
            'name': button_name,
            'type': 'ir.actions.act_window',
            'res_model': 'dev.export.wizard',
            'src_model': src_obj,
            'context': "{'dex_export_id' : %d}" % (self.ids[0]),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'view_id': view.id,
            'binding_model_id': self.model_id.id,
            'target': 'new',
            'auto_refresh': 1})
        self.write({
            'ref_ir_act_window': action.id,
        })

        return True
        
 
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
