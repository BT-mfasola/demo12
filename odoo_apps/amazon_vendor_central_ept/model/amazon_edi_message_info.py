from odoo import models,fields,api,_


class amazon_edi_message_info(models.Model):
        
    _name = "amazon.edi.message.info"
    
    name = fields.Char('Name', readonly=True)
    sender_id = fields.Char('Message Sender ID',size=100,readonly=True)
    recipient_id = fields.Char('Message Recipient ID',size=100,readonly=True)
    message_type = fields.Char('Message Type',size=100,readonly=True)
    msg_version = fields.Char('Message Version',size=100,readonly=True)
    buyer_id = fields.Char('Buyer ID',size=100,readonly=True)
    buyer_address = fields.Char('Buyer Address',readonly=True)
    supplier_id = fields.Char('Supplier ID',size=100,readonly=True)
    delivery_party_id = fields.Char('Delivery Party ID',size=100,readonly=True)
    country_code = fields.Char('Delivery Party Country',size=100,readonly=True)
    invoice_id = fields.Char('Invoice Party ID',size=100,readonly=True)
    currancy_code = fields.Char('Currency Code',size=100,readonly=True)
    order_id = fields.Char('Sale Order ID',size=100,readonly=True) 
    vat_number = fields.Char('VAT Registration Number',size=100,readonly=True)
    latest_date = fields.Date(string = 'Latest Date')
    earliest_date = fields.Date(string='Earliest Date')

    @api.model 
    def create(self,vals):
        try:
            sequence=self.env.ref('amazon_vendor_central_ept.sequence_amazon_edi_message_info')
            if sequence:
                name=sequence.next_by_id()
            else:
                name='/'
        except:
            name='/'
        vals.update({'name':name})
        return super(amazon_edi_message_info,self).create(vals)