from odoo import fields,models,api

class InventoryCoverageReportResSetting(models.TransientModel): 
    _inherit='res.config.settings'
    
    auto_forecast_use_warehouse = fields.Boolean(string="Forecast Sales for Only Mapped Warehouses",default=False)
    use_out_stock_percent = fields.Boolean(string="Out of Stock Ratio",default=False)
    use_forecasted_sales_for_requisition = fields.Boolean(string='Use Forecasted Sales',default=False)
    
    requisition_sales_past_days=fields.Integer(string = 'Use Past Sales Of X Days',default=30)
    is_default_requisition_backup_stock_days = fields.Integer(string='Keep Stock of X Days', default=60)
    out_stock_percent = fields.Float(string="Out of Stock Percent",help='Consider product in recommendation only if out of stock days are more than "Out of stock ratio (%)"')
    
    @api.model
    def get_values(self):
        res = super(InventoryCoverageReportResSetting, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
                    requisition_sales_past_days=int(params.get_param('inventory_coverage_report_ept.requisition_sales_past_days', default=30)),
                    is_default_requisition_backup_stock_days=int(params.get_param('inventory_coverage_report_ept.is_default_requisition_backup_stock_days', default=60)),
                    use_forecasted_sales_for_requisition = eval(params.get_param("inventory_coverage_report_ept.use_forecasted_sales_for_requisition",default='False')),
                    auto_forecast_use_warehouse = eval(params.get_param('inventory_coverage_report_ept.auto_forecast_use_warehouse',default='False')),
                    use_out_stock_percent = eval(params.get_param('inventory_coverage_report_ept.use_out_stock_percent',default='False')),
                    out_stock_percent = float(params.get_param('inventory_coverage_report_ept.out_stock_percent',default=0.0)),  
                   )
        return res
    
    
    def set_values(self):
        super(InventoryCoverageReportResSetting,self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("inventory_coverage_report_ept.requisition_sales_past_days", self.requisition_sales_past_days)
        ICPSudo.set_param("inventory_coverage_report_ept.is_default_requisition_backup_stock_days", self.is_default_requisition_backup_stock_days)
        ICPSudo.set_param("inventory_coverage_report_ept.use_forecasted_sales_for_requisition", repr(self.use_forecasted_sales_for_requisition))
        ICPSudo.set_param("inventory_coverage_report_ept.auto_forecast_use_warehouse", repr(self.auto_forecast_use_warehouse))
        ICPSudo.set_param("inventory_coverage_report_ept.use_out_stock_percent", repr(self.use_out_stock_percent))
        ICPSudo.set_param("inventory_coverage_report_ept.out_stock_percent", self.out_stock_percent)
        
