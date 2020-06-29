from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    _description = 'Stock Warehouse'
    
    virtual_warehouse = fields.Boolean('Virtual Warehouse', default=False)
    
    @api.constrains('virtual_warehouse')
    def check_virtual_warehouse_constrains(self):
        warehouse_ids = self.search([('virtual_warehouse', '=', True), ('company_id', '=', self.company_id.id)])
        if len(warehouse_ids) >= 2:
            raise UserError(_("Virtual Warehouse can be only one per company"))
