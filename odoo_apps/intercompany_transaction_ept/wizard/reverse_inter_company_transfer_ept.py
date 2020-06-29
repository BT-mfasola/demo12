from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import Warning



class ReverseInterCompanyTransfer(models.TransientModel):
    _name = 'reverse.inter.company.transfer.ept'
    _description = 'Reverse Inter Company  Process select lines'

    intercompany_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT")
    reverse_intercompanyline_ids = fields.One2many('reverse.inter.company.transfer.line.ept', 'reverse_intercompany_transfer_id', string="Reverse ICT Lines")
    
    @api.multi
    def action_create_reverse_process(self):
        intercompany_transfer_obj = self.env['inter.company.transfer.ept']
        intercompany_transfer_line_obj = self.env['inter.company.transfer.line.ept']
        reverse_intercompany_transfer_id = self.intercompany_transfer_id.copy(default={'type':'ict_reverse', 'intercompany_transfer_id':self._context.get('active_id')})
        
        product_lines = []
        for line in self.reverse_intercompanyline_ids:
            intercompany_transfer_line = intercompany_transfer_line_obj.create({ 'inter_transfer_id':reverse_intercompany_transfer_id.id, 'product_id':line.product_id.id,
                        'quantity':line.quantity or 1, 'price':line.price})
                        
            product_lines.append(intercompany_transfer_line.id)

        reverse_intercompany_transfer_id.write({'intercompany_transferline_ids':[(6, 0, product_lines)], 'intercompany_transfer_id':self.intercompany_transfer_id.id})
        return True


class ReverseInterCompanyTransferLines(models.TransientModel):

    _name = "reverse.inter.company.transfer.line.ept"
    _description = "Reverse Transfer Lines"
    
    reverse_intercompany_transfer_id = fields.Many2one("reverse.inter.company.transfer.ept", string="Reverse ICT")
    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float("Quantity", default=1.0)
    price = fields.Float('Price')
    qty_delivered = fields.Float(string="Delivered Qty", store=True)
    
    
    @api.one
    @api.constrains('quantity', 'qty_delivered')
    def _check_quantity(self):
        
        if self.quantity > self.qty_delivered:
            raise Warning(_('You can not enter quantity which was greater than original quantity'))

    
  
