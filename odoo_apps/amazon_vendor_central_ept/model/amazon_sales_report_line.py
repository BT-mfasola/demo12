from odoo import models, fields, api, _
from odoo.osv import osv

class Amazon_Sales_Report_Line(models.Model):
    _name = 'amazon.sales.report.line'

    amazon_sales_report_id = fields.Many2one('amazon.sales.report', string='Amazon Sales Report')
    product_id = fields.Many2one('product.product', string='Product')
    cost_of_goods_sold = fields.Float(string='Cost of Goods sold')
    sold_qty = fields.Float(string='Quantity sold')
    qty_on_hand = fields.Float(string='Quantity on Hand')
    ordered_qty = fields.Float(string='Ordered Quantity')
    seller_location_id = fields.Many2one('amazon.seller.location.code', string='Seller Location')
    report_start_date = fields.Datetime(string='Report Start Date')
    report_end_date = fields.Datetime(string='Report End Date')
