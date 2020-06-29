from odoo import models,api,fields
from odoo.exceptions import Warning, ValidationError,UserError,except_orm
from io import StringIO
import base64
import csv
from datetime import datetime
from odoo.tools.float_utils import float_round, float_compare

class import_product_package_info(models.TransientModel):
    _name = 'import.product.package.info.ept'
    _description = 'import product package info'
    
    choose_file = fields.Binary('Choose File',filters='*.csv')
    file_name = fields.Char("File Name")
    picking_id = fields.Many2one('stock.picking',string="Picking")
    delimiter=fields.Selection([('semicolon','Semicolon')],"Seperator",default="semicolon")
    
    
    @api.model
    def default_get(self,fields):
        context = dict(self._context or {})
        vals =  super(import_product_package_info,self).default_get(fields)
        picking_id = context.get('active_id', [])
        vals['picking_id'] = picking_id
        return vals
    
    @api.one
    def get_file_name(self, name=datetime.strftime(datetime.now(),'%Y%m%d%H%M%S%f')):
        return '/tmp/product_package_%s_%s' %(self.env.uid,name)
    
    @api.one
    def read_file(self,file_name,file):
        imp_file = StringIO(base64.decodestring(file).decode('utf-8'))
        new_file_name = self.get_file_name(name=file_name)[0]
        file_write = open(new_file_name,'w')
        file_write.writelines(imp_file.getvalue())
        file_write.close()
        file_read = open(new_file_name, "rU")
        dialect = csv.Sniffer().sniff(file_read.readline())
        file_read.seek(0)
        if self.delimiter=='semicolon':
            reader = csv.DictReader(file_read,dialect=dialect,delimiter=';',quoting=csv.QUOTE_NONE)
#         elif self.delimiter=='colon':
#             reader = csv.DictReader(file_read,dialect=dialect,delimiter=',',quoting=csv.QUOTE_NONE)
#         else:
#             reader = csv.DictReader(file_read,dialect=dialect,delimiter='\t',quoting=csv.QUOTE_NONE)
        return reader
    
    @api.one
    def validate_fields(self, fieldname):
        '''
            This import pattern requires few fields default, so check it first whether it's there or not.
        '''
        require_fields = ['default_code', 'quantity', 'package_ref','height','width','length','weight','package_type']
        missing = []
        for field in require_fields:
            if field not in fieldname:
                missing.append(field)
        #missing = list(set(require_fields) - set(fieldname))
             
        if len(missing) > 0:
            raise except_orm(('Incorrect format found..!'), ('Please provide all the required fields in file, missing fields => %s.' %(missing)))
        
        return True
    
    def fill_dictionary_from_file(self,reader):
        product_data = []
        for row in reader:
            vals = {
                    'default_code' : row.get('default_code'),
                    'quantity' : row.get('quantity'),
                    'package_ref' : row.get('package_ref'),
                    'height' : row.get('height'),
                    'width' : row.get('width'),
                    'length' : row.get('length'),
                    'weight' : row.get('weight'),
                    'package_type' : row.get('package_type')
                }
            product_data.append(vals)
        
        return product_data
    
    @api.multi
    def import_package_info(self):
        if self.file_name and self.file_name[-3:] != 'csv':
            raise Warning("You can only import CSV file")
        product_packaging_obj = self.env['product.packaging']
        product_product_obj = self.env['product.product']
        stock_move_obj = self.env['stock.move']
        stock_move_line_obj = self.env['stock.move.line']
        stock_quant_package_obj = self.env['stock.quant.package']
        
        reader = self.read_file(self.file_name,self.choose_file)[0]
        fieldname = reader.fieldnames
        picking_id = self.picking_id
        if self.validate_fields(fieldname) :
            product_data = self.fill_dictionary_from_file(reader)
            for data in product_data:
                default_code = data.get('default_code')
                file_qty = data.get('quantity')
                package_ref = data.get('package_ref')
                height = data.get('height')
                width = data.get('width')
                length = data.get('length')
                weight = data.get('weight')
                package_type = data.get('package_type','')
                if package_type.lower() == 'pallet':
                    package_type = 'pallet'
                elif package_type.lower() == 'carton':
                    package_type = 'carton'
                product_package = product_packaging_obj.search([('height','=',float(height)),('width','=',float(width)),('length','=',float(length))])
                if not product_package:
                    product_package = product_packaging_obj.create({
                                                    'name' : 'BOX %s x %s x %s'%(height,width,length),
                                                    'height' : float(height) ,
                                                    'width' : float(width),
                                                    'length' : float(length)
                                                    })
                
                
                package = False
                if not package:
                    package = stock_quant_package_obj.search([('amazon_carrier_code','=',package_ref)])
                    if not package:
                        package = stock_quant_package_obj.create({'amazon_carrier_code' : package_ref})
                    package.write({'packaging_id' : product_package.id,
                                   'amazon_package_weight' : float(weight),
                                   'package_type' : package_type})
                product = product_product_obj.search([('default_code','=',default_code)])
                move_lines = stock_move_obj.search([('picking_id','=',picking_id.id),('product_id','=',product.id),('state','in',('confirmed','assigned','partially_available'))])
                if not move_lines :
                    continue                
                qty_left = float(file_qty)
                for move in move_lines:
                    if qty_left > move.reserved_availability :
                        raise Warning("File Qty Should be equal to Reserved qty")
                    if qty_left <= 0.0 :
                        break
                    move_line_remaning_qty = (move.product_uom_qty)-(sum(move.move_line_ids.mapped('qty_done')))
                    stock_move_lines = move.move_line_ids.filtered(lambda o: o.qty_done <= 0 and not o.result_package_id)
                    
                    for stock_move_line in stock_move_lines:
                        if stock_move_line.product_uom_qty<=qty_left:
                            op_qty=stock_move_line.product_uom_qty
                        else:
                            op_qty=qty_left
                        stock_move_line.write({'qty_done':op_qty})
                        self._put_in_pack_ept(stock_move_line,package)
                        qty_left=float_round(qty_left -op_qty,precision_rounding=stock_move_line.product_uom_id.rounding,rounding_method='UP')
                        move_line_remaning_qty=move_line_remaning_qty-op_qty
                        if qty_left<=0.0:
                            break
                    if qty_left>0.0 and move_line_remaning_qty>0.0:
                        if move_line_remaning_qty<=qty_left:
                            op_qty=move_line_remaning_qty
                        else:
                            op_qty=qty_left
                        stock_move_line_obj.create(
                            {       
                                    'product_id':move.product_id.id,
                                    'product_uom_id':move.product_id.uom_id.id, 
                                    'picking_id':picking_id.id,
                                    'qty_done':float(op_qty) or 0,
                                    'ordered_qty':float(op_qty) or 0,
                                    'result_package_id':package and package.id or False,
                                    'location_id':picking_id.location_id.id, 
                                    'location_dest_id':picking_id.location_dest_id.id,
                                    'move_id':move.id,
                             })
                        qty_left=float_round(qty_left -op_qty,precision_rounding=move.product_id.uom_id.rounding,rounding_method='UP')
                        if qty_left<=0.0:
                            break
                if qty_left>0.0:
                    stock_move_line_obj.create(
                        {       
                                'product_id': move_lines[0].product_id.id,
                                'product_uom_id':move_lines[0].product_id.uom_id.id, 
                                'picking_id':picking_id.id,
                                'ordered_qty':float(qty_left) or 0,
                                'qty_done':float(qty_left) or 0,
                                'result_package_id':package and package.id or False,
                                'location_id':picking_id.location_id.id, 
                                'location_dest_id':picking_id.location_dest_id.id,
                                'move_id':move_lines[0].id,
                         })
                    
        self.picking_id.write({'is_package_info_imported' : True})
        return True
    
    
    
    def _put_in_pack_ept(self,operation,package):
        operation_ids = self.env['stock.move.line']
        if float_compare(operation.qty_done, operation.product_uom_qty, precision_rounding=operation.product_uom_id.rounding) >= 0:
            operation_ids |= operation
        else:
            quantity_left_todo = float_round(
                operation.product_uom_qty - operation.qty_done,
                precision_rounding=operation.product_uom_id.rounding,
                rounding_method='UP')
            new_operation = operation.copy(
                default={'product_uom_qty':0, 'qty_done': operation.qty_done})
            operation.write({'product_uom_qty': quantity_left_todo,'qty_done': 0.0})
            new_operation.write({'product_uom_qty':operation.qty_done})
            operation_ids |= new_operation
        package and operation_ids.write({'result_package_id': package.id})
        return True
        