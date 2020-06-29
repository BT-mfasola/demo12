from odoo import tools
from odoo import fields, api, models

class ForecastedAndActualSalesReport(models.Model):
    _name = "forecasted.and.actual.sales.report.ept"
    _description = "Forecast And Actual Sales Report"
    _auto = False
    _rec_name = "warehouse_id"
    _order = "id"
    
    
    sku = fields.Char(string='SKU', readonly=True)
    forecast_sales = fields.Float(string="Forecasted Sales", readonly=True, default=0)
    actual_sales = fields.Float(string="Actual Sales", readonly=True)
    diffrence = fields.Float(readonly=True, string="Diffrence")
    
    sale_date = fields.Date(readonly=True, string='Date')
    
    year_id = fields.Many2one('requisition.fiscal.year.ept', readonly=True)
    product_id = fields.Many2one("product.product", 'Product', readonly=True)
    period_id = fields.Many2one("requisition.period.ept", 'Period', readonly=True)
    warehouse_id = fields.Many2one("stock.warehouse", 'Warehouse', readonly=True)
    can_be_used_for_coverage_report_ept = fields.Boolean()
    
   
    
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'forecasted_and_actual_sales_report_ept')
        self.env.cr.execute("""CREATE or REPLACE VIEW forecasted_and_actual_sales_report_ept as 
        (
            SELECT row_number() over(order by product_id, period_id, warehouse_id ) as id,
                    t.product_id,
                    t.sku,
                    t.period_id,
                    t.warehouse_id,
                    sum(t.actual_sales) AS actual_sales,
                    sum(t.forecast_sales) AS forecast_sales,
                    sum(t.forecast_sales) - sum(t.actual_sales)::double precision AS diffrence,
                    t.sale_date,
                    t.year_id,
                    t.can_be_used_for_coverage_report_ept
               FROM 
                   ( 
                     SELECT --min(sale.id) AS id,
                        sale.product_id,
                        sale.sku,
                        sale.period_id,
                        sale.warehouse_id,
                        0 AS actual_sales,
                        sum(sale.forecast_sales) AS forecast_sales,
                        period.date_start As sale_date,
                        period.fiscalyear_id as year_id,
                        tmp.can_be_used_for_coverage_report_ept as can_be_used_for_coverage_report_ept
                    FROM forecast_sale_ept sale
                       JOIN requisition_period_ept period ON sale.period_id = period.id
                       JOIN product_product prod ON prod.id = sale.product_id
                       JOIN product_template tmp ON tmp.id = prod.product_tmpl_id
                    GROUP BY sale.product_id, sale.sku,sale.warehouse_id, sale.period_id,  period.date_start, period.fiscalyear_id, tmp.can_be_used_for_coverage_report_ept
                    
                    UNION ALL
                    
                    SELECT
                        sm.product_id,
                        prd.default_code AS sku,
                        fp.id  AS period_id,
                        wh.id AS warehouse_id,
                        sum(sm.product_qty) AS actual_sales,
                        0 AS forecast_sales,
                        fp.date_start :: date As sale_date,
                        fp.fiscalyear_id as year_id,
                        tmp.can_be_used_for_coverage_report_ept as can_be_used_for_coverage_report_ept
                    FROM stock_move sm
                        JOIN product_product prd ON sm.product_id = prd.id
                        JOIN product_template tmp ON tmp.id = prd.product_tmpl_id
                        JOIN stock_location sl ON sl.id = sm.location_dest_id
                        JOIN requisition_period_ept fp ON sm.date::date >= fp.date_start AND sm.date::date <= fp.date_stop
                        JOIN stock_picking_type pick_type on pick_type.id = sm.picking_type_id
                        JOIN stock_warehouse wh ON wh.id = pick_type.warehouse_id
                    WHERE sm.state::text = 'done'::text AND sl.usage::text = 'customer'::text
                    GROUP BY sm.product_id, prd.default_code, fp.id , wh.id, tmp.can_be_used_for_coverage_report_ept
                    ) t
                  group by product_id,sku,period_id,warehouse_id,sale_date,year_id,can_be_used_for_coverage_report_ept
                )
                """)
        
ForecastedAndActualSalesReport()       
