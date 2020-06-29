 
from odoo import api, fields, models, _
from datetime import timedelta, datetime, time
from odoo import netsvc
from odoo.tools.translate import _

class ImportOrderWorkflow(models.Model):
    _name = "import.order.workflow"
    
    real_inventory_update = fields.Boolean(string="Real Inventory Update")
    name = fields.Char(string="Name")
    reserve_qty=fields.Boolean('Reserve quantity')
    ship_product=fields.Many2one('product.product',string='Ship Product',required=True)
    discount_product=fields.Many2one('product.product',string='Discount Product')
    partner_id = fields.Many2one('res.partner',string='Partner')
    validate_order = fields.Boolean(string="Validate Order")
    create_invoice = fields.Boolean(string="Create Invoice")
    validate_invoice = fields.Boolean(string="Validate Invoice")
    register_payment = fields.Boolean(string="Register Payment")
    import_complete_order = fields.Boolean(string='Import Complete Order As Done In Odoo')
    complete_shipment = fields.Boolean(string="Complete Shipment")
    
    invoice_policy = fields.Selection(
        [('order', 'Ordered quantities'),
         ('delivery', 'Delivered quantities'),
         ('cost', 'Invoice based on time and material')],
        string='Invoicing Policy', default='order')
    picking_policy = fields.Selection([
        ('direct', 'Deliver each product when available'),
        ('one', 'Deliver all products at once')],
        string='Shipping Policy', required=True, readonly=True, default='direct')
    sale_journal = fields.Many2one('account.journal')
    pricelist_id = fields.Many2one('product.pricelist','Pricelist')
    warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse')
    company_id = fields.Many2one('res.company',string="Company")
    # from here the additional field is adding
    ship_expo_magen= fields.Selection(
        [('oncreation', 'Oncreation'),
         ('done', 'Done'),],
        string='Shipment export magento', default='oncreation',
        help="Select the option at which the shipment should "\
        "be exported to magento")
    invoice_expo_magen= fields.Selection(
        [('oncreation', 'Oncreation'),
        ('after_validation', 'After validation'),
         ('done', 'Done')],
        string='Invoice export magento ', default='oncreation')


