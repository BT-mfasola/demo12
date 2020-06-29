from odoo import api, fields, models
from datetime import datetime, date , timedelta
import xlsxwriter
import base64
import time
from io import BytesIO


class ExportRequistionDemand(models.TransientModel):
    _name = 'export.requistion.demand.ept'
    _description = "Demand Calculation Detail"
    
    
    
    datas = fields.Binary("File")
    is_use_forecast_sale_for_requisition = fields.Boolean("Use Forecast sale")        
    
    requisition_date = fields.Date(string='Requisition Date', default=date.today())
    past_sales_start_date = fields.Date(string="Past Sales Start Date", default=date.today())
    
    estimate_delivery_time = fields.Integer(string="Estimate Delivery Time")
    backup_days = fields.Integer(string="Keep Stock of X Days", default=lambda self: self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.default_requisition_backup_stock_days') or 1)
    
    
    product_id = fields.Many2one('product.product', string="Product")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")
    requisition_process_id = fields.Many2one('requisition.process.ept')
    warehouse_requisition_process_id = fields.Many2one('warehouse.requisition.process.ept')



    @api.onchange('requisition_process_id')
    def onchange_requisition_process(self):
        requisition_process_obj = self.env['requisition.process.ept']
        warehouse_id = []
        if self._context.get('is_default_requisition_process_id'):
            requisition_process_id = self._context.get('is_default_requisition_process_id', False)
            requisition_process = requisition_process_obj.browse(requisition_process_id)
            product_ids = requisition_process and requisition_process.product_ids.ids  or []
            if len(product_ids) == 1:
                self.product_id = requisition_process.product_ids.id
            confiuration_line_ids = requisition_process and requisition_process.configuration_line_ids or []
            for line in confiuration_line_ids:
                warehouse_id.append(line.warehouse_id.id)
                
            if len(warehouse_id) == 1:
                self.warehouse_id = confiuration_line_ids.warehouse_id.id    
            self.requisition_date = requisition_process and requisition_process.requisition_date or False
            self.is_use_forecast_sale_for_requisition = requisition_process and requisition_process.is_use_forecast_sale_for_requisition or False
            self.past_sales_start_date = requisition_process and requisition_process.requisition_past_sale_start_from
            domain = {'product_id':[('id', 'in', product_ids)], 'warehouse_id':[('id', 'in', warehouse_id)]}
            return{'domain':domain}
            
            
    
            
            
            
    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        requisition_configuration_line_obj = self.env['requisition.configuration.line.ept']
        warehouse_requisition_configuration_line_obj = self.env['warehouse.requisition.configuration.line.ept'] 
          
        if self._context.get('is_default_requisition_process_id'):
            requisition_process_id = self._context.get('is_default_requisition_process_id', False)
            requisition_configuration_line = requisition_configuration_line_obj.search([('requisition_process_id', '=', requisition_process_id), ('warehouse_id', '=', self.warehouse_id.id)])
            self.estimate_delivery_time = requisition_configuration_line.requisition_estimated_delivery_time
            self.backup_days = requisition_configuration_line.requisition_backup_stock_days     
            
        elif self._context.get('is_default_requisition_process_id'):
              
            warehouse_requisition_process_id = self._context.get('is_default_requisition_process_id', False)
            warehouse_requisition_configuration_line = warehouse_requisition_configuration_line_obj.search([('warehouse_requisition_process_id', '=', warehouse_requisition_process_id), ('warehouse_id', '=', self.warehouse_id.id)])
            self.estimate_delivery_time = warehouse_requisition_configuration_line.requisition_estimated_delivery_time
            self.backup_days = warehouse_requisition_configuration_line.requisition_backup_stock_days
            
            
    @api.onchange('warehouse_requisition_process_id')    
    def onchange_warehouse_requisition_process(self):
        warehouse_requisition_process_obj = self.env['warehouse.requisition.process.ept']
        warehouse_id = []
        if self._context.get('is_default_warehouse_requisition_process_id'):
            warehouse_requisition_process_id = self._context.get('is_default_warehouse_requisition_process_id', False)
            warehouse_requisition_process = warehouse_requisition_process_obj.browse(warehouse_requisition_process_id)
            product_ids = warehouse_requisition_process and warehouse_requisition_process.product_ids.ids or []
            if len(product_ids) == 1:
                self.product_id = warehouse_requisition_process.product_ids.id     
            warehouse_configuration_line_ids = warehouse_requisition_process and warehouse_requisition_process.warehouse_configuration_line_ids or []
            for line in warehouse_configuration_line_ids:
                     
                    warehouse_id.append(line.warehouse_id.id)
            if len(warehouse_id) == 1:
                self.warehouse_id = warehouse_configuration_line_ids.warehouse_id.id       
            self.requisition_date = warehouse_requisition_process and warehouse_requisition_process.requisition_date
            self.is_use_forecast_sale_for_requisition = warehouse_requisition_process and warehouse_requisition_process.is_use_forecast_sale_for_requisition or False
            self.past_sales_start_date = warehouse_requisition_process and warehouse_requisition_process.requisition_past_sale_start_from         
            domain = {'product_id':[('id', 'in', product_ids)], 'warehouse_id':[('id', 'in', warehouse_id)]}
            return{'domain':domain}
            
            
            
    @api.multi
    def check_forecasted_data(self, product_ids, period_ids, warehouse_ids):
        mismatch_data_obj = self.env['mismatch.data.ept']
        if  self.requisition_process_id.is_use_forecast_sale_for_requisition or self.warehouse_requisition_process_id.is_use_forecast_sale_for_requisition:

            list_of_warehouse_ids = []
            list_of_warehouse_ids.append(warehouse_ids)
            product_ids_str = '(' + str(product_ids or [0]).strip('[]') + ')'
          
            period_ids_str = '(' + str(period_ids or [0]).strip('[]') + ')'
            warehouse_ids_str = '(' + str(list_of_warehouse_ids or [0]).strip('[]') + ')'
            not_found_lines = []         
            not_found_query = """
                    Select 
                        product.id as product_id, 
                        warehouse.id as warehouse_id,
                        period.id as period_id
                    From 
                        product_product product, stock_warehouse warehouse, requisition_period_ept period
                    Where 
                        product.id in %s And 
                        warehouse.id in %s And 
                        period.id in %s
                    
                    Except
                    
                    Select 
                        product_id, 
                        warehouse_id, 
                        period_id
                    from forecast_sale_ept
                    Where 
                        product_id in %s And 
                        warehouse_id in %s And 
                        period_id in %s
                        
                """ % (str(product_ids_str), str(warehouse_ids_str), str(period_ids_str) , str(product_ids_str), str(warehouse_ids_str), str(period_ids_str))
            
            self._cr.execute(not_found_query)
            res_dict = self._cr.dictfetchall()
            if res_dict:
                for record in res_dict:
                    not_found_lines.append((0, 0, record))
            if not_found_lines:
                vals = {
                        'requisition_process_id' : self.requisition_process_id.id,
                        'mismatch_lines' : not_found_lines,
                        'warehouse_ids' : [(6, 0, list_of_warehouse_ids)]
                        }
                mismatch = mismatch_data_obj.create(vals)
                if mismatch:
                    return mismatch.wizard_view()     
                
                
                
                
                
    @api.multi
    def action_calculate_demand(self):
        requisition_period_obj = self.env['requisition.period.ept']
        warehouse_requisition_process_obj = self.env['warehouse.requisition.process.line.ept']
        requisition_process_line_obj = self.env['requisition.process.line.ept']
        forecast_sale_obj = self.env['forecast.sale.ept']
        
        
        self.ensure_one()
        if self.is_use_forecast_sale_for_requisition:
            total_time = self.backup_days + self.estimate_delivery_time
            total = datetime.strptime(str(self.requisition_date), '%Y-%m-%d').date() + timedelta(days=int(total_time))
            requisition_period_ids = requisition_period_obj.search([('date_start', '<=', total), ('date_stop', '>=', self.requisition_date)])
            mismatch_data = self.check_forecasted_data(self.product_id.id, requisition_period_ids.ids, self.warehouse_id.id)
            if mismatch_data:
                return mismatch_data
            
        t1_last_dic_data = {}
        t1_date_start = self.requisition_date or  time.strftime('%Y-%m-%d')
        d1 = datetime.strptime(str(t1_date_start), "%Y-%m-%d")
        requisition_date = d1.date()
        estimate_delivery_time = self.estimate_delivery_time - 1
        t1_date_stop = requisition_date + timedelta(days=estimate_delivery_time)
        end_date = t1_date_stop.strftime("%Y-%m-%d")
        date_stop = (t1_date_stop + timedelta(days=1))
        
        # t2_date calculation
        t2_date_start = date_stop.strftime("%Y-%m-%d")
        t2_date_stop = date_stop + timedelta(days=self.backup_days - 1)
        t2_date_stop = t2_date_stop.strftime("%Y-%m-%d")
        
        ctx = self.env.context.copy()
        ctx.update({'from_get_requisition_file':True}) 
        if self._context.get('is_default_warehouse_requisition_process_id'):
            warehouse_requisition_process_id = self._context.get('default_warehouse_requisition_process_id')
            warehouse_requisition_process_line = warehouse_requisition_process_obj.search([('warehouse_id', '=', self.warehouse_id.id), ('product_id', '=', self.product_id.id), ('warehouse_requisition_process_id', '=', warehouse_requisition_process_id)])
            t1_dict = warehouse_requisition_process_line.with_context(ctx).get_data_for_subframes(str(t1_date_start), end_date, is_first_frame=True)
            t1_opening_closing_frames = t1_dict.get('opening_closing_frames', {})
            frame_list = t1_opening_closing_frames.keys()
            if frame_list:
                t1_last_dic_data = t1_opening_closing_frames.get(max(frame_list), {})
              
            t2_dict = warehouse_requisition_process_line.get_data_for_subframes(t2_date_start, t2_date_stop, is_first_frame=False, last_dic_data=t1_last_dic_data)
            
        elif self._context.get('is_default_requisition_process_id'):
            
            requisition_process_id = self._context.get('is_default_requisition_process_id')
            requisition_process_line = requisition_process_line_obj.search([('warehouse_id', '=', self.warehouse_id.id), ('product_id', '=', self.product_id.id), ('requisition_process_id', '=', requisition_process_id)])
            t1_dict = requisition_process_line.with_context(ctx).get_data_for_subframes(str(t1_date_start), end_date, is_first_frame=True)
            t1_opening_closing_frames = t1_dict.get('opening_closing_frames', {})
            frame_list = t1_opening_closing_frames.keys()
            if frame_list:
                t1_last_dic_data = t1_opening_closing_frames.get(max(frame_list), {})
            t2_dict = requisition_process_line.get_data_for_subframes(t2_date_start, t2_date_stop, is_first_frame=False, last_dic_data=t1_last_dic_data)
      
        past_days = int(self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.requisition_sales_past_days') or 1)
        
        Avg = 0.0
        # Calculate Average for Sales
        if self.is_use_forecast_sale_for_requisition:
            
            forecaste_sale_list = []
            period_list = []
            Average_list = []
            month_days = []
            period_id_list = set()
            frame = len(t1_dict.get('days_frame').keys()) + len(t2_dict.get('days_frame').keys())
            for key in range(1, frame):

                if key in t1_dict.get('days_frame').keys():   
                    period_id_list.update(t1_dict.get('days_frame')[key].keys())
                if key in t2_dict.get('days_frame').keys():    
                    period_id_list.update(t2_dict.get('days_frame')[key].keys())
                period_ids = list(period_id_list)
            
            period_obj = requisition_period_obj.browse(period_ids)
            for period in period_obj:
                
                sales = forecast_sale_obj.search([('period_id', '=', period.id), ('product_id', '=', self.product_id.id), ('warehouse_id', '=', self.warehouse_id.id)])
                if not sales:
                    return 0.0
                forecast_sales = 0
                for sale in sales:
                    forecast_sales += sale.forecast_sales
                    forecaste_sale_list.append(forecast_sales)
                period_list.append(period.name)
                days = period.month_days
                month_days.append(days)
                Average_list.append(forecast_sales / days)
                    
        else:    
            if self._context.get('is_default_warehouse_requisition_process_id'):
                
                Avg = warehouse_requisition_process_line.get_forecast_sales(self.product_id.id, self.warehouse_id.id, self.past_sales_start_date)
            elif self._context.get('is_default_warehouse_requisition_process_id'):
                Avg = requisition_process_line_obj.get_forecast_sales(self.product_id.id, self.warehouse_id.id, self.past_sales_start_date)
           
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        col = 0
        row = 0
        
        data = []
        t1_frame_list = []
        header1 = ["Product", self.product_id.name]
        headers = ["Frames", "Start Date", "Days", "End Date", "Days", "Opening Stock", "Incoming", "Forcasted Sale", "Sales", "Closing"]
        header2 = headers[:]
        if  not self.is_use_forecast_sale_for_requisition: 
            header1.append("Days")
            header1.append("Sales")
            header1.append("Average")
            header2.insert(5, "ADS")
            data.append(past_days)
            data.append(int(Avg * past_days))
            data.append(Avg)
      
          
        for i, header in enumerate(header1):
            worksheet.write(0, i, header)
        
        row = row + 1
        worksheet.write_row(row, col + 2, data)

        row = row + 4    
        worksheet.write_row(row, col, header2)   
        
        row = row + 1
        
        if self.is_use_forecast_sale_for_requisition:
            t1_days = {}
            t2_days = {}
            for key in t1_dict.get('days_frame').keys():
                d = t1_dict.get('days_frame')[key].values()
                t1_days.update({key:sum(d)})
            t1_dict.update({'days_frame':t1_days})
            
            for key in t2_dict.get('days_frame').keys():
                d = t2_dict.get('days_frame')[key].values()
                t2_days.update({key:sum(d)})
            t2_dict.update({'days_frame':t2_days})   
             
        # prepare dict for t1 frame
        for key in range(1, t1_dict.get('frame_number') + 1):
            
            if len(t1_dict.get('days_frame')) == 1:
                t1_frame_list.append('T1')
            else:
                t1_frame_list.append('T1.' + str(key))    
        
            t1_frame_list.append(t1_dict.get('dateframes')[key][0])
            t1_frame_list.append("")
            t1_frame_list.append(t1_dict.get('dateframes')[key][1])
            t1_frame_list.append(t1_dict.get('days_frame')[key])
            t1_frame_list.append(t1_dict.get('opening_closing_frames')[key].get('opening_stock'))
            t1_frame_list.append(t1_dict.get('incoming_stock_frames')[key])
            t1_frame_list.append(t1_dict.get('opening_closing_frames')[key].get('forecast_sales'))
            t1_frame_list.append(t1_dict.get('opening_closing_frames')[key].get('sales'))
            t1_frame_list.append(t1_dict.get('opening_closing_frames')[key].get('closing_stock'))
            if not self.is_use_forecast_sale_for_requisition:
                t1_frame_list.insert(5, Avg)
            
            worksheet.write_row(row, col, t1_frame_list)
            t1_frame_list.clear()
            row = row + 1
            
            
        row = row + 4
        t2_frame_list = []
        for key in range(1, t2_dict.get('frame_number') + 1):
        
            if len(t2_dict.get('days_frame')) == 1:
                t2_frame_list.append('T2')
            else:
                t2_frame_list.append('T2.' + str(key))    
        
            t2_frame_list.append(t2_dict.get('dateframes')[key][0])
            t2_frame_list.append("")
            t2_frame_list.append(t2_dict.get('dateframes')[key][1])
            t2_frame_list.append(t2_dict.get('days_frame')[key])
            t2_frame_list.append(t2_dict.get('opening_closing_frames')[key].get('opening_stock'))
            t2_frame_list.append(t2_dict.get('incoming_stock_frames')[key])
            t2_frame_list.append(t2_dict.get('opening_closing_frames')[key].get('forecast_sales'))
            t2_frame_list.append(t2_dict.get('opening_closing_frames')[key].get('sales'))
            t2_frame_list.append(t2_dict.get('opening_closing_frames')[key].get('closing_stock'))
            if not self.is_use_forecast_sale_for_requisition:
                t2_frame_list.insert(5, Avg)
            worksheet.write_row(row, col, t2_frame_list)
            t2_frame_list.clear()
            row = row + 1

    
        row = row + 3
        
        if self.is_use_forecast_sale_for_requisition:
           # Add forecaste data in excel    
            worksheet.write(row, col, "Warehouse Name")
            worksheet.write(row + 1, col, sales.warehouse_id.name)  
            worksheet.write_row(row, col + 1, period_list)
            worksheet.write_row(row + 1, col + 1, forecaste_sale_list) 
            worksheet.write(row + 2, col, "Month Days") 
            worksheet.write_row(row + 2, col + 1, month_days) 
            worksheet.write(row + 3, col, "ADS")
            worksheet.write_row(row + 3, col + 1, Average_list)
       
        workbook.close()
        output.seek(0)
        output = base64.encodestring(output.read())
        self.write({'datas':output})

        active_id = self.ids[0]
        return {
            'type' : 'ir.actions.act_url',
            'url': 'web/content/?model=export.requistion.demand.ept&field=datas&download=true&id=%s&filename=Export_Reuisition_Demand.xlsx' % (active_id),
            'target': 'new',
        } 

        
