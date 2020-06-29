from odoo import models, fields, api, _
from odoo.osv import osv
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)


class sale_order_line(models.Model):
    _inherit = "sale.order.line"

    amazon_edi_line_code = fields.Char('Amazon EDI Line code')
    amazon_edi_line_code_type = fields.Selection([('barcode','Barcode'),('sku','SKU')])
    qty_available = fields.Float(string = "Quantity On Hand",)
    virtual_available = fields.Float(string = "Forecasted Quantity")
    actual_price = fields.Float(string = "Actual Price")
    do_operation = fields.Selection([('accept','Accept'),('cancel','Cancel'),('reject','Reject'),('backorder','Backorder')], string="Operation")
    dispatch_qty = fields.Float(string = "Dispatch Qty")
    backorder_qty = fields.Float(string = "Backorder Qty")

    @api.onchange('dispatch_qty')
    def onchange_dispatch_qty(self):
        for line in self:
            if line.product_uom_qty < line.dispatch_qty:
                line.dispatch_qty = line.product_uom_qty
                line.backorder_qty = 0
                warning_mess = {
                    'title':_('Warning!'),
                    'message':_('Amazon Vendor Central not allow \nto Dispatch more then ordered Qantity')}
                return {'warning':warning_mess}
            line.backorder_qty = line.product_uom_qty - line.dispatch_qty

    @api.onchange('backorder_qty')
    def onchange_backorder_qty(self):
        for line in self:
            if line.product_uom_qty < line.backorder_qty:
                line.backorder_qty = line.product_uom_qty
                line.dispatch_qty = 0
                warning_mess = {
                    'title':_('Warning!'),
                    'message':_('Amazon Vendor Central not allow \nto Backorder more then ordered Qantity')}
                return {'warning':warning_mess}
            line.dispatch_qty = line.product_uom_qty - line.backorder_qty
            if line.backorder_qty > 0:
                line.do_operation = 'backorder'

    @api.onchange('do_operation')
    def onchange_do_operation(self):
        for line in self:
            if line.do_operation == 'accept':
                line.dispatch_qty = line.product_uom_qty
                line.backorder_qty = 0
