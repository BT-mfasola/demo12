from odoo import models, fields, api, _
import time
from odoo import netsvc
from odoo.tools .translate import _


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    @api.depends('discount_amt','product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        res = super(SaleOrderLine, self)._compute_amount()
        for line in self:
            subtotal = line.price_subtotal - line.discount_amt
            line.update({'price_subtotal':subtotal})
            return line
        
    discount_amt = fields.Float('Discount Amount')
    
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % \
                            (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'display_type': self.display_type,
            'discount_amt': self.discount_amt
        }

        # res = {
        #     'name': self.name,
        #     'sequence': self.sequence,
        #     'origin': self.order_id.name,
        #     'account_id': account.id,
        #     'price_unit': self.price_unit,
        #     'quantity': qty,
        #     'discount': self.discount,
        #     'uom_id': self.product_uom.id,
        #     'product_id': self.product_id.id or False,
        #     'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
        #     'account_analytic_id': self.order_id.project_id.id,
        #     'discount_amt':self.discount_amt
        # }
        return res  


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    
    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id')
    def _compute_price(self):
        res = super(AccountInvoiceLine, self)._compute_price()
        for line in self:
            subtotal = line.price_subtotal - line.discount_amt
            line.update({'price_subtotal':subtotal})
            return line
    
    discount_amt = fields.Float('Discount Amount')
        