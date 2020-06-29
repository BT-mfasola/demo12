from odoo import fields, models, api
import xlrd
import base64
from odoo.exceptions import Warning, ValidationError
from datetime import datetime
import sys
import psycopg2
from io import BytesIO
import logging
import operator
try:
    import xlwt
except ImportError:
    xlwt = None
PY3 = sys.version_info >= (3, 0)

if PY3:
    basestring = str
    long = int
    xrange = range
    unicode = str

_logger = logging.getLogger(__name__)
    
class ImportExportForecastSale(models.TransientModel):
    _name = 'import.export.forecast.sale.ept'
    _description = 'Import Export Forecast Sale / Normal Sales and Auto Forecasting'
       
    @api.model       
    def default_warehouse_ids(self):

        warehouses = self.env['stock.warehouse'].search([])
        return warehouses 
    
    @api.model
    def default_start_period_id(self):
        current_date = fields.Date.context_today(self)
        current_date_obj = datetime.strptime(str(current_date), "%Y-%m-%d")  # change in datetime issue
        start_period = self.env['requisition.period.ept'].find(dt=current_date_obj)
        return start_period
    
    @api.model
    def default_end_period_id(self):
        current_date = fields.Date.context_today(self)
        current_date_obj = datetime.strptime(str(current_date), "%Y-%m-%d")  # change in datetime issue
        end_period = self.env['requisition.period.ept'].find(dt=current_date_obj)
        return end_period

    choose_file = fields.Binary(string='Choose File', filters='*.xls', help="File extention Must be XLS file", copy=False)
    datas = fields.Binary('File')
    file_name = fields.Char(string='Filename', size=512)
    
    auto_forecast = fields.Boolean(string="Auto Forecasting", default=False, help="If wants to do Sales Forecasting based on Forecast Rules for given periods and Warehouses")
    auto_forecast_as_per = fields.Selection([
            ('actual_sales', 'Actual Sales'),
            ('forecasted_sales', 'Forecasted Sales')
        ], string='Auto Forecast Based On', default='forecasted_sales', required=True) 
    apply_forecast_rule = fields.Boolean(string="Apply Forecast Sales Rules?", default=True)
    
    type = fields.Selection(string='Choose Operations', selection=[('import', 'Import'), ('export', 'Export')], default='import')    
     
    from_period_id = fields.Many2one('requisition.period.ept', 'Source Period', help="When doing Auto Forecasting, use this period as Source Period.")
    start_period_id = fields.Many2one("requisition.period.ept", string="Export From Period", default=default_start_period_id, help="Export Forecast / Normal sales from given period.")
    end_period_id = fields.Many2one("requisition.period.ept", string="To Period", default=default_end_period_id, help="Export Forecast / Normal Sales to given Period.") 
    requisition_log_id = fields.Many2one('requisition.log.ept', string='Log')
      
    for_period_ids = fields.Many2many('requisition.period.ept', string="Target Periods", help="When doing Auto Forecasting, it will do forecasting for given periods.")
    warehouse_ids = fields.Many2many("stock.warehouse", string="Warehouses", default=default_warehouse_ids, help="When Auto Forecasting, it will do forecasting for given Warehouses.")
    
#===============================================================================
# Import Process 
#===============================================================================
        
        
    @api.multi
    def do_import(self):
        if self.file_name and self.file_name[-3:] != 'xls' and self.file_name[-4:] != 'xlsx': 
            raise Warning("Please provide only .xls OR .xlsx Formated file to import forecasted sales!!!")
        to_date = self.get_default_datetime()
        self.requisition_log_id = self.create_log_record(to_date=to_date)
        try:
            forecast_sale_obj = self.env['forecast.sale.ept']
            worksheet = self.read_file(self.file_name, self.choose_file)
            column_header, periods = self.get_header(worksheet)
            
            if self.validate_fields(column_header):
                sale_data = self.fill_dictionary_from_file(worksheet, column_header)
                importable_data = self.validate_data(sale_data, periods)
                
                for data in importable_data:
                    product_id = data.get('product_id', False)
                    warehouse_id = data.get('warehouse_id', False)
                    period_id = data.get('period_id', False)
                    forecast_sales = data.get('forecast_sales', 0.0)
                    
                    try:
                        forecast_sale_id = forecast_sale_obj.search([('product_id', '=', product_id), ('warehouse_id', '=', warehouse_id), ('period_id', '=', period_id)])
                        if forecast_sale_id:
                            forecast_sale_id.write({'forecast_sales' : forecast_sales})
                        else:
                            forecast_sale_obj.create(data)
                    except Exception as e:
                        self.create_requisition_log_line("Data => " + str(data) + " || Error => " + str(e), self.requisition_log_id)
                        pass
        
        except Exception as e:
            self.validate_process()
            self.requisition_log_id.write({'message' : 'Process Failed, please refer log lines for more details.', 'state':'fail'})
            self._cr.commit()
            raise Warning(str(e))

        if not self.requisition_log_id.line_ids:
            self.requisition_log_id.write({'message' : 'Sales forecasted data imported successfully...', 'state':'success'})
            return {'effect': {'fadeout': 'slow', 'message': "Yeah! Forecast Sale Imported successfully.",
                           'img_url': '/web/static/src/img/smile.svg', 'type': 'rainbow_man', }}
        else:
            self.requisition_log_id.write({'message' : 'Process Failed, please refer log lines for more details.', 'state':'fail'})
        return True
                        
    def read_file(self, file_name, choose_file):
        """File read method.
          @param: File name and binary date
          @return: Return file radable data.
        """
        try:
            xl_workbook = xlrd.open_workbook(file_contents=base64.decodestring(choose_file))
            worksheet = xl_workbook.sheet_by_index(0)

        except Exception as e:
            error_value = str(e)
            raise ValidationError(error_value)
        return worksheet
    
    
    def get_header(self, worksheet):
        """File Header.
          @param: Xls file data
          @return: Return file Header data.
        """
        try:
            column_header = {}
            periods = {}
            normal_columns = ['company', 'product_name', 'warehouse', 'sku']
            period_obj = self.env['requisition.period.ept']
            invalid_periods = []
            for col_index in xrange(worksheet.ncols):
                value = worksheet.cell(0, col_index).value.lower()
                column_header.update({col_index: value}) 
                if value not in normal_columns:
                    period_id = period_obj.search([('code', 'ilike', value)])
                    if not period_id or len(period_id) > 1:
                        msg = "Invalid column found => " + str(value)
                        invalid_periods.append(msg)
                    else :
                        periods.update({value : col_index})
            if invalid_periods:
                if self.requisition_log_id.line_ids:
                    self.requisition_log_id.line_ids.sudo().unlink()
                error = ""
                for invalid_column in invalid_periods:
                    self.create_requisition_log_line(invalid_column, self.requisition_log_id, 'Import_forcasted_sales')
                error = "Found Invalid Column Please Check the Log :- " + self.requisition_log_id.name + " "
                raise ValidationError(error)                    
                       
        except Exception as e:
            error_value = str(e)
            raise ValidationError(error_value)

        return column_header, periods
    
    @api.multi
    def validate_fields(self, columnheader):
        '''
            This import pattern requires few fields default, so check it first whether it's there or not.
        '''
        require_fields = ['sku', 'warehouse']
        missing = []
        for field in require_fields:
            if field not in columnheader.values():
                missing.append(field)
            
        if len(missing) > 0:
            raise ValidationError("Please provide all the required fields in file, missing fields => %s." % (missing))
        
        return True
    
    def fill_dictionary_from_file(self, worksheet, column_header):
        """File to dict.
          @param: Worksheet and coloumn header.
          @return:Return file dict data.
        """
        try:
            data = []
            for row_index in range(1, worksheet.nrows):
                sheet_data = {}
                for col_index in xrange(worksheet.ncols):
                    sheet_data.update({column_header.get(col_index): worksheet.cell(row_index, col_index).value})
                data.append(sheet_data)
        except Exception as e:
            error_value = str(e)
            raise ValidationError(error_value)
        return data
    
    @api.multi
    def get_default_datetime(self):
        local_now = datetime.now()
        return local_now.strftime("%Y-%m-%d %H:%M:%S")
    
    @api.multi
    def create_log_record(self, msg="Import Sales Forecasted Data", to_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")):
        log_obj = self.env['requisition.log.ept']
        log_id = log_obj.create({'log_date':to_date, 'message':msg , 'log_type':"Import_forcasted_sales"})
        return log_id
    
    @api.multi
    def create_requisition_log_line(self, msg, log_id, log_type='Import_forcasted_sales'):
        log_line_obj = self.env['requisition.log.line.ept']
        log_line_obj.create({'log_id' : log_id.id, 'message':msg, 'log_type':log_type})
                            
    
    @api.multi
    def validate_data(self, sale_data=[], periods={}):
        product_obj = self.env['product.product']   
        warehouse_obj = self.env['stock.warehouse']
        period_obj = self.env['requisition.period.ept']
        invalid_data = []
        importable_data = []
        flag = False
        row_number = 1
        for data in sale_data:
            row_number += 1
            default_code = data.get('sku', '')
            if not default_code:
                msg = 'Invalid SKU ! " %s " . Row Number : %s.' % (data, row_number)
                invalid_data.append(msg)
                flag = True
                
            if type(default_code) == float:
                default_code = str(int(default_code))
            product_id = product_obj.search([('default_code', '=', default_code)])
            if not product_id:
                msg = 'Product not found Of Related SKU !! %s. Row Number : %s ' % (default_code, row_number)
                invalid_data.append(msg)
                flag = True
            
            if not product_id.can_be_used_for_coverage_report_ept:
                msg = 'Product is not going to be use for Coverage Report !! %s. Row Number : %s ' % (default_code, row_number)
                invalid_data.append(msg)
                flag = True
                
            warehouse = str(data.get('warehouse', ''))
            if not warehouse:
                msg = 'Invalid Warehouse!! => " %s " Row Number : %s ' % (data, row_number)
                invalid_data.append(msg)
                flag = True
                
            warehouse = warehouse.strip()
            warehouse_id = warehouse_obj.search([('name', '=', warehouse)])
            if not warehouse_id:
                msg = 'Warehouse not found!! " %s " Row Number : %s ' % (warehouse, row_number)
                invalid_data.append(msg)
                flag = True
            
            company = str(data.get('company', ''))
            if not company:
                msg = 'Invalid Company!! => " %s " Row Number : %s ' % (data, row_number)
                invalid_data.append(msg)
                flag = True
            
            company = company.strip()
            company_id = self.env['res.company'].search([('name', '=', company)])
            if not company_id:
                msg = 'Company not found!! " %s " Row Number : %s ' % (company, row_number)
                invalid_data.append(msg)
                flag = True
            if product_id and warehouse_id and company_id:
                for key in periods.keys():
                    period_id = period_obj.search([('code', 'ilike', key)])
                    if not data.get(key) :
                        continue
                    if isinstance(data.get(key, 0.0), (float)) :
                        vals = {
                              'product_id' : product_id.id,
                              'warehouse_id' : warehouse_id.id,
                              'period_id' : period_id.id,
                              'forecast_sales' : data.get(key, 0.0),
                              'company_id':company_id.id,
                              }
                        importable_data.append(vals)
                    else:
                        msg = 'Invalid Data " %s " Of Period %s Row Number : %s ' % (data.get(key, 0.0), period_id.code, row_number)
                        invalid_data.append(msg)
                        flag = True
            if flag:
                continue
    
        if len(invalid_data) > 0:
            error = ""
            for err in invalid_data:
                self.create_requisition_log_line(err, self.requisition_log_id, 'Import_forcasted_sales')
                error = error + err + "\n"
            raise ValidationError("Please Correct Data First and then Import File.For More Detail See the Log  %s." % (self.requisition_log_id.name))

        return importable_data
    
    def validate_process(self):
        '''
            Validate process by checking all the conditions and return back with sale order object
        '''   
        if not self.choose_file:
            raise ValidationError('Please select file to process...')
    
   
        
    
    def forecast_sale_create(self, dest_period, product, warehouse_id, qty):
        forecast_sale_obj = self.env['forecast.sale.ept']
        forecast_sale = forecast_sale_obj.search([('period_id', '=', dest_period), ('product_id', '=', product), ('warehouse_id', '=', warehouse_id)])        
        if forecast_sale:
            forecast_sale.write({'forecast_sales':round(qty, 2)})
        else:
            vals = {'period_id':dest_period,
                'product_id':product,
                'warehouse_id':warehouse_id,
                'forecast_sales':round(qty, 2),
                }
            forecast_sale_obj.create(vals)        
            return True 
        
    
    def do_auto_forecast(self):
        if self.auto_forecast_as_per == 'forecasted_sales':
            return self.do_auto_forecast_as_per_forecasted_sales()
        else:
            return self.do_auto_forecast_as_per_actual_sales()
    
    
    def do_auto_forecast_as_per_forecasted_sales(self):
        
        source_period = self.from_period_id.id
        dest_period_ids = self.for_period_ids
        warehouse_ids = self.warehouse_ids
  
        forecast_sale_rule_obj = self.env['forecast.sale.rule.ept']
        forecast_sale_obj = self.env['forecast.sale.ept']
        product_obj = self.env['product.product']
        auto_forecast_use_warehouse = eval(self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.auto_forecast_use_warehouse'))
        
        actual_qty = 0
        forecasted_qty = 0.0
        global_sale_ratio = 1
        
        for warehouse_id in warehouse_ids:
            if not auto_forecast_use_warehouse:
                products = product_obj.search([('type', '=', 'product'), ('can_be_used_for_coverage_report_ept', '=', True)])
            else:
                products = product_obj.search([('warehouse_ids', '=', warehouse_id.id), ('can_be_used_for_coverage_report_ept', '=', True)])
            for dest_period in dest_period_ids:
                for product_obj in products:
                    actual_qty = 1.0
                    forecast_sale = forecast_sale_obj.search([('product_id', '=', product_obj.id), ('warehouse_id', '=', warehouse_id.id), ('period_id', '=', source_period)], limit=1)
                    if not self.apply_forecast_rule:
                        self.forecast_sale_create(dest_period.id, product_obj.id, warehouse_id.id, forecast_sale and forecast_sale.forecast_sales or actual_qty)
                        actual_qty = 0
                    else:
                        if forecast_sale:
                            actual_qty = forecast_sale.forecast_sales                    
                            source_forecast_sales_rule = forecast_sale_rule_obj.search([('period_id', '=', source_period), ('warehouse_id', '=', warehouse_id.id)])
                            if source_forecast_sales_rule:
                                for source_forecast_sale_rule in source_forecast_sales_rule:
                                    global_sale_ratio = source_forecast_sale_rule.global_sale_ratio
                                    source_forecast_sale_rule_lines = source_forecast_sale_rule.forecast_sale_rule_line_ids.search([('forecast_sale_rule_id', '=', source_forecast_sale_rule.id), ('product_id', '=', product_obj.id)], limit=1)
                                    if source_forecast_sale_rule_lines:
                                        actual_qty = forecast_sale.forecast_sales / source_forecast_sale_rule_lines.sale_ratio
                                    else:
                                        actual_qty = forecast_sale.forecast_sales / global_sale_ratio
                           
                        # for dest_period in dest_period_ids:
                        dest_forecast_sale_rules = forecast_sale_rule_obj.search([('period_id', '=', dest_period.id), ('warehouse_id', '=', warehouse_id.id)])                        
                        if  dest_forecast_sale_rules:                     
                            for dest_forecast_sale_rule in dest_forecast_sale_rules:
                                dest_global_ratio = dest_forecast_sale_rule.global_sale_ratio 
                                dest_forecast_sale_rule_lines = dest_forecast_sale_rule.forecast_sale_rule_line_ids.search([('forecast_sale_rule_id', '=', dest_forecast_sale_rule.id), ('product_id', '=', product_obj.id)], limit=1)
                                if dest_forecast_sale_rule_lines:
                                    forecasted_qty = actual_qty * dest_forecast_sale_rule_lines.sale_ratio
                                else:
                                    forecasted_qty = actual_qty * dest_global_ratio    
                    
                            self.forecast_sale_create(dest_period.id, product_obj.id, warehouse_id.id, forecasted_qty)
                            forecasted_qty = 0
                        else:
                            self.forecast_sale_create(dest_period.id, product_obj.id, warehouse_id.id, actual_qty)
                            actual_qty = 0
        return {'effect': {'fadeout': 'slow', 'message': "Auto Sales Forecasting Done For Period %s and %s" % (" ".join(dest_period_ids.mapped('code')), ",".join(warehouse_ids.mapped('name'))),
                           'img_url': '/web/static/src/img/smile.svg', 'type': 'rainbow_man', }}    
   
   

    def do_auto_forecast_as_per_actual_sales(self):
        source_period = self.from_period_id
        dest_period_ids = self.for_period_ids
        warehouse_ids = self.warehouse_ids
        
        auto_forecast_use_warehouse = eval(self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.auto_forecast_use_warehouse'))
        
        actual_qty = 0
        forecasted_qty = 0.0
        global_sale_ratio = 1
        
        for warehouse_id in warehouse_ids:
            if not auto_forecast_use_warehouse:
                products = self.env['product.product'].search([('type', '=', 'product'), ('can_be_used_for_coverage_report_ept', '=', True)])
            else:
                products = self.env['product.product'].search([('warehouse_ids', '=', warehouse_id.id), ('can_be_used_for_coverage_report_ept', '=', True)])
            
            actual_sales_data = self.find_actual_sales(warehouse_id, products.ids, source_period)
            
            for dest_period in dest_period_ids:
                for product_detail in actual_sales_data:
                    product_id = self.env['product.product'].browse(product_detail.get('product_id'))
                    actual_sales = product_detail.get('sale_qty')
                    if actual_sales < 0.0:
                        actual_sales = 0.0
                    if not self.apply_forecast_rule:
                        self.forecast_sale_create(dest_period.id, product_id.id, warehouse_id.id, actual_sales)
                    else:
                        actual_qty = actual_sales
                        forecasted_qty = actual_sales
                        
                        source_forecast_sales_rules = self.env['forecast.sale.rule.ept'].search([('period_id', '=', source_period.id), ('warehouse_id', '=', warehouse_id.id)])
                        if source_forecast_sales_rules:
                            for source_forecast_sale_rule in source_forecast_sales_rules:
                                global_sale_ratio = source_forecast_sale_rule.global_sale_ratio
                                source_forecast_sale_rule_lines = source_forecast_sale_rule.forecast_sale_rule_line_ids.search([('forecast_sale_rule_id', '=', source_forecast_sale_rule.id), ('product_id', '=', product_id.id)], limit=1)
                                if source_forecast_sale_rule_lines:
                                    actual_qty = actual_sales / source_forecast_sale_rule_lines.sale_ratio
                                else:
                                    actual_qty = actual_sales / global_sale_ratio
                       
                        # for dest_period in dest_period_ids:
                        dest_forecast_sale_rules = self.env['forecast.sale.rule.ept'].search([('period_id', '=', dest_period.id), ('warehouse_id', '=', warehouse_id.id)])                        
                        if  dest_forecast_sale_rules:                     
                            for dest_forecast_sale_rule in dest_forecast_sale_rules:
                                dest_global_ratio = dest_forecast_sale_rule.global_sale_ratio 
                                dest_forecast_sale_rule_lines = dest_forecast_sale_rule.forecast_sale_rule_line_ids.search([('forecast_sale_rule_id', '=', dest_forecast_sale_rule.id), ('product_id', '=', product_id.id)], limit=1)
                                if dest_forecast_sale_rule_lines:
                                    forecasted_qty = actual_qty * dest_forecast_sale_rule_lines.sale_ratio
                                else:
                                    forecasted_qty = actual_qty * dest_global_ratio    
                        
                            self.forecast_sale_create(dest_period.id, product_id.id, warehouse_id.id, forecasted_qty)
                            forecasted_qty = 0
                        else:
                            self.forecast_sale_create(dest_period.id, product_id.id, warehouse_id.id, actual_qty)
                            actual_qty = 0
        return {'effect': {'fadeout': 'slow', 'message': "Auto Sales Forecasting Done For Period %s and %s" % (" ".join(dest_period_ids.mapped('code')), ",".join(warehouse_ids.mapped('name'))),
                           'img_url': '/web/static/src/img/smile.svg', 'type': 'rainbow_man', }}       
        
#===============================================================================
# Import Demo Data File
#===============================================================================
   
    def find_actual_sales(self, warehouse_id, product_ids, source_period):
        product_ids = '(' + str(product_ids or [0]).strip('[]') + ')'
        start_date = source_period.date_start
        stop_date = source_period.date_stop 
        
        actual_sales_qry = """
        Select product_id, sum(sale_qty) as sale_qty
            From
            (    
                Select 
                    move.date::date as sale_date,
                    (select code from requisition_period_ept where date_start <= move.date::date and date_stop >= move.date::date) sale_period,
                    move.product_id,
                    type.warehouse_id,
                    move.product_qty as sale_qty
                from     
                    stock_move as move 
                        Inner Join stock_picking pick on pick.id= move.picking_id
                        Inner Join stock_picking_type type on type.id = pick.picking_type_id
                        inner Join product_product prod on prod.id = move.product_id
                        Inner Join product_template tmpl on tmpl.id = prod.product_tmpl_id
                where move.state = 'done' AND tmpl.active=true AND prod.active=true AND
                    type.warehouse_id = %d AND
                    prod.id in %s AND
                    move.date between '%s 00:00:00' and '%s 23:59:59' AND
                    move.location_dest_id in (select id from stock_location where usage = 'customer')
                
                Union All
            
                Select 
                    move.date::date as sale_date,
                    (select code from requisition_period_ept where date_start <= move.date::date and date_stop >= move.date::date) sale_period,
                    move.product_id,
                    type.warehouse_id,
                    move.product_qty * -1 as sale_qty
                from     
                    stock_move as move 
                        Inner Join stock_picking pick on pick.id= move.picking_id
                        Inner Join stock_picking_type type on type.id = pick.picking_type_id
                        inner Join product_product prod on prod.id = move.product_id
                        Inner Join product_template tmpl on tmpl.id = prod.product_tmpl_id
                where move.state = 'done' AND tmpl.active=true AND prod.active=true AND
                    type.warehouse_id = %d AND
                    prod.id in %s AND
                    move.date between '%s 00:00:00' and '%s 23:59:59' AND
                    move.location_id in (select id from stock_location where usage = 'customer') 
                 
                Union All
             
                Select 
                    period.date_start,
                    period.code,
                    prod.id,
                    wh.id,
                    0
                from product_product prod, stock_warehouse wh, requisition_period_ept period, product_template tmpl
                where 
                    tmpl.id = prod.product_tmpl_id and 
                    wh.id = %d AND
                    prod.id in %s AND 
                    period.date_start >= '%s' and period.date_stop <= '%s' AND 
                    tmpl.type='product' and prod.active=true and tmpl.active=true
            ) Sales
            Group by product_id"""%(
                    warehouse_id.id, product_ids, start_date, stop_date,
                    warehouse_id.id, product_ids, start_date, stop_date,
                    warehouse_id.id, product_ids, start_date, stop_date  
                )   
        self._cr.execute(actual_sales_qry)
        actual_sales = self._cr.dictfetchall()
        return actual_sales
    
    
    @api.multi
    def download_forcasted_sales_template(self):
        attachment = self.env['ir.attachment'].search([('name', '=', 'import_forcasted_sales_template.xls')])
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % (attachment.id),
            'target': 'new',
            'nodestroy': False,
            }       
        
        
#===============================================================================
# Export Process
#===============================================================================
   
    @api.multi
    def export_forecast_sales(self):
        if self.start_period_id.date_start >= self.end_period_id.date_stop:
            raise Warning("End Date is Must be Greater then Start Date! ")
        sales_pivot = {}

        try:
                self._cr.execute("CREATE EXTENSION IF NOT EXISTS tablefunc;")
                from_date = self.start_period_id.date_start
                to_date = self.end_period_id.date_stop
                warehouse_ids = []
                for warehouse in self.warehouse_ids:
                    warehouse_ids.append(warehouse.id)
                warehouse_ids = '(' + str(warehouse_ids or [0]).strip('[]') + ')'        
                file_header1 = {'company': 0, 'product_name' : 1, 'warehouse': 2, 'sku':3}
                column_no = 4
                column_list = ""
                select_column_list = ""
                file_header2 = {} 
                file_header = {}
                periods = self.start_period_id.search([('date_start', '>=', from_date), ('date_stop', '<=', to_date)])
                if periods:
                    for period in periods:
                        column_list = column_list + ", %s float" % (period.code)  # #  ,Jan2017 float, Jan2017 float
                        select_column_list = select_column_list + ",coalesce(%s,0) as %s" % (period.code, period.code.lower())  # ,coalesce(Jan2017,0) as jan2017
                        file_header2.update({period.code.lower():column_no})
                        column_no += 1
                
                file_header.update(file_header1) 
                file_header.update(file_header2)
                
                query = """
                
            select    
            product,
            sku,
            product_name,
            company,
            warehouse
            %s    
            from crosstab(
            'Select 
                (w.name || '' - '' || f.sku)::varchar as product,
                f.sku,
                pt.name as product_name,
                co.name as company,
                w.name as warehouse,
                per.code as period,
                sum(forecast_sales) as sale_qty
            from     
                forecast_sale_ept f
                        Inner Join product_product p on p.id = f.product_id
                        Inner Join product_template pt on pt.id = p.product_tmpl_id
                        Inner Join stock_warehouse w on w.id = f.warehouse_id
                        Inner Join res_company co on co.id = w.company_id
                        Inner Join requisition_period_ept per on per.id = f.period_id
            where pt.active=true AND p.active=true AND date_start >= ''%s'' and date_stop <= ''%s'' and f.warehouse_id in %s
            group by f.sku, w.name,co.name,per.code, f.product_id, pt.name
            order by 1,3',
        'Select code from requisition_period_ept where date_start >= ''%s'' and date_stop <= ''%s'' order by date_start'
        )
        as newtable (
            product character varying, sku character varying, product_name character varying,company character varying , warehouse character varying %s
         );
         """ % (select_column_list, from_date, to_date, warehouse_ids, from_date, to_date, column_list)
                self._cr.execute(query)
                sales_pivot = self._cr.dictfetchall() 

        except psycopg2.DatabaseError as e:
            if e.pgcode == '58P01':
                raise Warning("To enable Export Forecast Sale, Please install Postgresql - Contrib in Postgresql")     
        
        if sales_pivot:
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet("Forecast Sale Report", cell_overwrite_ok=True)
            # ## it will return sorted data in list of tuple (sorting based on value)
            sorted_file_header = sorted(file_header.items(), key=operator.itemgetter(1))
            header_bold = xlwt.easyxf("font: bold on, height 250; pattern: pattern solid, fore_colour gray25;alignment: horizontal center")
            column = 0
            for header in sorted_file_header:
                worksheet.write(0, header[1], header[0], header_bold)
                column += 1
            row = 1
            for sale in sales_pivot:
                for header in sorted_file_header:
                    col_no = header[1]
                    value = sale[header[0]]
                    if value:
                        worksheet.write(row, col_no, value)
                row += 1   
            
            fp = BytesIO()
            workbook.save(fp)
            fp.seek(0)
            report_data_file = base64.encodestring(fp.read())
            fp.close()
            self.write({'datas':report_data_file})
           
            return {
            'type' : 'ir.actions.act_url',
            'url':   'web/content/?model=import.export.forecast.sale.ept&field=datas&download=true&id=%s&filename=Forecast_sale_report.xls' % (self.id),
            'target': 'new',
            }
        
    
    @api.multi
    def export_normal_sales(self):
        if self.start_period_id.date_start >= self.end_period_id.date_stop:
            raise Warning("End Date is Must be Greater then Start Date! ")
        from_date = self.start_period_id.date_start
        to_date = self.end_period_id.date_stop
        warehouse_ids = []
        for warehouse in self.warehouse_ids:
            warehouse_ids.append(warehouse.id)
        warehouse_ids = '(' + str(warehouse_ids or [0]).strip('[]') + ')'        
                
        file_header1 = {'company': 0, 'product_name' : 1, 'warehouse': 2, 'sku':3}
        column_no = 4
        column_list = ""
        select_column_list = ""
        file_header2 = {} 
        file_header = {}
        periods = self.start_period_id.search([('date_start', '>=', from_date), ('date_stop', '<=', to_date)])
        if periods:
            for period in periods:
                column_list = column_list + ", %s float" % (period.code)  # #  ,Jan2017 float, Jan2017 float
                select_column_list = select_column_list + ",coalesce(%s,0) as %s" % (period.code, period.code.lower())  # ,coalesce(Jan2017,0) as jan2017
                file_header2.update({period.code.lower():column_no})
                column_no += 1
        sales_pivot = {}
        file_header.update(file_header1) 
        file_header.update(file_header2)
        try:
                query = """
                    select
            product,
            warehouse,
            sku,
            product_name,
            company
            %s    
            from crosstab(
             'Select 
            ware.name || '' - '' || prod.default_code as product,
            ware.name as warehouse,
            prod.default_code as sku,
            tmpl.name as product_name,
            cmp.name as company,
            sale_period,
            sum(sale_qty) as sale_qty    
             from     
             (
            Select sale_date, sale_period, product_id, warehouse_id, sum(sale_qty) as sale_qty
            From
            (    
                Select 
                    move.date::date as sale_date,
                    (select code from requisition_period_ept where date_start <= move.date::date and date_stop >= move.date::date) sale_period,
                    move.product_id,
                    type.warehouse_id,
                    move.product_qty as sale_qty
                from     
                    stock_move as move 
                        Inner Join stock_picking pick on pick.id= move.picking_id
                        Inner Join stock_picking_type type on type.id = pick.picking_type_id
                        inner Join product_product prod on prod.id = move.product_id
                        Inner Join product_template tmpl on tmpl.id = prod.product_tmpl_id
                where move.state = ''done'' AND tmpl.active=true AND prod.active=true AND
                    type.warehouse_id in %s AND
                    move.date between ''%s 00:00:00'' and ''%s 23:59:59'' AND
                    move.location_dest_id in (select id from stock_location where usage = ''customer'')
                
                Union All
            
                Select 
                    move.date::date as sale_date,
                    (select code from requisition_period_ept where date_start <= move.date::date and date_stop >= move.date::date) sale_period,
                    move.product_id,
                    type.warehouse_id,
                    move.product_qty * -1 as sale_qty
                from     
                    stock_move as move 
                        Inner Join stock_picking pick on pick.id= move.picking_id
                        Inner Join stock_picking_type type on type.id = pick.picking_type_id
                        inner Join product_product prod on prod.id = move.product_id
                        Inner Join product_template tmpl on tmpl.id = prod.product_tmpl_id
                where move.state = ''done'' AND tmpl.active=true AND prod.active=true AND
                    type.warehouse_id in %s AND
                    move.date between ''%s 00:00:00'' and ''%s 23:59:59'' AND
                    move.location_id in (select id from stock_location where usage = ''customer'') 
                 
                Union All
             
                Select 
                    period.date_start,
                    period.code,
                    prod.id,
                    wh.id,
                    0
                from product_product prod, stock_warehouse wh, requisition_period_ept period, product_template tmpl
                where 
                    tmpl.id = prod.product_tmpl_id and 
                    wh.id in %s AND 
                    period.date_start >= ''%s'' and period.date_stop <= ''%s'' AND 
                    tmpl.type=''product'' and prod.active=true and tmpl.active=true
            ) Sales
            Group by sale_date, sale_period, product_id, warehouse_id    
             
             )T
            Inner Join product_product prod on prod.id = T.product_id
            Inner Join product_template tmpl on tmpl.id = prod.product_tmpl_id
            Inner Join stock_warehouse ware on ware.id = T.warehouse_id
            Inner Join res_company cmp on cmp.id = ware.company_id
             group by prod.id, ware.name, sale_period, prod.default_code,cmp.name, tmpl.name
             order by 1,3;',
             'Select code from requisition_period_ept where date_start >= ''%s'' and date_stop <= ''%s'' order by date_start'
             )
             as newtable (
            product varchar, warehouse varchar, sku varchar, product_name varchar,
            company varchar %s
            );""" % (select_column_list, warehouse_ids, from_date, to_date, warehouse_ids, from_date, to_date, warehouse_ids, from_date, to_date, from_date, to_date, column_list)
                self._cr.execute(query)
                sales_pivot = self._cr.dictfetchall()
        except psycopg2.DatabaseError as e:
            if e.pgcode == '58P01':
                raise Warning("To enable Export Forecast Sale Rule, Please install Postgresql - Contrib in Postgresql")     
        
        if sales_pivot:
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet("Normal Sales Data", cell_overwrite_ok=True)
            # ## it will return sorted data in list of tuple (sorting based on value)
            sorted_file_header = sorted(file_header.items(), key=operator.itemgetter(1))
            header_bold = xlwt.easyxf("font: bold on, height 250; pattern: pattern solid, fore_colour gray25;alignment: horizontal center")
            column = 0
            for header in sorted_file_header:
                worksheet.write(0, header[1], header[0], header_bold)
                column += 1
            row = 1
            for sale in sales_pivot:
                for header in sorted_file_header:
                    col_no = header[1]
                    value = sale[header[0]]
                    worksheet.write(row, col_no, value)
                row += 1   
            
            fp = BytesIO()
            workbook.save(fp)
            fp.seek(0)
            report_data_file = base64.encodestring(fp.read())
            fp.close()
            self.write({'datas':report_data_file})
           
            return {
            'type' : 'ir.actions.act_url',
            'url':   'web/content/?model=import.export.forecast.sale.ept&field=datas&download=true&id=%s&filename=normal_sale_data.xls' % (self.id),
            'target': 'new',
            }
