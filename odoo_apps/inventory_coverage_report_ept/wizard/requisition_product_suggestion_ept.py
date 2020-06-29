from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from calendar import monthrange
import math
import xlsxwriter
import base64
from io import BytesIO
from collections import OrderedDict
from itertools import groupby
from operator import itemgetter
from dateutil.relativedelta import relativedelta

class RequisitionProductSuggestion(models.TransientModel):
    _name = 'requisition.product.suggestion.ept'
    _description = "Inventory Coverage Report / Product Recommandation"
    
    @api.model
    def _get_default_backup_stock_days(self):
        backup_days = self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.is_default_requisition_backup_stock_days') 
        return backup_days and backup_days or 60
    
    @api.model
    def get_default_past_sale_start_from(self):
        start_date = fields.Date.context_today(self)
        start_date_obj = datetime.strptime(str(start_date), "%Y-%m-%d")
        start_date_obj = start_date_obj.strftime("%Y-%m-%d")
        return start_date_obj
    
    def default_is_use_forecast_sale_for_requisition(self):
        return eval(self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.use_forecasted_sales_for_requisition'))

    def default_warehouse_ids(self):
        warehouses = self.env['stock.warehouse'].search([])
        return warehouses
    
    @api.model
    def default_report_data_as(self):
        report_data = 'text'
        if self._context.get('default_inventory_coverage') :
            report_data = 'graphics'
        return report_data
 
    
    
    name = fields.Char(string="Name", default="Product Suggestion")
    inventory_analysis_of_x_days = fields.Integer(string="Inventory Analysis of X Days", default=_get_default_backup_stock_days)
    warehouse_ids = fields.Many2many('stock.warehouse', string="Warehouses", default=default_warehouse_ids)
    product_suggestion_line_ids = fields.One2many('requisition.product.suggestion.line.ept', 'product_suggestion_id', string='Product Suggestion Lines')
    is_use_forecast_sale_for_requisition = fields.Boolean("Use Forecast sale For Requisition", default=default_is_use_forecast_sale_for_requisition, copy=False)
    requisition_past_sale_start_from = fields.Date(string='Past Sales Start From', default=get_default_past_sale_start_from)
    product_ids = fields.Many2many('product.product', string="Products to Analyse")
    supplier_suggestion_type = fields.Selection([('quick', 'Quickest'),
                                                 ('cheap', 'Cheapest')], string="Choose Vendor", default='cheap')
    line_detail_ids = fields.One2many('product.suggestion.line.detail.ept', 'product_suggestion_id', string='details')
    product_inventory_coverage_detail_file = fields.Binary("File")
    has_pending_moves = fields.Boolean('Has Pending Moves?', default=False, help="Has Pending Moves to be rescheduled?")
    inventory_coverage = fields.Boolean("Is Inventory Coverage Report?", default=False)
    select_products = fields.Boolean("Choose Products", default=False, help="If want to Get details for only selected products then select products and it will check for selected products only otherwise for all")
    select_warehouses = fields.Boolean("Choose Warehouses", default=False, help="If want to Get details for only selected Warehouses then select Warehouses and it will check for selected Warehouses only otherwise for all")
    show_detailed_report = fields.Boolean("Show Detailed Report", default=True)
    show_products = fields.Selection([('all', 'All'), ('out_of_stock_product', 'Out of Stock Product Only'), ('in_stock_product', 'In Stock Product Only')],
                                     string="Product Visibility", default="all",
                                     help="All : Give Report with all details whether it is in stock or out of stock."
                                            "Out of Stock Product Only : Give Report with Only Out Of Stock Products"
                                            " In Stock Product Only : Give Report with Only In Stock Products"  
                                    )
    include_draft_quotations = fields.Boolean("Include Draft Quotations (Purchase RFQ)")
    check_stock_in_other_warehouses = fields.Boolean("Check Stock in Other Warehouses", default=False, help="If Report is for Out of Stock Products, Check stock Availability in Other Warehouses from chosen Warehouses")
    report_data_as = fields.Selection([('text', 'Text'), ('graphics', 'Graphics')],
                                      default=default_report_data_as,
                                      string="Data Mode"
                                      )
    report_type_as = fields.Selection([('pdf', 'PDF'), ('xlsx', 'XLSX')], default='xlsx', string="Download Report As")

    
    @api.multi
    @api.onchange('show_detailed_report')
    def onchange_show_detailed_report(self):
        for record in self :
            if not record.show_detailed_report :
                record.report_data_as = 'text'
                
    @api.multi
    @api.onchange('show_products')
    def onchange_show_products(self):
        for record in self:
            if record.show_products == 'in_stock_product':
                record.check_stock_in_other_warehouses = False
    
    
    @api.multi
    @api.onchange('report_type_as')
    def onchange_show_report_type_as(self):
        for record in self :
            if record.report_type_as == 'pdf' :
                record.report_data_as = 'text'
    
    @api.multi
    def get_net_on_hand_qty(self, product, warehouse):
        self.ensure_one()
        product = product.with_context({'warehouse':warehouse.id})
        qty_available = product.qty_available
        outgoing = product.outgoing_qty
        net_on_hand = qty_available - outgoing
        return net_on_hand
    
    def get_next_date(self, date, days=1):
        d1_obj = datetime.strptime(str(date), "%Y-%m-%d")  # change for the datatime issue
        d2_obj = d1_obj + timedelta(days=days)
        return d2_obj.strftime("%Y-%m-%d")
    
    
    def get_forecast_sales(self, product, warehouse , forecast_sale=False, past_sale_start_date=None, period_id=None):
        if forecast_sale:
            sales = self.env['forecast.sale.ept'].search([('period_id', '=', period_id), ('product_id', '=', product.id), ('warehouse_id', '=', warehouse.id)])
            if not sales:
                return 0.0
            forecast_sales = 0
            for sale in sales:
                forecast_sales += sale.forecast_sales
            dt = datetime.strptime(str(sale.period_id.date_start), "%Y-%m-%d")
            month_days = monthrange(dt.year, dt.month)[1]
            return forecast_sales / month_days
        else:
            start_date = past_sale_start_date or fields.Date.context_today(self) - timedelta(1)
            start_date_obj = datetime.strptime(str(start_date), "%Y-%m-%d")  # changes for datetime issue
            forecast_sales = 0.0
            past_days = int(self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.requisition_sales_past_days') or 1)
            reorder_last_date = (start_date_obj - timedelta(days=past_days)).strftime("%Y-%m-%d")
            sales = self.env['stock.move'].search([('product_id', '=', product.id), ('date', '>=', reorder_last_date), ('date', '<=', start_date), ('state', '=', 'done'), ('location_dest_id.usage', '=', 'customer'), ('location_id','child_of',warehouse and warehouse.view_location_id.id)])
            for sale in sales:
                #Replace the order_qty ->product_qty (Bcz it's remove in V12)
                forecast_sales += sale.product_qty
            if not past_days :
                past_days = 1
            return (forecast_sales / past_days)
        
    def get_periods_of_date(self, start_date, end_date):
        d1_obj = datetime.strptime(str(start_date), "%Y-%m-%d")  # change for datetime issue
        d2_obj = datetime.strptime(str(end_date), "%Y-%m-%d")  # change for datetime issue
        res = OrderedDict()
        dt = d1_obj
        while dt <= d2_obj:
            period = self.env['requisition.period.ept'].find(dt=dt)
            temp_obj = datetime.strptime(str(period.date_stop), "%Y-%m-%d")
            if temp_obj > d2_obj:
                temp_obj = d2_obj
            res.update({period.id : (dt.strftime("%Y-%m-%d"), temp_obj.strftime("%Y-%m-%d"))})
            dt = temp_obj + timedelta(days=1)
        return res
    
                    
                    
    @api.multi
    def get_moves(self, product, warehouse, start_date, end_date):
        move_obj = self.env['stock.move']
        moves = move_obj.browse([])
        dest_location_ids= self.env['stock.location'].search([('location_id','child_of',warehouse.view_location_id.id),('usage', '=', 'internal')])
        domain = [('date_expected', '>=', start_date), ('date_expected', '<=', end_date),
                  ('location_dest_id', 'in', dest_location_ids and dest_location_ids.ids or []), ('state', '=', 'assigned'),
                  ('product_id', '=', product.id)]
        moves += move_obj.search(domain, order='date_expected')
        return moves
    
    @api.multi
    def get_pending_moves(self, warehouse, product_ids=[]):
        product_ids = product_ids and product_ids or self.product_ids and self.product_ids.ids or []
        current_date = datetime.now().strftime("%Y-%m-%d")
        locations = self.env['stock.location'].search([('location_id','child_of',warehouse.view_location_id.id),('usage', '=', 'internal')])
        domain = [('date_expected', '<', current_date), ('state', '=', 'assigned'),
                  ('location_dest_id', 'in', locations and locations.ids or []),
                  ('product_id', 'in', product_ids)]
        moves = self.env['stock.move'].search(domain, order='date_expected')
        pickings = []
        for move in moves:
            if not move.picking_id in pickings:
                pickings.append(move.picking_id)
        return pickings
    
    @api.multi
    def days_between_sub_timeframe(self, d1=False, d2=False, repeat_date=False, forecast_sale=False):
        d1_obj = datetime.strptime(str(d1), "%Y-%m-%d")  # change for the datetime issue
        d2_obj = datetime.strptime(str(d2), "%Y-%m-%d")  # change for the datetime issue
        if forecast_sale:
            res = OrderedDict()
            dt = d1_obj
            while dt <= d2_obj:
                period = self.env['requisition.period.ept'].find(dt=dt)
                temp_obj = datetime.strptime(str(period.date_stop), "%Y-%m-%d")
                if temp_obj > d2_obj:
                    temp_obj = d2_obj
                if repeat_date == True :    
                    res.update({period.id : abs((temp_obj - dt).days)})
                else:
                    res.update({period.id : abs((temp_obj - dt).days) + 1})
                dt = temp_obj + timedelta(days=1)
        else:
            res = 0
            if d1 and d2 :
                res = abs((d2_obj - d1_obj + timedelta(days=1)).days)
        return res

    
    
    @api.multi
    def get_data_for_subframes(self, product, warehouse, start_date, end_date, is_use_forecast_sales=False):
        past_sale_start_date = self.requisition_past_sale_start_from or fields.Date.context_today(self)
        self.ensure_one()
        moves = self.get_moves(product, warehouse, start_date, end_date)
        dateframes = {}
        sales_subframes = {}
        incoming_stock_frames = {}
        opening_closing_frames = {}
        date_list = [start_date]
        details_data = {} 
        frame_number = 0
        recent_date = start_date
        if moves:
            op_stock = self.get_net_on_hand_qty(product, warehouse)  
            opening_closing_frames.update({frame_number + 1 : {'opening_stock' : op_stock, 'closing_stock' : 0.0, 'sales' : 0}})
            for move in moves:
                dt = datetime.strptime(str(move.date_expected), "%Y-%m-%d %H:%M:%S")
                date_expected = dt.strftime("%Y-%m-%d")
                if date_expected not in date_list:
                    date_list.append(date_expected)
                    # dt = datetime.strptime(move.date_expected,"%Y-%m-%d %H:%M:%S")
                    # date_expected = dt.strftime("%Y-%m-%d")
                    if not recent_date == date_expected:
                        date_expected = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
                    if is_use_forecast_sales :
                        periods = self.get_periods_of_date(recent_date, date_expected)
                        for period in periods :
                            frame_number = frame_number + 1
                            dateframes.update({frame_number : (periods[period][0], periods[period][1])})
                            stock = incoming_stock_frames.get((frame_number), 0.0)
                            incoming_stock_frames.update({frame_number: stock + 0})
                    else :
                        frame_number = frame_number + 1 
                        dateframes.update({frame_number : (recent_date, date_expected)})
                    recent_date = dt.strftime("%Y-%m-%d")
                if start_date == end_date:
                    stock = incoming_stock_frames.get((frame_number), 0.0)
                    incoming_stock_frames.update({(frame_number): stock + move.product_uom_qty})
                else:
                    stock = incoming_stock_frames.get((frame_number + 1), 0.0)
                    incoming_stock_frames.update({(frame_number + 1): stock + move.product_uom_qty})
        
        else:
            incoming_stock_frames.update({frame_number + 1: 0})
            op_stock = self.get_net_on_hand_qty(product, warehouse)
            opening_closing_frames.update({frame_number + 1 : {'opening_stock' : op_stock, 'closing_stock' : 0.0, 'sales' : 0}})
        
        if is_use_forecast_sales :
            periods = self.get_periods_of_date(recent_date, end_date)
            for period in periods :
                frame_number = frame_number + 1
                dateframes.update({frame_number : (periods[period][0], periods[period][1])})
                stock = incoming_stock_frames.get((frame_number), 0.0)
                incoming_stock_frames.update({frame_number: stock + 0})
        else : 
            frame_number = frame_number + 1
            dateframes.update({frame_number : (recent_date, end_date)})
        days_frame = {}
        date_repeat = False
        date1 = ''
        for k in dateframes:
            v = dateframes[k]
            if date1 == v[0]:
                date_repeat = True
            else:
                date1 = v[0]
        
        for key in dateframes:
            value = dateframes[key]
            # key = Frame  number
            # value = date range
            # this dictionary contains 
            # Key   => sub timeframe number
            # Value => days for each periods the frame exists
            
            if date_repeat == True and key == 1:
                days_frame.update({key : self.days_between_sub_timeframe(d1=value[0], d2=value[1], repeat_date=True, forecast_sale=is_use_forecast_sales)})
            else:
                days_frame.update({key : self.days_between_sub_timeframe(d1=value[0], d2=value[1], repeat_date=False, forecast_sale=is_use_forecast_sales)})
        

        # #now we need to find the forecasted sales of all timeframes / subtimeframes
        if is_use_forecast_sales:     
            for k in days_frame:
                subframe_sales = 0
                ads = 0
                for key, vals in days_frame[k].items():
                    ads = self.get_forecast_sales(product, warehouse, forecast_sale=is_use_forecast_sales, period_id=key)
                    subframe_sales += float((ads) * vals)
                sales_subframes.update({k : subframe_sales})
                stock_frame = opening_closing_frames.get(k, {})
                if stock_frame:
                    stock_frame.update({'sales' : subframe_sales, 'forecast_sales' : subframe_sales, 'ADS':ads})
                else:
                    opening_closing_frames.update({k : {'opening_stock' : 0, 'closing_stock' : 0.0, 'sales' : subframe_sales, 'forecast_sales' : subframe_sales, 'ADS':ads}})
        else:
            avg_daily_sale = self.get_forecast_sales(product, warehouse, past_sale_start_date=past_sale_start_date) 
            for k in days_frame:
                v = days_frame[k]
                subframe_sales = 0
                subframe_sales += (avg_daily_sale * v)
                sales_subframes.update({k : subframe_sales})
                stock_frame = opening_closing_frames.get(k, {})
                if stock_frame:
                    stock_frame.update({'sales' : subframe_sales, 'forecast_sales' : subframe_sales, 'ADS':avg_daily_sale})
                else:
                    opening_closing_frames.update({k : {'opening_stock' : 0, 'closing_stock' : 0.0, 'sales' : subframe_sales, 'forecast_sales' : subframe_sales, 'ADS':avg_daily_sale}})                                            
        # # Set opening closing stock
        for key in sales_subframes:
            stock_frame = opening_closing_frames.get(key, {})
            if stock_frame:
                op_stock = 0
                if key == 1 :
                    op_stock = stock_frame.get('opening_stock', 0)
                else:
                    op_stock = opening_closing_frames.get(key - 1, {}).get('closing_stock', 0.0)
                
                sales = stock_frame.get('sales', 0)
                forecast_sales = stock_frame.get('forecast_sales', 0.0)
                stock_in = incoming_stock_frames.get(key, 0)
                sales = sales - op_stock - stock_in
                if sales < 0:
                    sales = 0
                cl_stock = op_stock + stock_in - forecast_sales if (op_stock + stock_in - forecast_sales) > 0 else 0
                stock_frame.update({'opening_stock' : op_stock, 'closing_stock' : cl_stock, 'sales' : sales, })
                if is_use_forecast_sales :
                    days = sum(days_frame[key].values())
                else : 
                    days = days_frame[key]
                # days = is_use_forecast_sales and sum(days_frame[key].values()) or days_frame[key]
                details_data.update({key:{
                    'start_date':dateframes[key][0],
                    'end_date':dateframes[key][1],
                    'opening':op_stock,
                    'closing':cl_stock,
                    'frame_days':days,
                    'forecasted_sale':forecast_sales,
                    'incoming':stock_in,
                    'sales':sales,
                    'ADS':stock_frame.get('ADS', 0)
                    }})
    
        # # returns the dictionaries  
        # # 1). Incoming stock qty for each sub time frame
        # # 2). sub time frames date range (startdate , enddate)
        # # 3). days frame with all periods with the days within the timeframes
        # # 4). Sales of each sub time frames 
        # # 5). Opening Closing timeframes
        
        # return incoming_stock_frames, dateframes, days_frame, sales_subframes, opening_closing_frames
       
        res = {
                  'incoming_stock_frames' : incoming_stock_frames,
                  'dateframes' : dateframes,
                  'days_frame' : days_frame,
                  'sales_subframes' : sales_subframes,
                  'opening_closing_frames' : opening_closing_frames,
                  'frame_number':frame_number,
                  'detail_data':details_data,
                }
        return res
            
    @api.multi
    def check_forecast_sales_data(self, products, warehouses, start_date, end_date):
        product_ids = products and products.ids or []
        product_ids_str = '(' + str(product_ids or [0]).strip('[]') + ')'
        requisition_period_ids = self.env['requisition.period.ept'].search([('date_start', '<=', end_date), ('date_stop', '>=', start_date)])
        list_period_ids = [period.id for period in requisition_period_ids]
        period_ids_str = '(' + str(list_period_ids or [0]).strip('[]') + ')'
        warehouse_ids_str = '(' + str(warehouses and warehouses.ids or [0]).strip('[]') + ')'     
        not_found_query = """
                Select 
                    product.id as product_id, 
                    warehouse.id as warehouse_id,
                    period.id as period_id
                From 
                    product_product product, stock_warehouse warehouse, requisition_period_ept period
                Where 
                    product.id in {product_ids} And 
                    warehouse.id in {warehouse_ids} And 
                    period.id in {period_ids}
                
                Except
                
                Select 
                    product_id, 
                    warehouse_id, 
                    period_id
                from forecast_sale_ept
                Where 
                    product_id in {product_ids} And 
                    warehouse_id in {warehouse_ids} And 
                    period_id in {period_ids}
                    
            """
        not_found_query = not_found_query.format(product_ids=product_ids_str, warehouse_ids=warehouse_ids_str, period_ids=period_ids_str)
        self._cr.execute(not_found_query)
        res_dict = self._cr.dictfetchall()
        return res_dict
    
    @api.multi
    def get_products_for_requisition(self):
        warehouse_obj = self.env['stock.warehouse']
        product_obj = self.env['product.product']
        detail_line_obj = self.env['product.suggestion.line.detail.ept']
        product_suggestion_line_vals = []
        warehouses = self.warehouse_ids
        products = self.product_ids
        inventory_analysis_days = self.inventory_analysis_of_x_days 
        is_use_forecast_sales = self.is_use_forecast_sale_for_requisition
        lines = self.mapped('product_suggestion_line_ids')
        detail_lines = self.mapped('line_detail_ids')
        lines.sudo().unlink()
        detail_lines.sudo().unlink()
        
        module_available = self.env['ir.module.module'].search([('name', '=', 'advance_purchase_ordering_ept')])
        if module_available:
            procurement_module = self.env.ref('base.module_advance_purchase_ordering_ept')
            if procurement_module and procurement_module.state=='installed':
                process_for_coverage_report_only = False
            else:
                process_for_coverage_report_only = True
        else:
            process_for_coverage_report_only = True
            
        if inventory_analysis_days <= 0:
            raise UserError(_("Please set proper Inventory Analysis of X days!!!")) 
        inventory_analysis_start_date = fields.Date.context_today(self)
        inventory_analysis_end_date = self.get_next_date(inventory_analysis_start_date, days=inventory_analysis_days - 1)
        
        # if not warehouses :
        if not self.select_warehouses :
            warehouses = warehouse_obj.search([]) 
                
        # if not products :
        if not self.select_products :
            products = product_obj.search([('type', '=', 'product'), ('can_be_used_for_coverage_report_ept', '=', True)])
                        
        pending_pickings = []
        for warehouse in warehouses :
            pending_pickings += self.get_pending_moves(warehouse, products and products.ids or [])
        
        if is_use_forecast_sales :
            not_found_fs = self.check_forecast_sales_data(products, warehouses, inventory_analysis_start_date, inventory_analysis_end_date)
            if not_found_fs : 
                raise UserError(_("Forecast Sales not Found!!!"))
            
        if pending_pickings :
            self.write({'has_pending_moves':True})
            
        check_in_detail = False
        for product in products :
            for warehouse in warehouses :
                if not process_for_coverage_report_only:
                    check_in_detail = True
                else:
                    if self.inventory_coverage :
                        check_in_detail = True
                    else :
                        opening_stock = self.get_net_on_hand_qty(product, warehouse)
                        if opening_stock <= 0 :
                            check_in_detail = True
                        else : 
                            if is_use_forecast_sales : 
                                days = self.days_between_sub_timeframe(inventory_analysis_start_date, inventory_analysis_end_date, forecast_sale=is_use_forecast_sales)
                                for period_id in days :
                                    period_ads = self.get_forecast_sales(product, warehouse, is_use_forecast_sales, period_id=period_id)
                                    opening_stock = opening_stock - (period_ads * days[period_id])
                                    if opening_stock <= 0 :
                                        check_in_detail = True
                                        break
                            else : 
                                ads = self.get_forecast_sales(product, warehouse, past_sale_start_date=self.requisition_past_sale_start_from)
                                if ads <= 0 :
                                    continue
                                if (opening_stock / ads) >= self.inventory_analysis_of_x_days :
                                    continue
                                else : 
                                    check_in_detail = True
                if check_in_detail :
                    demand = 0 
                    demand_dict = self.get_data_for_subframes(product, warehouse, inventory_analysis_start_date, inventory_analysis_end_date, is_use_forecast_sales=is_use_forecast_sales)
                    demand_opening_closing_frames = demand_dict.get('opening_closing_frames', {})
                    for key in demand_opening_closing_frames:
                        value = demand_opening_closing_frames[key]
                            
                        demand += value.get('sales', 0.0)
                    if self.inventory_coverage or demand or (not process_for_coverage_report_only):
                        sellers = self.env['product.supplierinfo'].browse([]) 
                        if self.supplier_suggestion_type == 'quick' :
                            sellers = product.seller_ids.sorted('delay')
                        else :
                            sellers = product.seller_ids.sorted('price')
                        
                        detail_data = demand_dict.get('detail_data')
                        detail_line_vals = []
                        sequence = 0
                        for detail in detail_data.values() :
                            stock_status = 'in_stock'
                            ads = detail.get('ADS')
                            opening = detail.get('opening', 0)
                            incoming = detail.get('incoming', 0)
                            days = detail.get('frame_days', 0)
                            start_date = detail.get('start_date')
                            end_date = detail.get('end_date')
                            closing = detail.get('closing', 0)
                            forecast_sale = detail.get('forecasted_sale', 0)
                            stock = opening + incoming
                            if days == 0 :
                                continue
                            sequence += 1
                            val_dict = {
                                            'product_suggestion_id':self.id,
                                            'product_id':product.id,
                                            'warehouse_id':warehouse.id,
                                            'average_daily_sale':ads,
                                            'opening_stock':opening,
                                            'incoming':incoming,
                                            'start_date':start_date,
                                            'end_date':end_date,
                                            'days':days,
                                            'closing_stock':closing,
                                            'stock_status':'in_stock',
                                            'sequence' :sequence,
                                            'forecast_sales':forecast_sale,
                                         }                            
                            
                            if detail.get('sales', 0) > 0 :
                                if stock <= 0:
                                    stock_status = "out_stock"
                                ic_converage_days = ads != 0 and math.floor(stock / ads) or 0 
                                if ic_converage_days == 0 :
                                    val_dict.update({'stock_status':'out_stock'})
                                    detail_line_vals.append((0, 0, val_dict))
                                elif ic_converage_days < days :
                                    out_stock_val_dict = {}
                                    if ic_converage_days < 0 :
                                        stock_status = "out_stock"
                                        val_dict.update({
                                            'stock_status':stock_status,
                                            })
                                    else :
                                        stock_status = "out_stock"
                                        out_stock_val_dict = val_dict.copy()
                                        start_date_obj = datetime.strptime(str(start_date), "%Y-%m-%d")
                                        in_stock_end_date = start_date_obj + timedelta(days=ic_converage_days - 1)
                                        out_stock_start_date = start_date_obj + timedelta(days=ic_converage_days)
                                        in_stock_forecast_sales = ads * ic_converage_days
                                        in_stock_closing = stock - in_stock_forecast_sales
                                        val_dict.update({'days':ic_converage_days,
                                                         'end_date':in_stock_end_date,
                                                         'forecast_sales':in_stock_forecast_sales,
                                                         'closing_stock':in_stock_closing,
                                                                                                             
                                                         })
                                        out_of_stock_days = days - ic_converage_days
                                        sequence += 1
                                        out_stock_val_dict.update({'stock_status':stock_status,
                                                                   'sequence' :sequence,
                                                                   'days':out_of_stock_days,
                                                                   'start_date':out_stock_start_date,
                                                                   'forecast_sales':out_of_stock_days * ads,
                                                                   'opening_stock' :in_stock_closing,
                                                                   'incoming':0,
                                                                   })
                                    detail_line_vals.append((0, 0, val_dict))
                                    if out_stock_val_dict :
                                        detail_line_vals.append((0, 0, out_stock_val_dict))
                                    
                                    
                            else :
                                if not ads and not opening and not incoming:
                                    stock_status = 'na'
                                else :
                                    stock_status = 'in_stock'
                                val_dict.update({'stock_status':stock_status})
                                detail_line_vals.append((0, 0, val_dict))
                                
                                    
                                 
                        product_suggestion_line_vals.append((0, 0, {'product_id':product.id, 'warehouse_id':warehouse.id,
                                                                  'supplier_id':sellers and sellers[0].name.id or False,
                                                                  'line_detail_ids':detail_line_vals,
                                                                  }))
                        
        if product_suggestion_line_vals : 
            if not self.inventory_coverage:
                self.write({
                    'product_suggestion_line_ids':product_suggestion_line_vals,
                    'check_stock_in_other_warehouses' : True
                })
            else:
                self.write({
                    'product_suggestion_line_ids':product_suggestion_line_vals,
                })
            
        # if self.show_products == 'out_of_stock_product' and self.check_stock_in_other_warehouses :
        if self.show_detailed_report and self.check_stock_in_other_warehouses:
            for line in self.product_suggestion_line_ids :
                out_stock_lines = line.mapped('line_detail_ids').filtered(lambda detail : detail.stock_status == 'out_stock')
                for out_stock_line in out_stock_lines :
                    product_id = line.product_id.id
                    warehouse_id = line.warehouse_id.id
                    available_in_warehouses = []
                    partially_available_in_warehouses = []
                    other_warehouse_lines = self.env['requisition.product.suggestion.line.ept'].search([('product_id', '=', product_id), ('warehouse_id', '!=', warehouse_id), ('product_suggestion_id', '=', self.id)])
                    if other_warehouse_lines : 
                        if other_warehouse_lines.mapped('line_detail_ids').filtered(lambda d: d.stock_status == 'in_stock') :
                            for other_warehouse_line in other_warehouse_lines :
                                in_stock_detail_lines = other_warehouse_line.line_detail_ids.filtered(lambda d : d.stock_status == 'in_stock')
                                in_stock_detail_lines_group = []
                                for k, g in groupby(enumerate(in_stock_detail_lines), lambda i :i[0] - i[1].sequence):
                                    group = map(itemgetter(1), g)
                                    group_items = detail_line_obj.browse()
                                    for group_item in list(group) :
                                        group_items += detail_line_obj.browse(group_item.id)
                                    in_stock_detail_lines_group.append(group_items)
                                for group in in_stock_detail_lines_group :
                                    in_stock_start_date = group[0].start_date
                                    in_stock_end_date = group[-1].end_date
                                    if in_stock_start_date <= out_stock_line.start_date <= in_stock_end_date and in_stock_start_date <= out_stock_line.end_date <= in_stock_end_date:                                        
                                        available_in_warehouses.append(group[0].warehouse_id.name)
                                    if in_stock_start_date <= out_stock_line.start_date <= in_stock_end_date or in_stock_start_date <= out_stock_line.end_date <= in_stock_end_date or out_stock_line.start_date <= in_stock_start_date <= out_stock_line.end_date or out_stock_line.start_date <= in_stock_end_date <= out_stock_line.end_date :
                                        partially_available_in_warehouses.append(group[0].warehouse_id.name)
                        else :
                            continue
                    else : 
                        continue    
                    out_stock_line.write({'available_in_warehouses':", ".join(available_in_warehouses),
                                          'partial_available_in_warehouses':", ".join(partially_available_in_warehouses), })
                    if (not process_for_coverage_report_only) and (not line.procurement_source_warehouse_id):
                        demand_warehouse_company_id = line.warehouse_id.company_id.id
                        available_in_warehouse_ids = self.env['stock.warehouse'].search([('name', 'in', available_in_warehouses)])
                        if available_in_warehouse_ids:
                            available_in_same_company_warehouse = available_in_warehouse_ids.filtered(lambda x : x.company_id.id == demand_warehouse_company_id)
                            if available_in_same_company_warehouse:
                                choose_source_warehouse = available_in_same_company_warehouse[0]
                            else:
                                choose_source_warehouse = available_in_warehouse_ids[0]

                            if choose_source_warehouse:
                                line.write({'procurement_source_warehouse_id': choose_source_warehouse.id})

                    else :
                        continue
            
            
        tree_view_id = self.env.ref('inventory_coverage_report_ept.view_tree_product_suggestion_line_ept').id
#         line_ids = self.product_suggestion_line_ids and self.product_suggestion_line_ids.ids or []
        line_ids = self.product_suggestion_line_ids and self.product_suggestion_line_ids.filtered(lambda x : 'out_stock' in x.line_detail_ids.mapped('stock_status')).ids or [] 
        if not self.inventory_coverage : 
            use_out_stock_percent = eval(self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.use_out_stock_percent'))
            if use_out_stock_percent : 
                out_stock_percent = float(self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.out_stock_percent'))
                out_stock_grater_than_ratio = self.product_suggestion_line_ids.filtered(lambda line : sum(line.mapped('line_detail_ids').filtered(lambda detail:detail.stock_status == 'out_stock').mapped('days')) * 100 / inventory_analysis_days >= out_stock_percent)
                line_ids = out_stock_grater_than_ratio and out_stock_grater_than_ratio.ids or []
            
        action = {
            'name': 'Recommanded Products',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'requisition.product.suggestion.line.ept',
            'context': self._context,
            'view_mode':'tree,form',
            'views':[(tree_view_id, 'tree')],
            'domain':"[('id','in',%s)]" % (line_ids)
            }
        return action
    
    @api.multi
    def write_header_in_worksheet(self, worksheet, headers, header_format, row):
        col = 0
        worksheet.set_row(row,40)
        for header in headers :
            if header in ['Product', 'Warehouse'] :
                worksheet.set_column(col, col, 17)
            else :
                worksheet.set_column(col, col, len(header) + 1)
            worksheet.write(row, col, header, header_format)
            col += 1
        worksheet.freeze_panes(row + 1, 0)
        
    
    @api.multi
    def download_xlsx_report_with_text(self, suggestion_lines=None, suggestio_detail_lines=None):
        self.ensure_one()
        inventory_analysis_days = self.inventory_analysis_of_x_days 
        inventory_analysis_start_date = fields.Date.context_today(self)
        inventory_analysis_end_date = self.get_next_date(inventory_analysis_start_date, days=inventory_analysis_days - 1)
        detail_report = self.show_detailed_report 
        show_products = self.show_products
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        common_format_dict = {'font_name':'Arial', 'font_size':12, 'text_wrap': True}
        worksheet_format = workbook.add_format(common_format_dict)

        border_fmt = common_format_dict.copy()
        border_fmt.update({'border' : True})
        border_format = workbook.add_format(border_fmt)
        
        right_align = common_format_dict.copy()
        right_align.update({'align' : 'right', 'bg_color':'e2e7e8'})
        right_align_fmt = workbook.add_format(right_align)
        
        left_align = common_format_dict.copy()
        left_align.update({'align' : 'left', 'bg_color':'e2e7e8'})
        left_align_fmt = workbook.add_format(left_align)
        
        center_align = common_format_dict.copy()
        center_align.update({'align' : 'center', 'bg_color':'e2e7e8'})
        center_align_fmt = workbook.add_format(center_align)

        title_format_dict = common_format_dict.copy()
        title_format_dict.update({'bold':True, 'font_size':14, 'align':'center', 'valign': 'vcenter', 'bg_color' : 'e2e7e8'})
        title_format = workbook.add_format(title_format_dict)
        
        header_format_dict = common_format_dict.copy()
        header_format_dict.update({'bold':True, 'bg_color': '0855da', 'align':'center', 'valign': 'vcenter','font_size':12, 'font_color' : 'ffffff'})
        header_format = workbook.add_format(header_format_dict)
        
        out_stock_format_dict = common_format_dict.copy()
        out_stock_format_dict.update({'bg_color':'fdc8cd', 'border':True})
        out_stock_format = workbook.add_format(out_stock_format_dict)
        
        product_format_dict = common_format_dict.copy()
        product_format_dict.update({'align':'left', 'valign': 'vcenter', 'bg_color' : 'e2e7e8', 'bold':True, 'border':True})
        product_format = workbook.add_format(product_format_dict)
        
        details = self.line_detail_ids
        if suggestion_lines : 
            details = suggestion_lines.mapped('line_detail_ids')
            lines = suggestion_lines
        if suggestio_detail_lines :
            details = suggestio_detail_lines
            lines = suggestio_detail_lines.mapped('product_suggestion_line_id')
            
        if not self.inventory_coverage : 
            use_out_stock_percent = eval(self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.use_out_stock_percent'))
            if use_out_stock_percent : 
                out_stock_percent = float(self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.out_stock_percent'))
                out_stock_grater_than_ratio = lines.filtered(lambda line : sum(line.mapped('line_detail_ids').filtered(lambda detail:detail.stock_status == 'out_stock').mapped('days'))*100/inventory_analysis_days >= out_stock_percent)
                lines = out_stock_grater_than_ratio
                details = out_stock_grater_than_ratio.mapped('line_detail_ids')
        
        lines = self.product_suggestion_line_ids
        warehouses = lines.mapped('warehouse_id').mapped('name')
            
        for warehouse in warehouses:
            
            def find_line_of_this_warehouse_only(x):
                if x.warehouse_id.name == warehouse:
                    return x

            headers = ['From Date', 'To Date', 'Days', 'Opening\nStock', 'Incoming', 'Average\nDaily Sale', 'Forecasted\nSales', 'Closing\nStock']
            if show_products == 'out_of_stock_product' :
                title_string = "Inventory Coverage(Out Of Stock Products) : %s"%warehouse
                # lines = lines.mapped('line_detail_ids').filtered(lambda detail : detail.stock_status == 'out_stock')
                lines = lines.filtered(lambda line : line.mapped('line_detail_ids').filtered(lambda detail:detail.stock_status == 'out_stock'))
            elif show_products == 'in_stock_product' : 
                title_string = "Inventory Coverage(In Stock Products) : %s"%warehouse
                lines = lines.filtered(lambda line : line.mapped('line_detail_ids').filtered(lambda detail:detail.stock_status == 'in_stock'))
                # lines = lines.mapped('line_detail_ids').filtered(lambda detail : detail.stock_status == 'in_stock')
            else :
                title_string = "Inventory Coverage : %s"%warehouse
                headers = ['From Date', 'To Date', 'Days', 'Opening\nStock', 'Incoming', 'Average\nDaily Sale', 'Forecasted\nSales', 'Closing\nStock']
            if self.check_stock_in_other_warehouses :
                headers += ['Available\nin Warehouses']
                headers += ['Partial Available\nin Warehouses']
            if not detail_report :
                headers = ['Incoming', 'Total Coverage\nDays', 'In Stock\nDays', 'Out of Stock\nDays']  
            
            worksheet = workbook.add_worksheet(warehouse)
            worksheet.fit_width
            col = 0
            row = 0
            
            #worksheet.set_row(0, 40)

            if detail_report :
                worksheet.set_default_row(20)
                worksheet.merge_range(0, 0, 0, len(headers)-1, title_string, title_format)
                row += 1
                
                full_length = len(headers)-1
                remaining_length = full_length - 2
                worksheet.merge_range(row, 0, row, 1, "From Date : %s"%str(inventory_analysis_start_date), left_align_fmt)
                worksheet.merge_range(row, 2, row, remaining_length, "Report Date : %s"%datetime.strftime(datetime.today(), '%Y-%m-%d'), center_align_fmt)
                worksheet.merge_range(row, full_length - 1, row, full_length, "To Date : %s"%inventory_analysis_end_date, right_align_fmt)
                    
                row += 1

                self.write_header_in_worksheet(worksheet, headers, header_format, row)
                row += 1
                worksheet.merge_range(row, 0, row, len(headers) - 1, '')
                row += 1
                line_count = 0
                for line in lines.filtered(find_line_of_this_warehouse_only) :
                    if show_products == 'out_of_stock_product' :
                        details = line.line_detail_ids.filtered(lambda d : d.stock_status == 'out_stock')
                    elif show_products == 'in_stock_product':
                        details = line.line_detail_ids.filtered(lambda d : d.stock_status == 'in_stock')
                    else : 
                        details = line.line_detail_ids
                    if not details :
                        continue
                    if all(detail_line.stock_status == 'na' for detail_line in line.line_detail_ids) :
                        continue
                    line_count += 1 

                    product_data = line.product_id.display_name + '   ---   ' + str(line.line_detail_ids[0].opening_stock)
                    worksheet.merge_range(row, 0, row, len(headers)-1, product_data, product_format)
                    row += 1

                    col = 0
                    for detail in details :
                        detail_data = []
                        col = 0
                        detail_data += [str(detail.start_date), str(detail.end_date), detail.days]
#                         if show_products == 'all' :
#                             detail_data += [dict(detail._fields['stock_status'].selection).get(detail.stock_status)]
                        detail_data += [round(detail.opening_stock, 0), detail.incoming, round(detail.average_daily_sale, 2), round(detail.forecast_sales, 2), round(detail.closing_stock, 0)]
                        # if show_products == 'out_of_stock_product' and self.check_stock_in_other_warehouses :
                        if self.check_stock_in_other_warehouses:
                            detail_data += [detail.available_in_warehouses and detail.available_in_warehouses or '']
                            detail_data += [detail.partial_available_in_warehouses and detail.partial_available_in_warehouses or '']
                        worksheet.write_row(row, col, detail_data, detail.stock_status == 'out_stock' and show_products != 'out_of_stock_product' and out_stock_format or border_format)
                        
                        
                        row += 1
                        
                    total_out_stock = sum(line.line_detail_ids.filtered(lambda detail: detail.stock_status == 'out_stock').mapped('days'))
                    total_in_stock = sum(line.line_detail_ids.filtered(lambda detail: detail.stock_status == 'in_stock').mapped('days'))
                    total_coverage_days = inventory_analysis_days
                    
                    summary_data = "In Stock Days : " + str(total_in_stock) + "       " + "Out Of Stock Days : " + str(total_out_stock) + "       " + "Total Coverage Days : " + str(total_coverage_days)
                    worksheet.merge_range(row, 0, row, len(headers) - 1, summary_data, product_format)
                    row += 1
                    worksheet.set_row(row,8)
                    worksheet.merge_range(row, 0, row, len(headers) - 1, '')
                    row += 1
                self.set_column_width(workbook)
            else :
                headers = ['No','Product','Current Stock','incoming','Total Coverage Days','In Stock Days','Out of Stock Days']
                worksheet.merge_range(0, 0, 0, len(headers)-1, title_string, title_format)
                row += 1
                
                full_length = len(headers)-1
                remaining_length = full_length - 2
                worksheet.merge_range(row, 0, row, 1, "From Date : %s"%str(inventory_analysis_start_date), left_align_fmt)
                worksheet.merge_range(row, 2, row, remaining_length, "Report Date : %s"%datetime.strftime(datetime.today(), '%Y-%m-%d'), center_align_fmt)
                worksheet.merge_range(row, full_length - 1, row, full_length, "To Date : %s"%inventory_analysis_end_date, right_align_fmt)
                    
                row += 1

                self.write_header_in_worksheet(worksheet, headers, header_format, row)
                row += 1
                line_count = 0
                for line in lines.filtered(find_line_of_this_warehouse_only) :
                    if all(detail_line.stock_status == 'na' for detail_line in line.line_detail_ids) :
                        continue
                    line_count += 1
                    total_out_stock = sum(line.line_detail_ids.filtered(lambda detail: detail.stock_status == 'out_stock').mapped('days'))
                    total_in_stock = sum(line.line_detail_ids.filtered(lambda detail: detail.stock_status == 'in_stock').mapped('days'))
                    total_incoming = sum(line.line_detail_ids.mapped('incoming'))
                    total_coverage_days = inventory_analysis_days
                    detail_data = [line_count, line.product_id.display_name, 
                                   line.line_detail_ids[0].opening_stock,
                                   total_incoming,
                                   total_coverage_days, total_in_stock, total_out_stock]
                
                    if line.line_detail_ids[0].opening_stock < 0:
                        worksheet.write_row(row, 0, detail_data, out_stock_format)
                    else:
                        worksheet.write_row(row, 0, detail_data, border_format)
                    
                    row += 1
                worksheet.set_column(1, 1, 30)
        
        workbook.close()
        output.seek(0)
        output = base64.encodestring(output.read())
        self.write({'product_inventory_coverage_detail_file':output})
        filename = "Product_Recommendation_report_%s_to_%s.xlsx" % (inventory_analysis_start_date, inventory_analysis_end_date)
        if self.inventory_coverage :
            filename = "Inventory_Coverage_Report_%s_to_%s.xlsx" % (inventory_analysis_start_date, inventory_analysis_end_date)
        active_id = self.ids[0]
        return {
            'type' : 'ir.actions.act_url',
            'url': 'web/content/?model=requisition.product.suggestion.ept&field=product_inventory_coverage_detail_file&download=true&id=%s&filename=%s' % (active_id, filename),
            'target': 'new',
        }        
    
            
            
    @api.multi
    def set_column_width(self, workbook, graphic_report=False):
        if graphic_report:
            for worksheet in workbook.worksheets():
                worksheet.set_column(1, 1, 30)
                worksheet.set_column(2, 2, 10)
        else:
            for worksheet in workbook.worksheets():
                if self.check_stock_in_other_warehouses:
                    worksheet.set_column(0, 7, 10)
                    worksheet.set_column(8, 9, 20)
                else:
                    worksheet.set_column(0, 7, 15)
        return True
    
    
    
    @api.multi            
    def download_report_as_xlsx(self):
        self.ensure_one()
        self.get_products_for_requisition()
        if self.report_data_as == 'text' :
            report_action = self.download_xlsx_report_with_text()
        else :
            report_action = self.download_xlsx_report_with_stock_status_color()
        return report_action
    
    @api.multi
    def download_report_as_pdf(self):
        self.ensure_one()
        self.get_products_for_requisition()
        ctx = self._context.copy()
        report_action = self.env.ref('inventory_coverage_report_ept.action_report_inventory_coverage_report_ept').with_context(ctx).report_action(self)        
        return report_action
 
    @api.multi       
    def download_report(self):
        if self.report_type_as == "pdf":
            res = self.download_report_as_pdf()
        else:
            res = self.download_report_as_xlsx()     
        return res               
            
               
    @api.multi
    def get_month_date_header_detail(self, start_date, end_date):
        d1_obj = datetime.strptime(str(start_date), "%Y-%m-%d")
        d2_obj = datetime.strptime(str(end_date), "%Y-%m-%d")
        res = []
        dt = d1_obj
        month_count = 0
        while dt <= d2_obj:
            res.append({'month_name':datetime.strftime(dt, '%B-%Y'), 'year':dt.year, 'start_date':dt.day})
            if dt.month != d2_obj.month :
                dt = datetime(dt.year, dt.month, 1) + relativedelta(months=1, days=-1)
            if dt.month == d2_obj.month:
                res[month_count].update({'end_date':d2_obj.day})
                break
            res[month_count].update({'end_date':dt.day})
            dt = dt + relativedelta(days=1)
            month_count += 1
        return res
    
    @api.multi
    def download_xlsx_report_with_stock_status_color(self):
        self.get_products_for_requisition()
        self.ensure_one()
        inventory_analysis_start_date = fields.Date.context_today(self)
        inventory_analysis_end_date = self.get_next_date(inventory_analysis_start_date, days=self.inventory_analysis_of_x_days - 1)
        header_dates_detail = self.get_month_date_header_detail(inventory_analysis_start_date, inventory_analysis_end_date)
        detail_report = self.show_detailed_report 
        show_products = self.show_products
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        lines = self.product_suggestion_line_ids
        
        common_format_dict = {'font_name':'Arial', 'font_size':12, 'text_wrap': True, 'border':True}
        worksheet_format = workbook.add_format(common_format_dict)
        
        grey_fmt = common_format_dict.copy()
        grey_fmt.update({'bg_color' : 'e2e7e8'})
        grey_format = workbook.add_format(grey_fmt)
        
        col = 0
        row = 0
        
        title_format_dict = common_format_dict.copy()
        title_format_dict.update({'bold':True, 'font_size':14, 'align':'center', 'valign': 'vcenter', 'bg_color' : '0855da', 'font_color' : 'ffffff'})
        title_format = workbook.add_format(title_format_dict)
                
        header_format_dict = common_format_dict.copy()
        header_format_dict.update({'bold':True, 'bg_color': 'e2e7e8', 'font_size':12, 'align':'center', 'valign': 'vcenter'})
        header_format = workbook.add_format(header_format_dict)
    
        out_stock_format_dict = common_format_dict.copy()
        out_stock_format_dict.update({'bg_color': '7b9edc'})
        out_stock_format = workbook.add_format(out_stock_format_dict)
        
        in_stock_format_dict = common_format_dict.copy()
        in_stock_format_dict.update({'bg_color':'b8cbed'})
        in_stock_format = workbook.add_format(in_stock_format_dict)
        
        na_stock_format_dict = common_format_dict.copy()
        na_stock_format_dict.update({'bg_color': 'dddcdc'})
        na_stock_format = workbook.add_format(na_stock_format_dict)
        
        product_format_dict = common_format_dict.copy()
        product_format_dict.update({'align':'center', 'valign': 'vcenter'})
        product_format = workbook.add_format(product_format_dict)
        
        details = self.line_detail_ids
        
        headers = ['No', 'Product', 'Stock']
        date_header = []
        month_header = []
        for month in header_dates_detail :
            month_header.append(month['month_name'])
            formatter = "{:02d}".format
            date_header += list(map(formatter, range(month['start_date'], month['end_date'] + 1)))
            
        headers += date_header
            
        warehouses = lines.mapped('warehouse_id').mapped('name')
        for warehouse in warehouses:
            row = 0
            def find_line_of_this_warehouse_only(x):
                if x.warehouse_id.name == warehouse:
                    return x
                
            worksheet = workbook.add_worksheet(warehouse)
            worksheet.set_default_row(20)
            if show_products == 'out_of_stock_product' :
                title_string = "Inventory Coverage(Out Of Stock Products) : %s"%warehouse
                lines = lines.filtered(lambda line : line.mapped('line_detail_ids').filtered(lambda detail:detail.stock_status == 'out_stock'))
            elif show_products == 'in_stock_product' : 
                title_string = "Inventory Coverage(In Stock Products) : %s"%warehouse
                lines = lines.filtered(lambda line : line.mapped('line_detail_ids').filtered(lambda detail:detail.stock_status == 'in_stock'))
            else :
                title_string = "Inventory Coverage : %s"%warehouse  
            if not detail_report :
                headers = ['No', 'Product', 'Warehouse', 'Current Stock', 'Incoming', 'Total Coverage Days', 'In Stock Days', 'Out of Stock Days']
                  
            worksheet.set_row(0, 40)
            worksheet.merge_range(0, 0, 0, 2, title_string, title_format)
            row += 1
            
            worksheet.merge_range(row, 0, row, 1, "Report Date ", grey_format)
            worksheet.write(row, 2, datetime.strftime(datetime.today(), '%Y-%m-%d'), grey_format)
            
            col = len(headers) - len(date_header)
            if self.show_products == 'all' :
                colors_for = {' In Stock':in_stock_format, ' Out Of Stock':out_stock_format, ' N/A':na_stock_format }
            if self.show_products == 'in_stock_product' :
                colors_for = {' In Stock':in_stock_format, ' N/A':na_stock_format}
            if self.show_products == 'out_of_stock_product' :
                colors_for = { 'Out Of Stock':out_stock_format, ' N/A':na_stock_format}
        
            for color in colors_for :
                worksheet.write(row, col, '', colors_for[color])
                col += 1
                worksheet.merge_range(row, col, row, col + 3, color)
                col += 4
            
            row += 1
            worksheet.merge_range(row, 0, row, 1, "From Date", grey_format)
            worksheet.write(row, 2, str(inventory_analysis_start_date), grey_format)
            row += 1
            worksheet.merge_range(row, 0, row, 1, "To Date", grey_format)
            worksheet.write(row, 2, inventory_analysis_end_date, grey_format)
            row += 1
            
            if detail_report :
#                 worksheet.merge_range(row, 0, row, 2, warehouse, header_format) 
                col = len(headers) - len(date_header)
                worksheet.merge_range(row, 0, row, col-1, '')
                for month in header_dates_detail :
                    col_end = col + month['end_date'] - month['start_date']
                    if month['start_date'] == month['end_date']:
                        worksheet.write(row, col, month['month_name'], header_format)
                    else : 
                        worksheet.merge_range(row, col, row, col_end, month['month_name'], header_format)
                    col = col_end + 1
                col = 0    
                row += 1
                self.write_header_in_worksheet(worksheet, headers, header_format, row)            
                row += 1
                worksheet.freeze_panes(row, len(headers) - len(date_header))
                line_count = 0
                for line in lines.filtered(find_line_of_this_warehouse_only) :
                    col = 0
                    if show_products == 'out_of_stock_product' :
                        if not line.line_detail_ids.filtered(lambda d : d.stock_status == 'out_stock') :
                            continue
                    elif show_products == 'in_stock_product':
                        if not line.line_detail_ids.filtered(lambda d : d.stock_status == 'in_stock') :
                            continue  
                    details = line.line_detail_ids
                    if not details :
                        continue
                    if all(detail_line.stock_status == 'na' for detail_line in line.line_detail_ids) :
                        continue
                    line_count += 1 
                    detail_data = [line_count, line.product_id.display_name, line.line_detail_ids[0].opening_stock]
                    worksheet.write_row(row, col, detail_data)
                    col = len(detail_data)
                    for detail in details :
                        detail_data = ['' for i in range(1, detail.days + 1)]
                        cell_format = worksheet_format
                        if self.show_products in ['out_of_stock_product', 'all'] and detail.stock_status == 'out_stock':
                            cell_format = out_stock_format
                        if self.show_products in ['in_stock_product', 'all'] and detail.stock_status == 'in_stock':
                            cell_format = in_stock_format 
                        if self.show_products in ['all'] and detail.stock_status == 'na' :
                            cell_format = na_stock_format
                            
                        worksheet.write_row(row, col, detail_data, cell_format) 
                        col += len(detail_data)
                    row += 1
            else :
#                 worksheet.merge_range(row, 1, row, 6, warehouse, header_format)
                row += 1
                # headers = ['No','Product','Warehouse','Current Stock','incoming','Total Coverage Days','In Stock Days','Out of Stock Days']
                self.write_header_in_worksheet(worksheet, headers, header_format, row)
                row += 1
                line_count = 0
                for line in lines.filtered(find_line_of_this_warehouse_only) :
                    col = 0
                    if all(detail_line.stock_status == 'na' for detail_line in line.line_detail_ids) :
                        continue
                    line_count += 1
                    total_out_stock = sum(line.line_detail_ids.filtered(lambda detail: detail.stock_status == 'out_stock').mapped('days'))
                    total_in_stock = sum(line.line_detail_ids.filtered(lambda detail: detail.stock_status == 'in_stock').mapped('days'))
                    total_incoming = sum(line.line_detail_ids.mapped('incoming'))
                    total_coverage_days = self.inventory_analysis_of_x_days
                    detail_data = [line_count, line.product_id.default_code,
                                   line.line_detail_ids[0].opening_stock,
                                   total_incoming,
                                   total_coverage_days, total_in_stock, total_out_stock]
                    worksheet.write_row(row, col, detail_data, worksheet_format)
                    row += 1
        self.set_column_width(workbook, graphic_report=True)
        workbook.close()
        output.seek(0)
        output = base64.encodestring(output.read())
        self.write({'product_inventory_coverage_detail_file':output})
        filename = "Product_Recommendation_report_%s_to_%s.xlsx" % (inventory_analysis_start_date, inventory_analysis_end_date)
        if self.inventory_coverage :
            filename = "Inventory_Coverage_Report_%s_to_%s.xlsx" % (inventory_analysis_start_date, inventory_analysis_end_date)
        active_id = self.ids[0]
        return {
            'type' : 'ir.actions.act_url',
            'url': 'web/content/?model=requisition.product.suggestion.ept&field=product_inventory_coverage_detail_file&download=true&id=%s&filename=%s' % (active_id, filename),
            'target': 'new',
        }

class RequisitionProductSuggestionLine(models.TransientModel):
    _name = 'requisition.product.suggestion.line.ept'
    _description = "Inventory Coverage Report / Product Recommandation lines"
    _order = 'product_id, warehouse_id'
    
    product_suggestion_id = fields.Many2one('requisition.product.suggestion.ept')
    product_id = fields.Many2one('product.product', 'Product')
    supplier_id = fields.Many2one('res.partner', 'Supplier')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    procurement_source_warehouse_id = fields.Many2one('stock.warehouse', 'Procurement Source Warehouse')
    line_detail_ids = fields.One2many('product.suggestion.line.detail.ept', 'product_suggestion_line_id', string='details')
    
class RequisitionProductSuggestionLineDetail(models.TransientModel):
    _name = 'product.suggestion.line.detail.ept'
    _description = "Inventory Coverage Report / Product Recommandation detail lines"
    _order = 'product_id, warehouse_id, sequence'
    
    product_suggestion_id = fields.Many2one('requisition.product.suggestion.ept')
    product_suggestion_line_id = fields.Many2one('requisition.product.suggestion.line.ept')
    product_id = fields.Many2one('product.product', 'Product')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    average_daily_sale = fields.Float('Average Daily Sale')
    opening_stock = fields.Float('Opening Stock')
    incoming = fields.Float('Incoming')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    days = fields.Integer('Days')
    closing_stock = fields.Float('Closing Stock')
    stock_status = fields.Selection([('in_stock', "In Stock"),
                                     ('out_stock', 'Out of Stock'),
                                     ('na', 'N/A')], default='in_stock')
    sequence = fields.Integer('Sequence', default=1)
    forecast_sales = fields.Float('Forecast Sales')
    available_in_warehouses = fields.Char("Available in Warehouses")
    partial_available_in_warehouses = fields.Char("Partial Available in Warehouses")
    
    
    
