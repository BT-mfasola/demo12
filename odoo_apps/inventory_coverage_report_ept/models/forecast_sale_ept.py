from odoo import models, api, fields
from datetime import datetime, timedelta
import time

class ForecastSale(models.Model):
    _name = "forecast.sale.ept"
    _description = "Forecast Sales"
    _order = "product_id, warehouse_id, period_id desc"
    
    def _comp_previous_forecasted_sales(self):
        requisition_period_obj = self.env['requisition.period.ept']
        for forecast_sale in self:
            current_period_date = forecast_sale.period_id.date_start or time.strftime('%Y-%m-%d')
            formated_date = datetime.strptime(str(current_period_date), "%Y-%m-%d")  # change for datetime issue
            pre_period_end_date = formated_date - timedelta(days=1) 
            pre_date_stop = pre_period_end_date.date()
            previous_period = requisition_period_obj.search([('date_stop', '=', pre_date_stop)])    
            if previous_period:
                pre_forecastsale_obj = self.search([('period_id', '=', previous_period.id), ('product_id', '=', self.product_id.id), ('warehouse_id', '=', self.warehouse_id.id)], limit=1)
                forecast_sale.previous_forecast_sales = pre_forecastsale_obj.forecast_sales
        
    @api.multi
    def _compute_name(self):
        for record in self:
            record.name = '%s\t\t|\t%s\t\t|\t%s' % (record.warehouse_id.name , record.period_id.name , record.product_id.name)
    
    name = fields.Char('name', compute="_compute_name")
    sku = fields.Char(related='product_id.default_code', string='SKU', store=True)
    
    previous_forecast_sales = fields.Float(compute='_comp_previous_forecasted_sales' , readonly=True, string='Previous forecasted Sales')
    forecast_sales = fields.Float(string="Forecasted Sales", default=0)
    
    period_id = fields.Many2one("requisition.period.ept", 'Period')
    product_id = fields.Many2one("product.product", 'Product')
    warehouse_id = fields.Many2one("stock.warehouse", 'Warehouse', copy=False)
    company_id = fields.Many2one("res.company", related="warehouse_id.company_id", string="Company", store=True)

    
    _sql_constraints = [
        ('name_period_product_warehouse_company_unique', 'unique(period_id, product_id,warehouse_id,company_id)', 'Forecast Sale must be unique For Period,Company,Warehouse and Product Wise !'),
    ]  
      
    


    
