# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#    Globalteckz Software Solutions and Services                             #
#    Copyright (C) 2013-Today(www.globalteckz.com).                          #
#                                                                            #
#    This program is free software: you can redistribute it and/or modify    #
#    it under the terms of the GNU Affero General Public License as          #
#    published by the Free Software Foundation, either version 3 of the      #
#    License, or (at your option) any later version.                         #
#                                                                            #
#    This program is distributed in the hope that it will be useful,         #  
#    but WITHOUT ANY WARRANTY; without even the implied warranty of          #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           #
#    GNU Affero General Public License for more details.                     #
#                                                                            #
#                                                                            #
##############################################################################
from odoo import models, fields, api, _
import time
from odoo import netsvc
from odoo.tools .translate import _

class AccountInvoice(models.Model):
    _inherit = "account.invoice"


    payment_method = fields.Many2one('payment.method.magento', string='Payment Method')
    is_magento = fields.Boolean(string='Magento')
    invoice_store_id = fields.Many2one('magento.shop', string='Magento Shop')


    @api.model
    def create(self, vals):
        sale_obj = self.env['sale.order']
        invoice = super(AccountInvoice, self).create(vals)
        sale_id = sale_obj.search([('name','=',invoice.origin),('magento_order','=',True)])
        if sale_id:
            invoice.write({'is_magento':True, 'invoice_store_id':sale_id.store_id.id})
        return invoice


#     @api.multi
#     def invoice_pay_customer_magento(self):
#         if self._context is None:
#             self._context={}
#         wf_service = netsvc.LocalService("workflow")
#         accountinvoice_link = self
#         saleorder_obj = self.env['sale.order']
#         currentTime = time.strftime("%Y-%m-%d")
#         if self.type == 'out_invoice':
#             cr.execute("SELECT invoice_id, order_id FROM sale_order_invoice_rel WHERE invoice_id =%d" % (ids[0],))
#             saleorder_res = dict(cr.fetchall())
#             saleorder_id = saleorder_res[ids[0]]
#             saleorder_link = saleorder_obj.browse(saleorder_id)
#             period_id = self.env['account.period'].search([('date_start','<=',currentTime),('date_stop','>=',currentTime),('company_id','=',saleorder_link.company_id.id)])
#             if not period_id:
#                 raise UserError(_('Period is not defined'))
#             else:
#                 period_id = period_id[0]
#             self._context['type'] = 'out_invoice'
#             journal_id = self._get_journal()
#             journal = self.env['account.journal'].browse(journal_id)
#             acc_id = journal.default_credit_account_id and journal.default_credit_account_id.id or False
#             if not acc_id:
#                 raise UserError(_('Your journal must have a default credit and debit account.'))
#             paid = True
#             currency_id = self._get_currency()
#             self._context['currency_id'] = currency_id
#             voucher_id = saleorder_obj.generate_payment_with_journal_magento(journal_id, saleorder_link.partner_id.id, saleorder_link.amount_total, accountinvoice_link.reference, accountinvoice_link.origin, currentTime, paid)
#             self.pay_and_reconcile(saleorder_link.amount_total, acc_id, period_id, journal_id, False, period_id, False)
# 
#             wf_service.trg_write('account.invoice', self.id)
#             wf_service.trg_write('sale.order', saleorder_id,)
# 
#         elif self.type == 'in_invoice':
#             cr.execute("SELECT invoice_id, purchase_id FROM purchase_invoice_rel WHERE invoice_id =%d" % (ids[0],))
#             purchase_res = dict(cr.fetchall())
#             purchase_id = purchase_res[ids[0]]
# 
#             purchase_obj = self.env['purchase.order']
#             purchase_link = purchase_obj
# 
#             period_id = self.env['account.period'].search([('date_start','<=',currentTime),('date_stop','>=',currentTime),('company_id','=',purchase_link.company_id.id)])
#             if not period_id:
#                 raise wizard.except_wizard(_('Error !'), _('Period is not defined.'))
#             else:
#                 period_id = period_id[0]
# 
#             self._context['type'] = 'in_invoice'
#             journal_id = self._get_journal()
#             journal = self.env['account.journal'].browse(journal_id)
#             acc_id = journal.default_credit_account_id and journal.default_credit_account_id.id
#             if not acc_id:
#                 raise wizard.except_wizard(_('Error !'), _('Your journal must have a default credit and debit account.'))
# 
#             paid = True
#             currency_id = self._get_currency()
#             self._context['currency_id'] = currency_id
#             voucher_id = saleorder_obj.generate_payment_with_journal(journal_id, purchase_link.partner_id.id, purchase_link.amount_total, accountinvoice_link.reference, accountinvoice_link.origin, currentTime, paid)
#             picking_ids = purchase_link.picking_ids
# 
#             if picking_ids:
#                 for picking_id in picking_ids:
#                     stockpicking_obj = self.env['stock.picking']
#                     picking_id.write({'invoice_state':'invoiced'})
#                     if picking_id.state == 'done':
#                         purchase_id.write({'state':'done'})
#                     else:
#                         purchase_id.write({'state':'invoiced'})
#             else:
#                 purchase_id.write({'state':'invoiced'})
# 
#             self.pay_and_reconcile(purchase_link.amount_total, acc_id, period_id, journal_id, False, period_id, False)
#             wf_service.trg_write('account.invoice', self.id)
#             self.confirm_paid()
#             wf_service.trg_write('purchase.order', purchase_id)
#         return True
# 
#     @api.multi
#     def invoice_pay_customer_base(self):
#         self._context={}
#         accountinvoice_link = self
#         currentTime = time.strftime("%Y-%m-%d")
#         journal_id = self._default_journal()
#         if self.type == 'out_invoice':
#             self._context['type'] = 'out_invoice'
#         elif self.type == 'out_refund':
#             self._context['type'] = 'out_refund'
#         self.pay_and_reconcile(journal_id.id,accountinvoice_link.amount_total, False, False)
#         return True





