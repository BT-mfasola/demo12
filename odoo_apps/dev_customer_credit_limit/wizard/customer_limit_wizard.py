# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import api, fields, models


class customer_limit_wizard(models.TransientModel):
    _name = "customer.limit.wizard"
    
    @api.multi
    def set_credit_limit_state(self):
        order_id = self.env['sale.order'].browse(self._context.get('active_id'))
        order_id.state = 'credit_limit'
        order_id.exceeded_amount = self.exceeded_amount
        #order_id.send_mail_approve_credit_limit()
        self.partner_id.credit_limit_on_hold = self.credit_limit_on_hold
        return True
    
    current_sale = fields.Float('Current Quotation')
    exceeded_amount = fields.Float('Exceeded Amount')
    credit = fields.Float('Total Receivable')
    partner_id = fields.Many2one('res.partner',string="Customer")
    credit_limit = fields.Float(related='partner_id.credit_limit',string="Credit Limit")
    sale_orders = fields.Char("Sale Orders")
    invoices = fields.Char("Invoices")
    credit_limit_on_hold = fields.Boolean('Credit Limit on Hold')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: