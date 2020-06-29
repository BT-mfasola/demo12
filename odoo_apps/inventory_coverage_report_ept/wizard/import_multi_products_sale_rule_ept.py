from odoo import models, fields, api

class ImportMultiProductsSaleRule(models.TransientModel):
    _name = "import.multi.products.sale.rule.ept"
    _description = 'Add Multiple Products in Forecast Sale Rule'
 
    product_ids = fields.Many2many("product.product", string='Products')
    sale_ratio = fields.Float(string="Sale Ratio")
    
    @api.multi
    def import_multi_products(self):
        if  self._context.get('active_id'):
            for product in self.product_ids:
                val = {'forecast_sale_rule_id':self._context.get('active_id') ,
                       'product_id': product.id,
                       'sale_ratio': self.sale_ratio ,
                       }
                self.env['forecast.sale.rule.line.ept'].create(val)
