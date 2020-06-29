from odoo import models, fields, api
from datetime import datetime, timedelta
import datetime
from odoo.addons import decimal_precision as dp
from calendar import monthrange


class RequisitionProcessLine(models.Model):
    _name = "requisition.process.line.ept"
    _description = "Reorder Process Line"
    
    can_be_update = fields.Boolean(string='Allow to Update Adjusted Qty', default=True)
    
    qty_available_for_sale = fields.Integer(string='Qty Available to Sale')
    requisition_qty = fields.Integer(string="Demanded Quantity")
    forecasted_stock = fields.Integer(string='Forecasted Stock')
    adjusted_requisition_qty = fields.Integer(string='Adjusted Demand',)
    expected_sale = fields.Integer(string="Expected Sale")
    
    sharing_percent = fields.Float(string="Sharing Percentage", digits=dp.get_precision('Payment Terms'))
    opening_stock = fields.Float(string="Opening Stock")
    
    state = fields.Selection([('draft', 'Draft'), ('generated', 'Calculated'), ('approved' , 'Approved')], string='Status', default='draft', index=True)
   
    warehouse_id = fields.Many2one('stock.warehouse', string='Requested Warehouse', index=True)
    requisition_process_id = fields.Many2one('requisition.process.ept', string='Reorder Process', index=True)
    product_id = fields.Many2one('product.product', string="Product", index=True)
    configuraiton_line_id = fields.Many2one('requisition.configuration.line.ept', string='Reorder Planning', index=True)
    requisition_summary_id = fields.Many2one('requisition.summary.line.ept', string='Reorder Summary')
   
   
   
   
    @api.multi
    def get_data_for_subframes(self, date_start, date_stop, is_first_frame=False, last_dic_data={}):
        past_sale_start_date = self.requisition_process_id.requisition_past_sale_start_from or fields.Date.context_today(self)
        moves = self.get_moves(date_start, date_stop)
        dateframes = {}
        sales_subframes = {}
        incoming_stock_frames = {}
        opening_closing_frames = {}
        date_list = [date_start]
        frame_number = 0
        recent_date = date_start
        if moves:
            incoming_stock_frames.update({frame_number + 1: 0})
            if is_first_frame:
                op_stock = self.get_net_on_hand_qty()
                opening_closing_frames.update({frame_number + 1 : {'opening_stock' : op_stock, 'closing_stock' : 0.0, 'sales' : 0}})
            for move in moves:
                dt = datetime.datetime.strptime(str(move.date_expected), "%Y-%m-%d %H:%M:%S")
                date_expected = dt.strftime("%Y-%m-%d")
                if date_expected not in date_list:
                    date_list.append(date_expected)
#                     date_list.append(move.date_expected)
#                     dt = datetime.datetime.strptime(str(move.date_expected), "%Y-%m-%d %H:%M:%S")
#                     date_expected = dt.strftime("%Y-%m-%d")
                    if not recent_date == date_expected:
                        date_expected = (dt - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                    frame_number = frame_number + 1
                    dateframes.update({frame_number : (recent_date, date_expected)})
                    recent_date = dt.strftime("%Y-%m-%d")
#                     if frame_number == 1:
#                         incoming_stock_frames.update({frame_number: 0})
#                         if is_first_frame:
#                             op_stock = self.get_net_on_hand_qty()
#                             opening_closing_frames.update({frame_number : {'opening_stock' : op_stock, 'closing_stock' : 0.0, 'sales' : 0}})
                if date_start == date_stop:
                    stock = incoming_stock_frames.get((frame_number), 0.0)
                    incoming_stock_frames.update({(frame_number): stock + move.product_uom_qty})
                else:
                    stock = incoming_stock_frames.get((frame_number + 1), 0.0)
                    incoming_stock_frames.update({(frame_number + 1): stock + move.product_uom_qty})
        
        else:
            incoming_stock_frames.update({frame_number + 1: 0})
            if is_first_frame:
                op_stock = self.get_net_on_hand_qty()
                opening_closing_frames.update({frame_number + 1 : {'opening_stock' : op_stock, 'closing_stock' : 0.0, 'sales' : 0}})
            else:
                if last_dic_data:
                    op_stock = last_dic_data.get('closing_stock', 0.0)
                    opening_closing_frames.update({frame_number + 1 : {'opening_stock' : op_stock, 'closing_stock' : 0.0, 'sales' : 0}})
        
#         if not date_start == date_stop:
        frame_number = frame_number + 1
        dateframes.update({frame_number : (recent_date, date_stop)})
        days_frame = {}
#         for key, value in dateframes.iteritems():
#             # key = Frame  number
#             # value = date range
#             # this dictionary contains 
#             # Key   => sub timeframe number
#             # Value => days for each periods the frame exists
#             days_frame.update({key : self.days_between_sub_timeframe(d1=value[0], d2=value[1])})
#         
    # it's find if both frame start date is same then it will skip 1st frame.
        date_repeat = False
        date1 = ''
        for k in dateframes:
            v = dateframes[k]
            if date1 == v[0]:
                date_repeat = True
            else:
                date1 = v[0]
        
        
        #  use_forecast_sale_for_requisition = self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.use_forecasted_sales_for_requisition')
        
        for key in dateframes:
            value = dateframes[key]
            # key = Frame  number
            # value = date range
            # this dictionary contains 
            # Key   => sub timeframe number
            # Value => days for each periods the frame exists
            
            if date_repeat == True and key == 1:
                days_frame.update({key : self.days_between_sub_timeframe(d1=value[0], d2=value[1], repeat_date=True, forecast_sale=self.requisition_process_id.is_use_forecast_sale_for_requisition)})
            else:
                days_frame.update({key : self.days_between_sub_timeframe(d1=value[0], d2=value[1], repeat_date=False, forecast_sale=self.requisition_process_id.is_use_forecast_sale_for_requisition)})
        

        # #now we need to find the forecasted sales of all timeframes / subtimeframes
        if self.requisition_process_id.is_use_forecast_sale_for_requisition:     
            for k in days_frame:
                subframe_sales = 0
                for key, vals in days_frame[k].items():
                    subframe_sales += float((self.get_forecast_sales(self.product_id.id, self.warehouse_id.id, past_sale_start_date, forecast_sale=self.requisition_process_id.is_use_forecast_sale_for_requisition, period_id=key)) * vals)
                sales_subframes.update({k : subframe_sales})
                stock_frame = opening_closing_frames.get(k, {})
                if stock_frame:
                    stock_frame.update({'sales' : subframe_sales, 'forecast_sales' : subframe_sales})
                else:
                    opening_closing_frames.update({k : {'opening_stock' : 0, 'closing_stock' : 0.0, 'sales' : subframe_sales, 'forecast_sales' : subframe_sales}})
        else:
            avg_daily_sale = self.get_forecast_sales(self.product_id.id, self.warehouse_id.id, past_sale_start_date) 
            for k in days_frame:
                v = days_frame[k]
                subframe_sales = 0
                subframe_sales += (avg_daily_sale * v)
                sales_subframes.update({k : subframe_sales})
                stock_frame = opening_closing_frames.get(k, {})
                if stock_frame:
                    stock_frame.update({'sales' : subframe_sales, 'forecast_sales' : subframe_sales})
                else:
                    opening_closing_frames.update({k : {'opening_stock' : 0, 'closing_stock' : 0.0, 'sales' : subframe_sales, 'forecast_sales' : subframe_sales}})                                            
        # # Set opening closing stock
        for key in sales_subframes:
            stock_frame = opening_closing_frames.get(key, {})
            if stock_frame:
                op_stock = 0
                if is_first_frame and key == 1:
                    op_stock = stock_frame.get('opening_stock', 0)
                else:
                    if key == 1 and last_dic_data:
                        op_stock = last_dic_data.get('closing_stock', 0.0)
                    else:
                        op_stock = opening_closing_frames.get(key - 1, {}).get('closing_stock', 0.0)
                
                sales = stock_frame.get('sales', 0)
                forecast_sales = stock_frame.get('forecast_sales', 0.0)
                stock_in = incoming_stock_frames.get(key, 0)
                if is_first_frame:  # and key == 1:
                    sales = sales if (op_stock + stock_in) >= sales else (op_stock + stock_in)
                else:
                    sales = sales - op_stock - stock_in
                    if sales < 0:
                        sales = 0
                cl_stock = op_stock + stock_in - forecast_sales if (op_stock + stock_in - forecast_sales) > 0 else 0
                stock_frame.update({'opening_stock' : op_stock, 'closing_stock' : cl_stock, 'sales' : sales, })
    
        # # returns the dictionaries  
        # # 1). Incoming stock qty for each sub time frame
        # # 2). sub time frames date range (startdate , enddate)
        # # 3). days frame with all periods with the days within the timeframes
        # # 4). Sales of each sub time frames 
        # # 5). Opening Closing timeframes
        
        # return incoming_stock_frames, dateframes, days_frame, sales_subframes, opening_closing_frames
       
        res = {'incoming_stock_frames' : incoming_stock_frames, 'dateframes' : dateframes,
               'days_frame' : days_frame, 'sales_subframes' : sales_subframes,
               'opening_closing_frames' : opening_closing_frames, 'frame_number':frame_number}
        return res
    
    
    
    
      
    @api.multi
    def get_moves(self, stare_date, end_date):
        move_obj = self.env['stock.move']
        moves = move_obj.browse([])
        for line in self :
            dest_location_ids = self.env['stock.location'].search([('location_id', 'child_of', line.warehouse_id.view_location_id.id), ('usage', '=', 'internal')])
            domain = [('date_expected', '>=', stare_date), ('date_expected', '<=', end_date),
                      ('location_dest_id', 'in', dest_location_ids and dest_location_ids.ids or []), ('state', '=', 'assigned'),
                      ('product_id', '=', line.product_id.id)]
            moves += move_obj.search(domain, order='date_expected')
        return moves
    
    
        
    @api.multi
    def get_net_on_hand_qty(self):
        if self._context.get('from_get_requisition_file', False):
            return self.opening_stock
        else:
            product = self.product_id.with_context({'warehouse':self.warehouse_id.id})
            qty_available = product.qty_available
            outgoing = product.outgoing_qty
            net_on_hand = qty_available - outgoing
            return net_on_hand
    
    
    
    
    @api.multi
    def days_between_sub_timeframe(self, d1=False, d2=False, repeat_date=False, forecast_sale=False):
        d1_obj = datetime.datetime.strptime(str(d1), "%Y-%m-%d")
        d2_obj = datetime.datetime.strptime(str(d2), "%Y-%m-%d")
        if forecast_sale:
            res = {}
            dt = d1_obj
            while dt <= d2_obj:
                period = self.env['requisition.period.ept'].find(dt=dt)
                temp_obj = datetime.datetime.strptime(str(period.date_stop), "%Y-%m-%d")
                if temp_obj > d2_obj:
                    temp_obj = d2_obj
                if repeat_date == True :    
                    res.update({period.id : abs((temp_obj - dt).days)})
                else:
                    res.update({period.id : abs((temp_obj - dt).days) + 1})
                dt = temp_obj + datetime.timedelta(days=1)
        else:
            res = 0
            if d1 and d2 :
                res = abs((d2_obj - d1_obj + timedelta(days=1)).days)
        return res
   
   
    @api.multi
    def get_forecast_sales(self, product_id, warehouse_id, past_sale_start_date, forecast_sale=False, period_id=None):
        warehouse = self.env['stock.warehouse'].browse(warehouse_id)
        if forecast_sale:
            sales = self.env['forecast.sale.ept'].search([('period_id', '=', period_id), ('product_id', '=', product_id), ('warehouse_id', '=', warehouse_id)])
            if not sales:
                return 0.0
            forecast_sales = 0
            for sale in sales:
                forecast_sales += sale.forecast_sales
            dt = datetime.datetime.strptime(str(sale.period_id.date_start), "%Y-%m-%d")
            month_days = monthrange(dt.year, dt.month)[1]
            return forecast_sales / month_days
        else:
            start_date = past_sale_start_date or fields.Date.context_today(self) - timedelta(1)
            start_date_obj = datetime.datetime.strptime(str(start_date), "%Y-%m-%d")
            forecast_sales = 0.0
            past_days = int(self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.requisition_sales_past_days') or 1)
            reorder_last_date = (start_date_obj - timedelta(days=past_days)).strftime("%Y-%m-%d")
            sales = self.env['stock.move'].search([('product_id', '=', product_id), ('date', '>=', reorder_last_date), ('date', '<=', start_date), ('state', '=', 'done'), ('location_dest_id.usage', '=', 'customer'), ('location_id', 'child_of', warehouse and warehouse.view_location_id.id)])
            for sale in sales:
                # order qty is removed in V12
                forecast_sales += sale.product_qty
            if not past_days :
                past_days = 1
            return (forecast_sales / past_days)
   
   
