# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Devintelle Software Solutions (<http://devintellecs.com>).
#
##############################################################################

#from cStringIO import StringIO
from io import BytesIO
import time
import datetime
from odoo import api, fields, models, _
import xlwt

from xlsxwriter.workbook import Workbook
from xlwt import easyxf
import base64
import xlsxwriter
import itertools
from operator import itemgetter
import operator
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class dev_export_wizard(models.TransientModel):
    _name ='dev.export.wizard'
    
    
    @api.multi
    def get_main_field_values_dic(self,model_id,field_val,rec):
        main_vals={}
        label=[]
        for field in field_val:
            if len(field) > 1:
                model_id_val = model_id.read([field[0]])
                field_val = model_id_val[0].get(field[0])
                if field_val:
                    model_pool = self.env[field[1]]
                    field_obj_ids = model_pool.browse(field_val[0])
                    field_obj_val = field_obj_ids.read([field[2]])
                    final_val = field_obj_val[0].get(field[2])
                    if field[0] == rec.group_by_field_id.name or field[0] == rec.sub_group_by_field_id.name or field[0] == rec.third_group_by_field_id.name:
                        main_vals.update({field[0]:final_val or ''})
                        label.append(field[0])
                    else:
                        main_vals.update({field[2]:final_val or ''})
                        label.append(field[2])
                else:   
                    if field[0] == rec.group_by_field_id.name or field[0] == rec.sub_group_by_field_id.name or field[0] == rec.third_group_by_field_id.name:
                        main_vals.update({field[0]:''})
                        label.append(field[0])
                    else:
                        main_vals.update({field[2]:''})
                        label.append(field[2])
            else:
                model_id_val = model_id.read([field[0]])
                field_val = model_id_val[0].get(field[0])
                if field[0] == rec.group_by_field_id.name or field[0] == rec.sub_group_by_field_id.name or field[0] == rec.third_group_by_field_id.name:
                    main_vals.update({field[0]:field_val or ''})
                    label.append(field[0])
                else:
                    main_vals.update({field[0]:field_val or ''})
                    label.append(field[0])
        return (label,main_vals)
        
    @api.multi
    def get_main_field_values(self,model_id,field_val):
        main_vals=[]
        for field in field_val:
            if len(field) > 1:
                model_id_val = model_id.read([field[0]])
                field_val = model_id_val[0].get(field[0])
                if field_val:
                    model_pool = self.env[field[1]]
                    field_obj_ids = model_pool.browse(field_val[0])
                    field_obj_val = field_obj_ids.read([field[2]])
                    final_val = field_obj_val[0].get(field[2])
                    main_vals.append(final_val or '')
                else:
                    main_vals.append('')
            else:
                model_id_val = model_id.read([field[0]])
                field_val = model_id_val[0].get(field[0])
                main_vals.append(field_val or '')
        return main_vals
        
    @api.multi
    def get_main_field_label(self,fields):
        field_val = []
        main_field_label = []
        line_sum_dic={}
        i=0
        for field in fields:
            if not field.ref_field:
                field_val.append([field.name.name])
                if field.name.ttype in ['integer','float','monetary']:
                    line_sum_dic.update({str(i):0})
            else:
                field_val.append([field.name.name,field.name.relation,field.ref_field.name])
                if field.ref_field.ttype in ['integer','float','monetary']:
                    line_sum_dic.update({str(i):0})
            i+=1
            main_field_label.append(field.label or '')
        return {'field_val':field_val,'main_field_label':main_field_label,'line_sum_dic':line_sum_dic}
        
        
    def set_main_label_formate(self,rec,main_label_format):
        if rec.label_set_font_name:
            main_label_format.set_font_name(rec.label_set_font_name)
        if rec.label_set_font_size:
            main_label_format.set_font_size(rec.label_set_font_size)
        if rec.label_set_font_color:
            main_label_format.set_font_color(rec.label_set_font_color)
        if rec.lable_set_bg_color:
            main_label_format.set_bg_color(rec.lable_set_bg_color)
        if rec.label_set_border:
            main_label_format.set_border()
            main_label_format.set_border_color(rec.label_set_border_color)
        if rec.label_set_bold:
            main_label_format.set_bold()
        if rec.label_set_italic:
            main_label_format.set_italic()
        if rec.label_set_underline:
            main_label_format.set_underline()
        if rec.label_align:
            main_label_format.set_align(rec.label_align)
            
        return main_label_format
    
    def set_main_val_format(self,rec,main_val_format,align='',bold='',bg_color='',text_color=''):
        if rec.val_set_font_name:
            main_val_format.set_font_name(rec.val_set_font_name)
        if rec.val_set_font_size:
            main_val_format.set_font_size(rec.val_set_font_size)
        if text_color:
            main_val_format.set_font_color(text_color)
        else:
            if rec.val_set_font_color:
                main_val_format.set_font_color(rec.val_set_font_color)
        if bg_color:
            main_val_format.set_bg_color(bg_color)
        else:
            if rec.val_set_bg_color:
                main_val_format.set_bg_color(rec.val_set_bg_color)
        if rec.val_set_border:
            main_val_format.set_border()
            main_val_format.set_border_color(rec.val_set_border_color)
        if bold:
            main_val_format.set_bold()
        else:
            if rec.val_set_bold:
                main_val_format.set_bold()
        if rec.val_set_italic:
            main_val_format.set_italic()
        if rec.val_set_underline:
            main_val_format.set_underline()
            
        if align:
            main_val_format.set_align(align)
        else:
            if rec.val_align:
                main_val_format.set_align(rec.val_align)
            
        return main_val_format
        
    def set_line_label_format(self,rec,line_label_format):
        if rec.line_label_set_font_name:
            line_label_format.set_font_name(rec.line_label_set_font_name)
        if rec.line_label_set_font_size:
            line_label_format.set_font_size(rec.line_label_set_font_size)
        if rec.line_label_set_font_color:
            line_label_format.set_font_color(rec.line_label_set_font_color)
        if rec.line_lable_set_bg_color:
            line_label_format.set_bg_color(rec.line_lable_set_bg_color)
        if rec.line_label_set_border:
            line_label_format.set_border()
            line_label_format.set_border_color(rec.line_label_set_border_color)
        if rec.line_label_set_bold:
            line_label_format.set_bold()
        if rec.line_label_set_italic:
            line_label_format.set_italic()
        if rec.line_label_set_underline:
            line_label_format.set_underline()
        if rec.line_label_align:
            line_label_format.set_align(rec.line_label_align)
        if rec.line_label_text_wrap:
            line_label_format.set_text_wrap()
        if rec.line_label_valign:
            line_label_format.set_valign(rec.line_label_valign)
        return line_label_format
    
    def set_line_val_format(self,rec,line_val_format,align='',bold='',bg_color='',text_color=''):
        if rec.line_val_set_font_name:
            line_val_format.set_font_name(rec.line_val_set_font_name)
        if rec.line_val_set_font_size:
            line_val_format.set_font_size(rec.line_val_set_font_size)
        if text_color:
            line_val_format.set_font_color(text_color)
        else:
            if rec.line_val_set_font_color:
                line_val_format.set_font_color(rec.line_val_set_font_color)
        if bg_color:
            line_val_format.set_bg_color(bg_color)
        else:
            if rec.line_val_set_bg_color:
                line_val_format.set_bg_color(rec.line_val_set_bg_color)
        if rec.line_val_set_border:
            line_val_format.set_border()
            line_val_format.set_border_color(rec.line_val_set_border_color)
        if bold:
            line_val_format.set_bold()
        else:
            if rec.line_val_set_bold:
                line_val_format.set_bold()
        if rec.line_val_set_italic:
            line_val_format.set_italic()
        if rec.line_val_set_underline:
            line_val_format.set_underline()
        if align:
            line_val_format.set_align(align)
        else:
            if rec.line_val_align:
                line_val_format.set_align(rec.line_val_align)
        return line_val_format
        
    def set_header_format(self,rec,header_format):
        if rec.header_set_font_name:
            header_format.set_font_name(rec.header_set_font_name)
        if rec.header_set_font_size:
            header_format.set_font_size(rec.header_set_font_size)
        if rec.header_set_font_color:
            header_format.set_font_color(rec.header_set_font_color)
        if rec.header_set_bg_color:
            header_format.set_bg_color(rec.header_set_bg_color)
        if rec.header_set_border:
            header_format.set_border()
            header_format.set_border_color(rec.header_set_border_color)
        if rec.header_set_bold:
            header_format.set_bold()
        if rec.header_set_italic:
            header_format.set_italic()
        if rec.header_set_underline:
            header_format.set_underline()
        if rec.header_align:
            header_format.set_align(rec.header_align)
        return header_format
        
    def set_group_format(self,rec,group_format,align='',bg_color='',text_color=''):
        if rec.group_set_font_name:
            group_format.set_font_name(rec.group_set_font_name)
        if rec.group_set_font_size:
            group_format.set_font_size(rec.group_set_font_size)
        if text_color:
            group_format.set_font_color(text_color)
        else:
            if rec.group_set_font_color:
                group_format.set_font_color(rec.group_set_font_color)
        if bg_color:
            group_format.set_bg_color(bg_color)
        else:
            if rec.group_set_bg_color:
                group_format.set_bg_color(rec.group_set_bg_color)
        if rec.group_set_border:
            group_format.set_border()
            group_format.set_border_color(rec.group_set_border_color)
        if rec.group_set_bold:
            group_format.set_bold()
        if rec.group_set_italic:
            group_format.set_italic()
        if rec.group_set_underline:
            group_format.set_underline()
        if align:
            group_format.set_align(align)
        else:
            if rec.group_align:
                group_format.set_align(rec.group_align)
        return group_format
    
    def set_company_format(self,rec,company_format):
        if rec.company_set_font_name:
            company_format.set_font_name(rec.company_set_font_name)
        if rec.company_set_font_size:
            company_format.set_font_size(rec.company_set_font_size)
        if rec.company_set_font_color:
            company_format.set_font_color(rec.company_set_font_color)
        if rec.company_set_bg_color:
            company_format.set_bg_color(rec.company_set_bg_color)
        if rec.company_set_border:
            company_format.set_border()
            company_format.set_border_color(rec.company_set_border_color)
        if rec.company_set_bold:
            company_format.set_bold()
        if rec.company_set_italic:
            company_format.set_italic()
        if rec.company_set_underline:
            company_format.set_underline()
        if rec.company_align:
            company_format.set_align(rec.company_align)
        return company_format
                
    @api.multi
    def export_excel(self):
        dev_export_id = self._context.get('dex_export_id')
        rec = self.env['dev.export'].browse(dev_export_id)
        f_name = rec.file_name + '.xlsx'
    
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        
        obj_pool = self.env[rec.model_id.model]
        active_ids = self._context.get('active_ids')
        if active_ids:
            active_ids.sort()
            active_ids.reverse()
        obj_ids = obj_pool.browse(active_ids)
        
        
        res=self.get_main_field_label(rec.export_fields_ids)
        field_val = res.get('field_val')
        main_field_label = res.get('main_field_label')
        main_line_sum_dic = res.get('line_sum_dic')
        
        
        # set the main label Format
        main_label_format = workbook.add_format()
        main_label_format = self.set_main_label_formate(rec,main_label_format)
        
        #set the main value format
        main_val_format = workbook.add_format()
        main_val_format = self.set_main_val_format(rec,main_val_format)
        
        #set the header format
        header_format = workbook.add_format()
        header_format = self.set_header_format(rec,header_format)
        
        group_format = workbook.add_format()
        group_format = self.set_group_format(rec,group_format)
        
        company_format = workbook.add_format()
        company_format = self.set_company_format(rec,company_format)
        
        
        worksheet=[]
        if not rec.split_sheet or not rec.relational_field:
            worksheet=[0]
            worksheet[0] = workbook.add_worksheet(rec.file_name)
            worksheet[0].set_column(0, 30, 10)
            row=0
            if rec.print_company_detail:
                row=0
                company = self.env.user.company_id
                worksheet[0].merge_range(row, 0, row, 1, company.name or '',company_format)
                row+=1
                worksheet[0].merge_range(row, 0, row, 1, company.street or '',company_format)
                row+=1
                if company.street2:
                    worksheet[0].merge_range(row, 0, row, 1, company.street2 or '',company_format)
                    row+=1
                if company.city or company.zip:
                    city=''
                    if company.city:
                        city = company.city
                    if company.zip:
                        if city:
                            city = city + '-' + company.zip
                        else:
                            city = company.zip
                    worksheet[0].merge_range(row, 0, row, 1, city or '',company_format)
                    row+=1
                if company.country_id:
                    worksheet[0].merge_range(row, 0, row, 1, company.country_id.name or '',company_format)
                    row+=1
            if rec.header_text:
                row = 1
                worksheet[0].merge_range(0, 3, 1, 7, rec.header_text,header_format)
            if rec.print_company_detail or rec.header_text:
                row+=1
        else:
            for l in range(0,len(obj_ids)):
                worksheet.append(l)
        
        
        
        if rec.is_group_by:
            # this section for the group
            group_field_label = []
            group_field_name = []
            group_field_vals=[]
            sum_dic={}
            i=0
            for field in rec.export_fields_ids:
                if not field.ref_field:
                    group_field_label.append(field.label)
                    group_field_name.append([field.name.name])
                    if field.name.ttype in ['integer','float','monetary']:
                        sum_dic.update({str(i):0})
                    i+=1
                else:
                    group_field_label.append(field.label)
                    group_field_name.append([field.name.name,field.name.relation,field.ref_field.name])
                    if field.ref_field.ttype in ['integer','float','monetary']:
                        sum_dic.update({str(i):0})
                    i+=1
                    
            g_label = []
            for model in obj_ids:
                vals= self.get_main_field_values_dic(model,group_field_name,rec)
                if not g_label:
                    g_label = vals[0]
                group_field_vals.append(vals[1])
            new_lst=sorted(group_field_vals,key=itemgetter(rec.group_by_field_id.name))
            groups = itertools.groupby(new_lst, key=operator.itemgetter(rec.group_by_field_id.name))
            results = [{rec.group_by_field_id.name:k,'values':[x for x in v]} for k, v in groups]
            
            col=0
            for i in range(0,len(group_field_label)):
                worksheet[0].write(row,col, group_field_label[i] or '',main_label_format)
                col+=1
            row+=1
            for result in results:
                col=0
                las_col = (len(group_field_label)//2) + 1
                if isinstance(result[rec.group_by_field_id.name], tuple):
                    worksheet[0].merge_range(row,col,row,las_col, result[rec.group_by_field_id.name][1] or '',group_format)
                else:
                    worksheet[0].merge_range(row,col,row,las_col, result[rec.group_by_field_id.name] or '',group_format)
                row+=1
                if rec.sub_group_by_field_id:
                    sub_new_lst=sorted(result['values'],key=itemgetter(rec.sub_group_by_field_id.name))
                    sub_groups = itertools.groupby(sub_new_lst, key=operator.itemgetter(rec.sub_group_by_field_id.name))
                    sub_results = [{rec.sub_group_by_field_id.name:k,'values':[x for x in v]} for k, v in sub_groups]
                    for sub_result in sub_results:
                        col=0
                        las_col = (len(group_field_label)//2) + 1
                        group_format = workbook.add_format()
                        group_format = self.set_group_format(rec,group_format,bg_color=rec.sub_group_set_bg_color)
                        if isinstance(sub_result[rec.sub_group_by_field_id.name], tuple):
                            worksheet[0].merge_range(row,col,row,las_col, sub_result[rec.sub_group_by_field_id.name][1] or '',group_format)
                        else:
                            worksheet[0].merge_range(row,col,row,las_col, sub_result[rec.sub_group_by_field_id.name] or '',group_format)
                        if rec.third_group_by_field_id:
                            row+=1
                            third_new_lst=sorted(sub_result['values'],key=itemgetter(rec.third_group_by_field_id.name))
                            third_groups = itertools.groupby(third_new_lst, key=operator.itemgetter(rec.third_group_by_field_id.name))
                            third_results = [{rec.third_group_by_field_id.name:k,'values':[x for x in v]} for k, v in third_groups]
                            for third_result in third_results:
                                col=0
                                las_col = (len(group_field_label)//2) + 1
                                group_format = workbook.add_format()
                                group_format = self.set_group_format(rec,group_format,bg_color=rec.third_group_set_bg_color)
                                if isinstance(third_result[rec.third_group_by_field_id.name], tuple):
                                    worksheet[0].merge_range(row,col,row,las_col, third_result[rec.third_group_by_field_id.name][1] or '',group_format)
                                else:
                                    worksheet[0].merge_range(row,col,row,las_col, third_result[rec.third_group_by_field_id.name] or '',group_format)
                                group_format = workbook.add_format()
                                group_format = self.set_group_format(rec,group_format)
                                row+=1
                                for val in third_result['values']:
                                    col=0
                                    for g_field in g_label:
                                        main_val_format = workbook.add_format()
                                        main_val_format = self.set_main_val_format(rec,main_val_format)
                                        if isinstance(val[g_field], float) or isinstance(val[g_field], int):
                                            if str(col) in sum_dic:
                                                if val[g_field]:
                                                    sum_dic[str(col)] += val[g_field]
                                            main_val_format = workbook.add_format()
                                            main_val_format = self.set_main_val_format(rec,main_val_format,'right')
                                            worksheet[0].write(row,col, format((val[g_field]),'.2f') or 0.00,main_val_format)
                                        else:
                                            if str(col) in sum_dic:
                                                if val[g_field]:
                                                    sum_dic[str(col)] += val[g_field]
                                            worksheet[0].write(row,col, val[g_field] or '',main_val_format)
                                            main_val_format = workbook.add_format()
                                            main_val_format = self.set_main_val_format(rec,main_val_format)
                                        col+=1
                                    row+=1
                                if rec.is_sum:
                                    for ran in range(0,len(group_field_label)):
                                        if str(ran) in sum_dic:
                                            group_format = workbook.add_format()
                                            group_format = self.set_group_format(rec,group_format,'right',rec.total_color,rec.total_font_color)
                                            worksheet[0].write(row,ran, format((sum_dic[str(ran)]),'.2f') or 0.00,group_format)
                                            group_format = workbook.add_format()
                                            group_format = self.set_group_format(rec,group_format)
                                    row+=1
                                    sum_dic=sum_dic.fromkeys(sum_dic, 0)
                                
                            
                        else:
                            group_format = workbook.add_format()
                            group_format = self.set_group_format(rec,group_format)
                            row+=1
                            for val in sub_result['values']:
                                col=0
                                for g_field in g_label:
                                    main_val_format = workbook.add_format()
                                    main_val_format = self.set_main_val_format(rec,main_val_format)
                                    if isinstance(val[g_field], float) or isinstance(val[g_field], int):
                                        if str(col) in sum_dic:
                                            if val[g_field]:
                                                sum_dic[str(col)] += val[g_field]
                                        main_val_format = workbook.add_format()
                                        main_val_format = self.set_main_val_format(rec,main_val_format,'right')
                                        worksheet[0].write(row,col, format((val[g_field]),'.2f') or 0.00,main_val_format)
                                    else:
                                        if str(col) in sum_dic:
                                            if val[g_field]:
                                                sum_dic[str(col)] += val[g_field]
                                        worksheet[0].write(row,col, val[g_field] or '',main_val_format)
                                        main_val_format = workbook.add_format()
                                        main_val_format = self.set_main_val_format(rec,main_val_format)
                                    col+=1
                                row+=1
                            if rec.is_sum:
                                for ran in range(0,len(group_field_label)):
                                    if str(ran) in sum_dic:
                                        group_format = workbook.add_format()
                                        group_format = self.set_group_format(rec,group_format,'right',rec.total_color,rec.total_font_color)
                                        worksheet[0].write(row,ran, format((sum_dic[str(ran)]),'.2f') or 0.00,group_format)
                                        group_format = workbook.add_format()
                                        group_format = self.set_group_format(rec,group_format)
                                row+=1
                                sum_dic=sum_dic.fromkeys(sum_dic, 0)
                else:
                    for val in result['values']:
                        col=0
                        for g_field in g_label:
                            main_val_format = workbook.add_format()
                            main_val_format = self.set_main_val_format(rec,main_val_format)
                            if isinstance(val[g_field], float) or isinstance(val[g_field], int):
                                if str(col) in sum_dic:
                                    if val[g_field]:
                                        sum_dic[str(col)] += val[g_field]
                                main_val_format = workbook.add_format()
                                main_val_format = self.set_main_val_format(rec,main_val_format,'right')
                                worksheet[0].write(row,col, format((val[g_field]),'.2f') or 0.00,main_val_format)
                            else:
                                if str(col) in sum_dic:
                                    if val[g_field]:
                                        sum_dic[str(col)] += val[g_field]
                                worksheet[0].write(row,col, val[g_field] or '',main_val_format)
                                main_val_format = workbook.add_format()
                                main_val_format = self.set_main_val_format(rec,main_val_format)
                            col+=1
                        row+=1
                    if rec.is_sum:
                        for ran in range(0,len(group_field_label)):
                            if str(ran) in sum_dic:
                                group_format = workbook.add_format()
                                group_format = self.set_group_format(rec,group_format,'right',rec.total_color,rec.total_font_color)
                                worksheet[0].write(row,ran, format((sum_dic[str(ran)]),'.2f') or 0.00,group_format)
                                group_format = workbook.add_format()
                                group_format = self.set_group_format(rec,group_format)
                        row+=1
                        sum_dic=sum_dic.fromkeys(sum_dic, 0)
        else:
            #This section for the other 
            if rec.relational_field:
                # set the line label Format
                line_label_format = workbook.add_format()
                line_label_format = self.set_line_label_format(rec,line_label_format)
                
                # set the line val format
                line_val_format = workbook.add_format()
                line_val_format = self.set_line_val_format(rec,line_val_format)
                
           
            sheet_i = 0
            label_count = 0
            for model_id in obj_ids:
                if rec.split_sheet and rec.relational_field:
                    she_name=rec.file_name+'-'+str(sheet_i)
                    worksheet[sheet_i] = workbook.add_worksheet(she_name)
                    worksheet[sheet_i].set_column(0, 30, 10)
                    row=1
                    if rec.print_company_detail:
                        row=0
                        company = self.env.user.company_id
                        worksheet[sheet_i].merge_range(row, 0, row, 1, company.name or '',company_format)
                        row+=1
                        worksheet[sheet_i].merge_range(row, 0, row, 1, company.street or '',company_format)
                        row+=1
                        if company.street2:
                            worksheet[sheet_i].merge_range(row, 0, row, 1, company.street2 or '',company_format)
                            row+=1
                        if company.city or company.zip:
                            city=''
                            if company.city:
                                city = company.city
                            if company.zip:
                                if city:
                                    city = city + '-' + company.zip
                                else:
                                    city = company.zip
                            worksheet[sheet_i].merge_range(row, 0, row, 1, city or '',company_format)
                            row+=1
                        if company.country_id:
                            worksheet[sheet_i].merge_range(row, 0, row, 1, company.country_id.name or '',company_format)
                            row+=1
                    if rec.header_text:
                        worksheet[sheet_i].merge_range(0, 1, 1, 7, rec.header_text,header_format)
                    row+=1
                    
                main_vals= self.get_main_field_values(model_id,field_val)
                if rec.template == 'template1' and not rec.relational_field:
                    if label_count == 0:
                        col=0
                        for i in range(0,len(main_field_label)):
                            worksheet[sheet_i].write(row,col, main_field_label[i] or '',main_label_format)
                            col+=1
                        row+=1
                        label_count +=1
                    col=0
                    for i in range(0,len(main_vals)):
                        if str(i) in main_line_sum_dic:
                            if main_vals[i]:
                                main_line_sum_dic[str(i)] += main_vals[i]
                        if isinstance(main_vals[i], float):
                            main_val_format = workbook.add_format()
                            main_val_format = self.set_main_val_format(rec,main_val_format,'right')
                            worksheet[sheet_i].write(row,col, format((main_vals[i]),'.2f') or 0.00,main_val_format)
                        elif isinstance(main_vals[i], int):
                            main_val_format = workbook.add_format()
                            main_val_format = self.set_main_val_format(rec,main_val_format,'right')
                            worksheet[sheet_i].write(row,col, format((main_vals[i]),'.2f') or 0.00,main_val_format)
                        else:
                            worksheet[sheet_i].write(row,col, main_vals[i] or '',main_val_format)
                        main_val_format = workbook.add_format()
                        main_val_format = self.set_main_val_format(rec,main_val_format)
                        col+=1
                    row+=1  
                    continue
                elif rec.template == 'template1':
                    col=0
                    for i in range(0,len(main_field_label)):
                        worksheet[sheet_i].write(row,col, main_field_label[i] or '',main_label_format)
                        col+=1
                    if len(main_field_label) > 0:
                        row+=1
                    col=0
                    for i in range(0,len(main_vals)):
                        if isinstance(main_vals[i], float):
                            main_val_format = workbook.add_format()
                            main_val_format = self.set_main_val_format(rec,main_val_format,'right')
                            worksheet[sheet_i].write(row,col, format((main_vals[i]),'.2f') or 0.00,main_val_format)
                        elif isinstance(main_vals[i], int):
                            main_val_format = workbook.add_format()
                            main_val_format = self.set_main_val_format(rec,main_val_format,'right')
                            worksheet[sheet_i].write(row,col, format((main_vals[i]),'.2f') or 0.00,main_val_format)
                        else:
                            worksheet[sheet_i].write(row,col, main_vals[i] or '',main_val_format)
                        main_val_format = workbook.add_format()
                        main_val_format = self.set_main_val_format(rec,main_val_format)
                        col+=1
                    if len(main_vals) > 0:
                        row+=2
                else:
                    half = len(main_field_label)//2
                    count =0
                    my_row=row
                    for i in range(0,half):
                        col=1
                        worksheet[sheet_i].write(my_row,col, main_field_label[count] or '',main_label_format)
                        col+=1
                        if isinstance(main_vals[i], float):
                            main_val_format = workbook.add_format()
                            main_val_format = self.set_main_val_format(rec,main_val_format,'right')
                            worksheet[sheet_i].write(my_row,col, format((main_vals[i]),'.2f') or 0.00,main_val_format)
                        elif isinstance(main_vals[i], int):
                            main_val_format = workbook.add_format()
                            main_val_format = self.set_main_val_format(rec,main_val_format,'right')
                            worksheet[sheet_i].write(my_row,col, format((main_vals[i]),'.2f') or 0.00,main_val_format)
                        else:
                            worksheet[sheet_i].write(my_row,col, main_vals[i] or 0.00,main_val_format)
                        main_val_format = workbook.add_format()
                        main_val_format = self.set_main_val_format(rec,main_val_format)
                            
                        count+=1
                        my_row+=1
                    for i in range(half,len(main_field_label)):
                        col=4
                        worksheet[sheet_i].write(row,col, main_field_label[count] or '',main_label_format)
                        col+=1
                        if isinstance(main_vals[count], float):
                            main_val_format = workbook.add_format()
                            main_val_format = self.set_main_val_format(rec,main_val_format,'right')
                            worksheet[sheet_i].write(row,col, format((main_vals[count]),'.2f') or 0.00,main_val_format)
                        elif isinstance(main_vals[count], int):
                            main_val_format = workbook.add_format()
                            main_val_format = self.set_main_val_format(rec,main_val_format,'right')
                            worksheet[sheet_i].write(row,col, format((main_vals[count]),'.2f') or 0.00,main_val_format)
                        else:
                            worksheet[sheet_i].write(row,col, main_vals[count] or '',main_val_format)
                        main_val_format = workbook.add_format()
                        main_val_format = self.set_main_val_format(rec,main_val_format)
                        count+=1
                        row+=1
                    row+=1
                if rec.relational_field and rec.relational_fields_ids:
                    model = self.env[rec.relational_model_id.model]
                    line=model_id.read([rec.relational_field.name])
                    line_ids=model.browse(line[0].get(rec.relational_field.name))
                    
                    res= self.get_main_field_label(rec.relational_fields_ids)
                    line_field_val = res.get('field_val')
                    line_field_label = res.get('main_field_label')
                    line_sum_dic = res.get('line_sum_dic')
                    col=0
                    if rec.print_counter_column:
                        worksheet[sheet_i].write(row,col,'No#',line_label_format)
                        col+=1
                    for i in range(0,len(line_field_label)):
                        worksheet[sheet_i].write(row,col, line_field_label[i] or '',line_label_format)
                        col+=1
                    if rec.line_label_set_height > 0:
                        worksheet[sheet_i].set_row(0, rec.line_label_set_height)
                    row+=1
                    if rec.print_counter_column:
                        c=0
                    line_main_val=[]
                    for line in line_ids:
                        line_main_val = self.get_main_field_values(line,line_field_val)
                        col=0
                        if rec.print_counter_column:
                            c += 1
                            worksheet[sheet_i].write(row,col,c or '',line_val_format)
                            col+=1
                        for i in range(0,len(line_main_val)):
                            if str(i) in line_sum_dic:
                                if line_main_val[i] and isinstance(line_main_val[i], (int, float)):
                                    line_sum_dic[str(i)] += line_main_val[i]
                            if isinstance(line_main_val[i], float):
                                line_val_format = workbook.add_format()
                                line_val_format = self.set_line_val_format(rec,line_val_format,'right')
                                worksheet[sheet_i].write(row,col,format((line_main_val[i]),'.2f') or '',line_val_format)
                            elif isinstance(line_main_val[i], int):
                                line_val_format = workbook.add_format()
                                line_val_format = self.set_line_val_format(rec,line_val_format,'right')
                                worksheet[sheet_i].write(row,col,format((line_main_val[i]),'.2f') or '',line_val_format)
                            elif isinstance(line_main_val[i], datetime.datetime):
                                line_val_format = workbook.add_format()
                                line_val_format = self.set_line_val_format(rec, line_val_format, 'left')
                                worksheet[sheet_i].write(row, col, datetime.datetime.strftime(line_main_val[i], DEFAULT_SERVER_DATETIME_FORMAT) or '',
                                                         line_val_format)
                            elif isinstance(line_main_val[i], datetime.date):
                                line_val_format = workbook.add_format()
                                line_val_format = self.set_line_val_format(rec, line_val_format, 'right')
                                worksheet[sheet_i].write(row, col, datetime.datetime.strftime(line_main_val[i], DEFAULT_SERVER_DATE_FORMAT) or '',
                                                         line_val_format)
                            else:
                                worksheet[sheet_i].write(row,col,line_main_val[i] or '',line_val_format)
                            line_val_format = workbook.add_format()
                            line_val_format = self.set_line_val_format(rec,line_val_format)
                            col+=1
                        row+=1
                    if rec.is_sum:
                        for sum_i in range(0,len(line_main_val)):
                            if str(sum_i) in line_sum_dic:
                                line_val_format = workbook.add_format()
                                line_val_format = self.set_line_val_format(rec,line_val_format,'right',True, rec.total_color, rec.total_font_color)
                                if rec.print_counter_column:
                                    worksheet[sheet_i].write(row,sum_i+1,format((line_sum_dic[str(sum_i)]),'.2f') or '',line_val_format)
                                else:
                                    worksheet[sheet_i].write(row, sum_i,format((line_sum_dic[str(sum_i)]), '.2f') or '',line_val_format)
                                line_val_format = workbook.add_format()
                                line_val_format = self.set_line_val_format(rec,line_val_format)
                        row+=1
                        line_sum_dic.fromkeys(line_sum_dic, 0)
                row+=2
                 
                if rec.split_sheet and rec.relational_field:
                    sheet_i += 1
        
            #For Sum of all main line
            if rec.template == 'template1' and not rec.relational_field and rec.is_sum:
                for sum_i in range(0,len(main_vals)):
                    if str(sum_i) in main_line_sum_dic:
                        main_val_format = workbook.add_format()
                        main_val_format = self.set_main_val_format(rec,main_val_format,'right',True,rec.total_color, rec.total_font_color)
                        worksheet[sheet_i].write(row,sum_i,format((main_line_sum_dic[str(sum_i)]),'.2f') or '',main_val_format)
                        main_val_format = workbook.add_format()
                        main_val_format = self.set_main_val_format(rec,main_val_format,'right',True)
                row+=1
                main_line_sum_dic.fromkeys(main_line_sum_dic, 0)

        workbook.close()
        xlsx_data = output.getvalue()
        export_id = self.env['dev.export.file.excel'].create({ 'excel_file': base64.encodestring(xlsx_data),'file_name': f_name})
        return {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'dev.export.file.excel',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
        
dev_export_wizard()


class dev_export_file_excel(models.TransientModel):
    _name= "dev.export.file.excel"
    
    excel_file = fields.Binary('Export Excel')
    file_name = fields.Char('Export Excel')

dev_export_file_excel()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: 
