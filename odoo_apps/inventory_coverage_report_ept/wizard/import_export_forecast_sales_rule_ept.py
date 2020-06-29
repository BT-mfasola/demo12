import xlrd
from odoo import fields, models, api
import base64
from odoo.exceptions import Warning, ValidationError
from datetime import datetime
import sys
import logging
import operator
import psycopg2

try:
    import xlwt
except ImportError:
    xlwt = None
from io import BytesIO

_logger = logging.getLogger(__name__)

PY3 = sys.version_info >= (3, 0)

if PY3:
    basestring = str
    long = int
    xrange = range
    unicode = str
    
class ImportExportForecastSaleRule(models.TransientModel):
    _name = 'import.export.forecast.sale.rule.ept'
    _description = 'Import Export Forecast Sale Rule'
        
    @api.model    
    def default_warehouse_ids(self):

        warehouses = self.env['stock.warehouse'].search([])
        return warehouses 
    
    
    @api.model
    def default_start_period_id(self):
        current_date = fields.Date.context_today(self)
        current_date_obj = datetime.strptime(str(current_date), "%Y-%m-%d")  # changes into the datetime
        start_period = self.env['requisition.period.ept'].find(dt=current_date_obj)
        return start_period
    
    @api.model
    def default_end_period_id(self):
        current_date = fields.Date.context_today(self)
        current_date_obj = datetime.strptime(str(current_date), "%Y-%m-%d")  # change for the datetime issue
        end_period = self.env['requisition.period.ept'].find(dt=current_date_obj)
        return end_period

    
        
    choose_file = fields.Binary(string='Choose File', filters='*.xlsx', help="File extention Must be XLS, or XLSX", copy=False)
    file_name = fields.Char(string='Filename', size=512)
    requisition_log_id = fields.Many2one('requisition.log.ept', string='Log')    
    
    start_period_id = fields.Many2one("requisition.period.ept", string="Export From Period", default=default_start_period_id, help="Export Forecast Sales Rule From Given Period.")
    end_period_id = fields.Many2one("requisition.period.ept", string="To Period", default=default_end_period_id, help="Export Forecast Sales Rule to Given Period.")
    warehouse_ids = fields.Many2many("stock.warehouse", string="Warehouses", default=default_warehouse_ids, help="Export Forecast Sales Rule for given Warehouses.")
    datas = fields.Binary('File')
    type = fields.Selection(string='Choose Operations', selection=[('import', 'Import'), ('export', 'Export')],
                            default='import')    
   

    @api.multi
    def download_forcasted_sales_rule_template(self):
        attachment = self.env['ir.attachment'].search([('name', '=', 'import_forcasted_sales_rule_template.xls')])
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % (attachment.id),
            'target': 'new',
            'nodestroy': False,
            }     
               
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
            normal_columns = ['product_sku', 'warehouse']
            period_obj = self.env['requisition.period.ept']
            invalid_periods = []
            for col_index in xrange(worksheet.ncols):
                value = worksheet.cell(0, col_index).value.lower()
                column_header.update({col_index: value}) 
                if value not in normal_columns:
                    period_id = period_obj.search([('code', '=ilike', value)])
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
                    self.create_requisition_log_line(invalid_column, self.requisition_log_id, 'Import_forcasted_sales_rule')
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
        require_fields = ['warehouse']
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
        log_id = log_obj.create({'log_date':to_date, 'message':msg , 'log_type':"Import_forcasted_sales_rule"})
        return log_id
    
    @api.multi
    def create_requisition_log_line(self, msg, log_id, log_type='Import_forcasted_sales_rule'):
        log_line_obj = self.env['requisition.log.line.ept']
        log_line_obj.create({'log_id' : log_id.id,
                            'message':msg,
                            'log_type':log_type
                           })
    
    @api.multi
    def validate_data(self, sale_data=[], periods={}):
        product_obj = self.env['product.product']   
        warehouse_obj = self.env['stock.warehouse']
        period_obj = self.env['requisition.period.ept']
        invalid_data = []
        flag = False 
        importable_data = []
        row_number = 1
        for data in sale_data:
            product_id = ''
            row_number += 1
            default_code = data.get('product_sku', '')
            if type(data.get('product_sku')) == type(0.0):
                default_code = str(int(data.get('product_sku')))
            if default_code:
                product_id = product_obj.search([('default_code', '=', default_code)])
                if not product_id:
                    msg = 'Product not found Of Related SKU !! " %s ". Row Number : %s ' % (default_code, row_number)
                    invalid_data.append(msg)
                    flag = True
                if not product_id.can_be_used_for_coverage_report_ept:
                    msg = 'Product is not going to be use for Coverage Report !! %s. Row Number : %s ' % (default_code, row_number)
                    invalid_data.append(msg)
                    flag = True
                    
            warehouse = str(data.get('warehouse', ''))
            if not warehouse:
                msg = 'Invalid Warehouse!! => %s Row Number : %s ' % (data, row_number)
                invalid_data.append(msg)
                flag = True
                
            warehouse = warehouse.strip()
            warehouse_id = warehouse_obj.search([('name', '=', warehouse)])
            if not warehouse_id:
                msg = 'Warehouse not found!! " %s " Row Number : %s ' % (warehouse, row_number)
                invalid_data.append(msg)
                flag = True
            
            for key in periods.keys():
                period_id = period_obj.search([('code', 'ilike', key)])
                if not data.get(key) :
                    continue
                if isinstance(data.get(key, 0.0), (float)) :
                    vals = {
                          'warehouse_id' : warehouse_id.id,
                          'period_id' : period_id.id,
                          'global_sale_ratio':data.get(key, 1.0),
                          'product_id' : product_id and product_id.id or '',
                          'sale_ratio' : data.get(key, 1.0),
                          }
                    importable_data.append(vals)                    
                else :
                    msg = 'Invalid Data " %s " Of Period %s Row Number : %s ' % (data.get(key, 0.0), period_id.code, row_number)
                    invalid_data.append(msg)
                    flag = True
            if flag:
                continue
    
        if len(invalid_data) > 0:
            error = ""
            for err in invalid_data:
                self.create_requisition_log_line(err, self.requisition_log_id, 'Import_forcasted_sales_rule')
                error = error + err + "\n"
            raise ValidationError("Please Correct Data First and then Import File.For More Detail See the Log  %s." % (self.requisition_log_id.name))

        return importable_data
    
    def validate_process(self):
        '''
            Validate process by checking all the conditions and return back with sale order object
        '''   
        if not self.choose_file:
            raise ValidationError('Please select file to process...')
    
    @api.multi
    def do_import(self):

        if self.file_name and self.file_name[-3:] != 'xls' and self.file_name[-4:] != 'xlsx': 
            raise Warning("Please Provide Only .xls OR .xlsx File to Import Forecast Sales!!!")
        to_date = self.get_default_datetime()
        self.requisition_log_id = self.create_log_record(to_date=to_date)
        try:
            forecast_sale_rule_obj = self.env['forecast.sale.rule.ept']
            forecast_sale_rule_line_obj = self.env['forecast.sale.rule.line.ept']
            worksheet = self.read_file(self.file_name, self.choose_file)
            column_header, periods = self.get_header(worksheet)
            
            if self.validate_fields(column_header):
                sale_data = self.fill_dictionary_from_file(worksheet, column_header)
                importable_data = self.validate_data(sale_data, periods)
                
                for data in importable_data:
                    product_id = data.get('product_id', False)
                    warehouse_id = data.get('warehouse_id', False)
                    period_id = data.get('period_id', False)
                    global_sale_ratio = data.get('global_sale_ratio', 1.0)
                    sale_ratio = data.get('sale_ratio', 1.0)
                    
                    rule = forecast_sale_rule_obj.search([('warehouse_id', '=', warehouse_id), ('period_id', '=', period_id)])
                    if not rule:
                        if product_id:
                            rule = forecast_sale_rule_obj.create({
                                    'warehouse_id' : warehouse_id,
                                    'period_id' : period_id,
                                    'global_sale_ratio':1.0
                                    })
                            rule_line = forecast_sale_rule_line_obj.search([('forecast_sale_rule_id', '=', rule.id), ('product_id', '=', product_id)])
                            if rule_line:
                                rule_line.write({
                                    'sale_ratio':sale_ratio
                                    })
                            else:
                                rule_line = forecast_sale_rule_line_obj.create({
                                    'forecast_sale_rule_id':rule.id,
                                    'product_id':product_id,
                                    'sale_ratio':sale_ratio
                                    })
                        else:
                            rule = forecast_sale_rule_obj.create({
                                    'warehouse_id' : warehouse_id,
                                    'period_id' : period_id,
                                    'global_sale_ratio':global_sale_ratio
                                    })            
                    else:
                        if product_id:
                            rule_line = forecast_sale_rule_line_obj.search([('forecast_sale_rule_id', '=', rule.id), ('product_id', '=', product_id)])
                            if rule_line:
                                rule_line.write({
                                    'sale_ratio':sale_ratio
                                    })
                            else:
                                rule_line = forecast_sale_rule_line_obj.create({
                                    'forecast_sale_rule_id':rule.id,
                                    'product_id':product_id,
                                    'sale_ratio':sale_ratio
                                    })
                        else:
                            rule.write({
                               'global_sale_ratio':global_sale_ratio
                              })
        
        except Exception as e:
            self.validate_process()
            self.requisition_log_id.write({'message' : 'Process Failed, please refer log lines for more details.', 'state':'fail'})
            self._cr.commit()
            raise Warning(str(e))

        if not self.requisition_log_id.line_ids:
            self.requisition_log_id.write({'message' : 'Sales forecast Rule data imported successfully...', 'state':'success'})
            return {'effect': {'fadeout': 'slow', 'message': "Yeah! Forecast Sale Rule Imported successfully.",
                           'img_url': '/web/static/src/img/smile.svg', 'type': 'rainbow_man', }}
        else:
            self.requisition_log_id.write({'message' : 'Process Failed, please refer log lines for more details.', 'state':'fail'})
        return True
    ####################### EXPORT ####################################
 
    @api.multi
    def export_forecast_sales_rule(self):
        if self.start_period_id.date_start >= self.end_period_id.date_stop:
            raise Warning("End Date is Must be Greater then Start Date ! ")
        fsr_dict = {}

        try:
            self._cr.execute("CREATE EXTENSION IF NOT EXISTS tablefunc;")
            from_date = self.start_period_id.date_start
            to_date = self.end_period_id.date_stop
            warehouse_ids = []
            for warehouse in self.warehouse_ids:
                warehouse_ids.append(warehouse.id)
            warehouse_ids = '(' + str(warehouse_ids or [0]).strip('[]') + ')'        
            file_header1 = {'warehouse': 0, 'product_sku' : 1}
            column_no = 2
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
            query_line = """select 
                                warehouse,
                                product_sku
                                %s
                            from crosstab(
                                            'Select 
                                                w.name || COALESCE(p.default_code,'''') AS row_name,
                                                w.name as warehouse,
                                                p.default_code as product_sku,
                                                per.code as period,
                                                sale_ratio
                                            from     
                                                 (
                                                    Select *
                                                        From
                                                            (
                                                            select warehouse_id,null as product_id,f.period_id,f.global_sale_ratio as sale_ratio
                                                                from
                                                                    forecast_sale_rule_ept f
                                                                    join requisition_period_ept per on per.id = f.period_id
                                                                    where per.date_start >= ''%s'' and per.date_stop <= ''%s'' and f.warehouse_id in %s
                                                            Union All
                                                            select warehouse_id,product_id,f.period_id,l.sale_ratio
                                                                from 
                                                                    forecast_sale_rule_ept f
                                                                    join forecast_sale_rule_line_ept l on l.forecast_sale_rule_id = f.id
                                                                    join product_product p on p.id = l.product_id
                                                                    Join requisition_period_ept per on per.id = f.period_id
                                                                    where per.date_start >= ''%s'' and per.date_stop <= ''%s'' and f.warehouse_id in %s
                                                            )T
                                                )Sales 
                                                Inner Join stock_warehouse w on w.id = sales.warehouse_id
                                                Inner Join requisition_period_ept per on per.id = sales.period_id
                                                left join product_product p on p.id = sales.product_id
                                                order by 1,2;',
                                            'Select code from requisition_period_ept where date_start >= ''%s'' and date_stop <= ''%s'' order by date_start') 
                            as newtable (row_name text, warehouse varchar,product_sku varchar %s)""" % (select_column_list, from_date, to_date, warehouse_ids, from_date, to_date, warehouse_ids, from_date, to_date, column_list)
            
            self._cr.execute(query_line)
            fsr_dict = self._cr.dictfetchall() 
        except psycopg2.DatabaseError as e:
            if e.pgcode == '58P01':
                raise Warning("To enable Export Forecast Sale Rule, Please install Postgresql - Contrib in Postgresql")     
        
        if fsr_dict:
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet("Forecast Sale Rule Report", cell_overwrite_ok=True)
            # ## it will return sorted data in list of tuple (sorting based on value)
            sorted_file_header = sorted(file_header.items(), key=operator.itemgetter(1))
            header_bold = xlwt.easyxf("font: bold on, height 250; pattern: pattern solid, fore_colour gray25;alignment: horizontal center")
            column = 0
            for header in sorted_file_header:
                worksheet.write(0, header[1], header[0], header_bold)
                column += 1
            row = 1
            for sale in fsr_dict:
                for header in sorted_file_header:
                    col_no = header[1]
                    value = sale.get(header[0], '')
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
            'url':   'web/content/?model=import.export.forecast.sale.rule.ept&field=datas&download=true&id=%s&filename=Forecast_sale_rule_report.xls' % (self.id),
            'target': 'new',
            }    
