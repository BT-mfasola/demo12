from odoo import fields, models, api, _

class InterCompanyTransfer(models.Model):
    _inherit = 'inter.company.transfer.ept'
    _description = 'Inter Company Transfer'
    
    
    warehouse_requisition_process_id = fields.Many2one('warehouse.requisition.process.ept', string='Procurement Process')
    warehouse_configuration_line_ids = fields.One2many('warehouse.requisition.configuration.line.ept', 'intercompany_transfer_id', string="Procurement Process Planning")
    
    @api.multi
    def auto_create_saleorder(self):
        res = super(InterCompanyTransfer, self).auto_create_saleorder()
        for so in res:
            if so.intercompany_transfer_id.warehouse_requisition_process_id:    
                so.write({'warehouse_requisition_process_id':so.intercompany_transfer_id.warehouse_requisition_process_id.id})            
        return res
    
    @api.multi
    def auto_create_purchaseorder(self):
        res = super(InterCompanyTransfer, self).auto_create_purchaseorder()
        for po in res:
            if po.intercompany_transfer_id.warehouse_requisition_process_id:    
                po.write({'warehouse_requisition_process_id':po.intercompany_transfer_id.warehouse_requisition_process_id.id})            
        return res
