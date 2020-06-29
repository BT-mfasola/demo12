from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning
import base64
import csv
from io import StringIO, BytesIO
from csv import DictReader
from csv import DictWriter
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)
import xlrd
    
try:
    import xlwt
except ImportError:
    xlwt = None


class ImportExportProductList(models.TransientModel):
    _name = "import.export.product.list.ept"
    _description = 'Import Export Product Process'
    
    datas = fields.Binary('File')
    report_type = fields.Selection(selection=[('csv', 'CSV'), ('xls', 'Xls')], string='Report Type', required=True)
    choose_file = fields.Binary("Select File")
    file_name = fields.Char(string='file name')

    file_delimiter = fields.Selection([(',', ',')], default="," , string="Delimiter", help="Select a delimiter to process CSV file.")    
    update_existing = fields.Boolean('Do you want to update already exist record ?', default=False)
    replace_product_qty = fields.Boolean('Do you want to replace product quantity?' , help="""
        If you select this option then it will replace product quantity by csv quantity field data, it will not perform addition like 2 quantity is there in line and csv contain 3,
        then it will replace 2 by 3, it won't be updated by 5.If you have not selected this option then it will increase (addition) line quantity with csv quantity field data like 2 quantity in line,
        and csv have 3 quantity then it will update line with 5 quantity""")

    
#===========================================================================
# Import Product List 
#===========================================================================

    @api.multi
    def import_product_list(self):
        inter_companytransfer_obj = self.env['inter.company.transfer.ept']
        inter_companytransfer_line_obj = self.env['inter.company.transfer.line.ept']
        product_obj = self.env['product.product']
        ict_log_obj = self.env['inter.company.transfer.log.ept']
        
        self.validate_process()[0]
        file_name = self.file_name
        index = file_name.rfind('.')
        flag = 0
        if index == -1:
            flag = 1
        extension = file_name[index + 1:]
                
        if flag or extension not in ['csv', 'xls']:
            raise Warning('Incorrect file format found..!' 'Please provide only .csv or .xls file formate to import data!!!')


        inter_companytransfer_id = self._context.get('record', False)
        inter_companytransfer_id = inter_companytransfer_obj.browse(inter_companytransfer_id)
        if inter_companytransfer_id:
            log_record = ict_log_obj.return_log_record(inter_companytransfer_id, operation_type="import")
            if inter_companytransfer_id.state not in ['draft']:
                raise Warning('Current Inter Company Transfer state is not Draft State')
            if self.report_type == 'csv':
                if not self.file_delimiter:
                    raise Warning('Unable to process..!' 'Please select File Delimiter...')

                self.write({'datas':self.choose_file})
                self._cr.commit()
                import_file = BytesIO(base64.decodestring(self.datas))
                csvf = StringIO(import_file.read().decode())
                reader = csv.DictReader(csvf, delimiter=',')
                for line in reader:
                    if not line.get('default_code'):
                        raise Warning('Unable to process..!'  'Please Provide Default Code of Product...') 
                    if not line.get('default_code').strip():
                        raise Warning('Unable to process..!'  'Please Provide Default Code of Product...') 
                    default_code = line.get('default_code').strip() 
                    if default_code != None:
                        product_id = product_obj.search([('default_code', '=', default_code), ('type', '=', 'product')], limit=1)
                        if not product_id:
                            msg = "Product either Product Default code is not match any Product , File Default code is  %s " % (default_code)
                            log_record.post_log_line(msg, type='mismatch')
                            continue
                        qty = line.get('qty').strip()
                        if qty:
                            if qty == '0':
                                qty = 1
                            else:
                                qty = qty
                        else:
                            qty = 1.0
                        inter_companytransfer_line = inter_companytransfer_line_obj.search([('inter_transfer_id', '=', inter_companytransfer_id.id), ('product_id', '=', product_id.id)], limit=1)
                        if inter_companytransfer_line:
                            if self.update_existing:
                                if self.replace_product_qty:
                                    if qty != '0':
                                        inter_companytransfer_line.write({'quantity':float(qty)})
                                    else:
                                        msg = "Inter Company Transfer Line remove due to File Qty is %s and Default Code %s and Product %s" % (qty, default_code, product_id.name)
                                        log_record.post_log_line(msg, type='info')
                                        inter_companytransfer_line.sudo().unlink()
                                else:
                                    if qty != '0':
                                        inter_companytransfer_line.write({'quantity':inter_companytransfer_line.quantity + float(qty)})
                                    else:
                                        msg = "Inter Company Transfer Line remove due to File Qty is %s and Default Code %s and Product %s" % (qty, default_code, product_id.name)
                                        log_record.post_log_line(msg, type='info')
                                        inter_companytransfer_line.sudo().unlink()
                        if not inter_companytransfer_line:
                            vals = {'inter_transfer_id':inter_companytransfer_id.id, 'product_id':product_id.id, 'quantity':qty}
                            if line.get('price'):
                                price = line.get('price')
                                if price != None:
                                    price = line.get('price')
                                    if price != None:
                                        vals.update({'price':price})
                                    else:
                                        price = product_id.lst_price
                                        vals.update({'price':price})
                            inter_companytransfer_line_id = inter_companytransfer_line_obj.create(vals)
                            if not line.get('price'):
                                inter_companytransfer_line_id.default_price_get()
        
            elif self.report_type == 'xls':    
                try:
                    worksheet = self.read_file(self.choose_file)
                    file_header = self.get_xls_header(worksheet)
                except Exception as e:
                    raise Warning("Something is wrong.\n %s" % (str(e)))
                if self.validate_fields(file_header):
                    file_line_data = self.prepare_xls_data(worksheet, file_header)
                    for line_data in file_line_data:
                        default_code = line_data.get('default code', '')
                        if type(default_code) == float:
                            default_code = str(int(default_code))
                        else:
                            default_code = default_code = line_data.get('default code', '') and str(line_data.get('default code', ''))  
                            # comment this below line due to resolve the ticket issue : '03301' i.e 
                            # '''If the spreadsheet has a code that ends in a 0 the tool doesn't deal with that and seems to remove it.'''                
                            # default_code = default_code and default_code.rstrip('0').rstrip('.')
                        if default_code != None:
                            product_id = product_obj.search([('default_code', '=', default_code)], limit=1)
                            if not product_id:
                                msg = "Product either Product Default code is not match any Product , File Default code is  %s " % (default_code)
                                log_record.post_log_line(msg, type='mismatch')
                                continue
                            if type(line_data.get('qty')) in [None, str]:
                                quantity = 1.0
                            else:
                                quantity = line_data.get('qty')
                            if quantity != None:
                                inter_companytransfer_line = inter_companytransfer_line_obj.search([('inter_transfer_id', '=', inter_companytransfer_id.id), ('product_id', '=', product_id.id)], limit=1)
                                if inter_companytransfer_line :
                                    if self.update_existing:
                                        if self.replace_product_qty:
                                            if quantity != 0.0:
                                                inter_companytransfer_line.write({'quantity':quantity})
                                            else:
                                                msg = "Inter Company Transfer Line remove due to File Qty is %s and Default Code %s and Product %s" % (quantity, default_code, product_id.name)
                                                log_record.post_log_line(msg, type='info')
                                                inter_companytransfer_line.sudo().unlink()
                                        else:
                                            if quantity != 0.0:
                                                inter_companytransfer_line.write({'quantity':inter_companytransfer_line.quantity + quantity})
                                            else:
                                                msg = "Inter Company Transfer Line remove due to File Qty is %s and Default Code %s and Product %s" % (quantity, default_code, product_id.name)
                                                log_record.post_log_line(msg, inter_companytransfer_id, type='info')
                                                inter_companytransfer_line.sudo().unlink()
                                        
                                if not inter_companytransfer_line:
                                    if quantity != 0.0:
                                        vals = {'inter_transfer_id':inter_companytransfer_id.id, 'product_id':product_id.id, 'quantity':quantity}
                                        if line_data.get('price'):
                                            price = line_data.get('price')
                                            if price != None:
                                                price = line_data.get('price')
                                                if price != None:
                                                    vals.update({'price':price})
                                                else:
                                                    price = product_id.lst_price
                                                    vals.update({'price':price})
                                        inter_companytransfer_line_id = inter_companytransfer_line_obj.create(vals)
                                        if not line_data.get('price'):
                                            inter_companytransfer_line_id.default_price_get()
                                    else:
                                        msg = "File Qty is %s for this Product %s. So You can not Import Product Due to this Qty %s you can high your Qty" % (quantity, product_id.name, quantity)
                                        log_record.post_log_line(msg,  type='error')
        
        
        if not log_record.ict_log_line_ids:
            log_record.unlink()                     
        return True
    
    
    @api.one            
    def validate_process(self):
        if not self.choose_file:
            raise Warning('Unable to process..!'  'Please select file to process...')
        
        return True
    
    
    def read_file(self, choose_file):
        try:
            xl_workbook = xlrd.open_workbook(file_contents=base64.decodestring(choose_file))
            worksheet = xl_workbook.sheet_by_index(0)
        except Exception as e:
            raise e
        return worksheet
    
    
    @api.multi
    def get_xls_header(self, worksheet):
        column_lst = []
        for col_index in range(worksheet.ncols):
            column_lst.append(worksheet.cell(0, col_index).value.lower()) 
        return column_lst
    
    @api.one
    def validate_fields(self, file_fields):
        require_fields = ['default code', 'qty']
        missing = []
        for field in require_fields:
            if field not in file_fields:
                missing.append(field)
            
        if len(missing) > 0:
            raise Warning('Incorrect format found..! Please provide all the required fields in file, missing fields => %s.' % (missing))
        
        return True
    
    @api.multi
    def prepare_xls_data(self, xl_sheet, keys):
        value_list = []
        for row_index in range(1, xl_sheet.nrows):
            valsdict = {keys[col_index]: xl_sheet.cell(row_index, col_index).value for col_index in range(xl_sheet.ncols)}
            value_list.append(valsdict)
        return value_list 
    
#===============================================================================
# Export Product List 
#===============================================================================
    @api.multi
    def export_product_list(self):

        inter_companytransfer_line_obj = self.env['inter.company.transfer.line.ept']
        line_ids = inter_companytransfer_line_obj.search([('inter_transfer_id', 'in', self.env.context.get('active_ids'))])
        inter_companytransfer_name = line_ids and line_ids[0].inter_transfer_id.name or ''
       
        if self.report_type == 'csv':
            buffer = StringIO()
            buffer.seek(0)
            field_names = ['default_code', 'qty', 'price']
            csvwriter = DictWriter(buffer, field_names, delimiter=',')
            csvwriter.writer.writerow(field_names)
            
            line_no = 0    
            for line in line_ids:
                data = {'default_code':line.product_id.default_code or "",
                     'qty':line.quantity or 0,
                     'price':line.price or 0}
                line_no = line_no + 1     
                csvwriter.writerow(data)
            
            buffer.seek(0)
            file_data = buffer.read().encode()
            file_data = base64.encodestring(file_data)
            self.write({'datas':file_data})
            return {'type' : 'ir.actions.act_url',
                    'url':   'web/content/?model=import.export.product.list.ept&download=true&field=datas&id=%s&filename=Export_Product_List_%s.csv' % (self.id, inter_companytransfer_name),
                    'target': 'new',
                }
        
        
        elif self.report_type == 'xls':
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet("Normal Sales Data", cell_overwrite_ok=True)
            
            worksheet.write(0, 0, 'Default Code')
            worksheet.write(0, 1, 'Qty')
            worksheet.write(0, 2, 'Price')
            
            row = 1 
            for line in line_ids:
                worksheet.write(row, 0, line.product_id.default_code or "")
                worksheet.write(row, 1, line.quantity  or 0)
                worksheet.write(row, 2, line.price or 0)
                row = row + 1 
            
            fp = BytesIO()
            workbook.save(fp)
            fp.seek(0)
            report_data_file = base64.encodestring(fp.read())
            fp.close()
            self.write({'datas':report_data_file})
               
            return {
                'type' : 'ir.actions.act_url',
                'url':   'web/content/?model=import.export.product.list.ept&download=true&field=datas&id=%s&filename=Export_Product_List_%s.xls' % (self.id, inter_companytransfer_name),
                'target': 'new',
                 }   
