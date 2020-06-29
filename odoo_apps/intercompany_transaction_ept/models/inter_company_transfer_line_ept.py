from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.addons import decimal_precision as dp



class InterCompanyTransferLine(models.Model):
    
    _name = "inter.company.transfer.line.ept"
    _description = "Internal Company Transfer Line"
    
    
    @api.depends( 'inter_transfer_id.picking_ids.state')
    def _get_delivered_qty(self):
         for line in self:
            if line.inter_transfer_id.state in ['processed']:
                qty_delivered = 0.0
                for picking_id in line.inter_transfer_id.picking_ids:
                    if picking_id.state != 'cancel':
                        for move_line in picking_id.move_ids_without_package:
                            if line.product_id == move_line.product_id:
                                if picking_id.picking_type_id.code == 'incoming':
                                        qty_delivered += move_line.product_id.uom_id._compute_quantity(move_line.quantity_done, move_line.product_id.uom_id)
                            line.qty_delivered = qty_delivered
            else:
                line.qty_delivered = 0.0
    
    
    quantity = fields.Float(string="Quantity", default=1.0)
    qty_delivered = fields.Float(compute='_get_delivered_qty', string='Delivered Quantity', store=True, readonly=True, digits=dp.get_precision('Product Unit of Measure'))
    price = fields.Float(string='Price')
    product_id = fields.Many2one('product.product', string='Product')
    inter_transfer_id = fields.Many2one('inter.company.transfer.ept')


    @api.onchange('product_id', 'inter_transfer_id')
    def default_price_get(self):
        """
        Get the Product Price
        """
        for record in self:
            product_id = record.product_id
            if product_id:
                pricelist_id = record.inter_transfer_id.price_list_id
                if pricelist_id:
                    record.price = pricelist_id.price_get(product_id.id, record.quantity)[pricelist_id.id]
                else:
                    record.price = record.product_id.lst_price
            else:
                record.price = 0.0
                
                
                
