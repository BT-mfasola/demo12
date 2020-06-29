from odoo import tools
from odoo import fields, api,models

class ForecastSaleReport(models.Model):
    _name = "forecast.sale.ept.report"
    _description = "Forecast Sale Report"
    _auto = False
    
    sku = fields.Char(string='SKU',readonly =True)
   
    forecast_sales = fields.Float(string="Forecasted Sales",readonly =True)
    date = fields.Date(string='Date',readonly =True)
    
    year_id=fields.Many2one('requisition.fiscal.year.ept',string="Years",)
    product_id = fields.Many2one("product.product",'Product',readonly =True)
    period_id = fields.Many2one("requisition.period.ept",'Period',readonly =True)
    warehouse_id = fields.Many2one("stock.warehouse",'Warehouse',readonly =True)
    
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr,'forecast_sale_ept_report')
        self.env.cr.execute(""" CREATE or REPLACE VIEW forecast_sale_ept_report as 
            (
                select 
                    min(sale.id) as id,
                    sale.product_id as product_id,
                    sale.sku as sku,
                    sale.period_id as period_id, 
                    sale.warehouse_id as warehouse_id,
                    sum (sale.forecast_sales)  as forecast_sales,
                    fp.date_start as date,
                    fp.fiscalyear_id as year_id
                from forecast_sale_ept sale 
                    join requisition_period_ept fp on fp.id = sale.period_id
                group by 
                    product_id,
                    sku,
                    period_id,
                    warehouse_id,date,year_id
            )""")