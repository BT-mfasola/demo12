from odoo import models,fields,api,_
from odoo.osv import expression,osv
from odoo.exceptions import Warning


class avc_file_process_job(models.Model):
    "Amazon Vendor Central file process job"
    _name = 'avc.file.transaction.log'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'
    _description = 'Avc File Transaction Log'
    
    name = fields.Char("Name", readonly=True)
    filename = fields.Char("File Name")
    message=fields.Text("Message")
    vendor_id = fields.Many2one('amazon.vendor.instance', string = 'Vendor')
    company_id=fields.Many2one('res.company',string="Company")
    transaction_log_ids = fields.One2many("avc.transaction.log.line","job_id",string="Log")
    application = fields.Selection([('sale_order','Sale Order')
                                    ,('sale_order_despatch_advice','Sale Order Dispatch Advice')
                                    ,('sale_order_response','Sale Order Response')
                                    ,('invoice','Invoice')
                                    ,('routing_request','Routing Request')
                                    ,('routing_instruction','Routing Instruction')
                                    ,('stock_adjust','Stock Adjustment')
                                    ,('shipment_notice' ,'Advance Shipment Notice')
                                    ,('sales_report','Sales Report')
                                    ,('other','Other')],string="Application")
    operation_type = fields.Selection([('import','Import'),('export','Export')],string="Operation")    
    create_date = fields.Datetime("Create Date")
    sale_order_id = fields.Many2one('sale.order', string = "Sale Order")
    attachment_id = fields.Many2one('ir.attachment',string="Attachment")
    @api.model 
    def create(self,vals):
        try:
            sequence=self.env.ref('amazon_vendor_central_ept.sequence_avc_file_process_job')
            if sequence:
                name=sequence.next_by_id()
            else:
                name='/'
        except:
            name='/'
        vals.update({'name':name})
        return super(avc_file_process_job,self).create(vals)
    
    
class avc_trasaction_log(models.Model):
    _name = 'avc.transaction.log.line'
    _rec_name='filename'
    _order='id desc'
    _description = 'avc transaction log line'
    
    @api.multi
    def get_difference_qty(self):
        for record in self:
            record.difference_qty = record.processed_qty - record.export_qty
            
    message = fields.Text("Message")
    remark=fields.Text("Remark")
    
    job_id = fields.Many2one("avc.file.transaction.log",string="File Process Job", ondelete='cascade')
    picking_id = fields.Many2one("stock.picking",string="Picking")
    back_order_id=fields.Many2one("stock.picking",related="picking_id.backorder_id",readonly=True)
    sale_order_line_id = fields.Many2one("sale.order.line",string="Sales Order")
    sale_order_id = fields.Many2one('sale.order', string = 'Sale Order')
    product_id = fields.Many2one("product.product",string="Product")
    package_id=fields.Many2one("stock.quant.package","Destination Package")
    stock_inventory_id=fields.Many2one('stock.inventory',string="Inventory",readonly=True)
    company_id=fields.Many2one('res.company',string="Company")
    user_id = fields.Many2one("res.users",string="Responsible")
    
    operation_type = fields.Selection([('import','Import'),('export','Export')]
                                      ,string="Operation",readonly=True)
    picking_state=fields.Selection([
                ('draft', 'Draft'),
                ('cancel', 'Cancelled'),
                ('waiting', 'Waiting Another Operation'),
                ('confirmed', 'Waiting Availability'),
                ('partially_available', 'Partially Available'),
                ('assigned', 'Ready to Transfer'),
                ('done', 'Transferred'),
                ],related="picking_id.state",string="Picking State",readonly=True,store=False)
    application = fields.Selection([('sale_order','Sale Order')
                                    ,('sale_order_despatch_advice','Sale Order Dispatch Advice')
                                    ,('sale_order_response','Sale Order Response')
                                    ,('invoice','Invoice')
                                    ,('routing_instruction', 'Routing Instruction')
                                    ,('stock_adjust','Stock Adjustment')
                                    ,('sales_report', 'Sales Report')
                                    ,('other','Other')],string="Application")
    export_qty = fields.Float("Export Qty",default=0.0)
    processed_qty = fields.Float("File Qty",default=0.0)
    difference_qty=fields.Float("Difference Qty",compute=get_difference_qty)
    
    manually_processed=fields.Boolean("Manually Processed",help="If This field is True then it will be hidden from mismatch details", default=False)
    is_mismatch_detail = fields.Boolean("Mismatch", default=False)
    skip_line = fields.Boolean("Skip Line", default=False)
    skip_order = fields.Boolean("Skip Order", default=False) 
    
    product_default_code = fields.Char(string="Product Code",related="product_id.default_code",store=False,readonly=True)
    filename = fields.Char(string="File Name", related = 'job_id.filename',store=False,readonly=True)
    export_time_picking_state=fields.Char("Export Time Picking State")
    export_time_move_state=fields.Char("Export Time Move State")

    create_date = fields.Datetime("Created Date")
    price = fields.Float(string = 'Price')
    