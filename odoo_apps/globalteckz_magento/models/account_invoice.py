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

import time
from lxml import etree
import odoo.addons.decimal_precision as dp
import odoo.exceptions
from datetime import timedelta, datetime, date
from odoo import netsvc
from odoo import pooler
from odoo import models, fields, api, _
from odoo.tools.translate import _

class account_invoice(models.Model):
    _inherit = "account.invoice"

# 
    def invoice_pay_customer_base(self,saleorder_id):
        self._context={}
        wf_service = netsvc.LocalService("workflow")
        account_obj=self.env['account.account']
        account_type_obj=self.env['account.account.type']
        accountinvoice_link = self
        saleorder_obj = self.env['sale.order']
        invoice_obj=self.env['account.invoice']
        today =datetime.now()
        currentTime = datetime.strftime(today,"%Y-%m-%d")
 
        if accountinvoice_link.type == 'out_invoice' or accountinvoice_link.type == 'out_refund':

            saleorder_link = saleorder_obj.browse(cr,uid,saleorder_id)
            period_id = self.env['account.period'].search([('date_start','<=',currentTime),('date_stop','>=',currentTime),('company_id','=',saleorder_link.company_id.id)])
            if not period_id:
                raise UserError(_('Period is not defined'))
            else:
                period_id = period_id[0]
 
            self._context['type'] = accountinvoice_link.type
            journal_id = self.env['account.invoice.refund']._get_journal()
            type=account_type_obj.search([('name','=','Bank')])
            acc_id=account_obj.search([('user_type','=',type)])
            if not acc_id:
                raise wizard.except_wizard(_('Error !'), _('Your journal must have a default credit and debit account.'))
            paid = True
            currency_id = self._default_currency()
            self._context['currency_id'] = currency_id
            for i in self:
                amount_total=self.browse(i).amount_total
                self.pay_and_reconcile([i],amount_total,acc_id[0], period_id, journal_id, False, period_id, False)
                wf_service.trg_write('account.invoice', i,)
 
        return True



    def make_payment_of_invoice(self):
         if not self._context:
             self._context = {}
         inv_obj = self
         voucher_id = False
         invoice_number = inv_obj.number
         voucher_pool = self.env['account.voucher']
         journal_pool = self.env['account.journal']
         period_obj = self.env['account.period']
         if self._context.get('journal_type',''):
            bank_journal_ids=  journal_pool.search([('type', '=', self._context.get('journal_type'))])
         else:
            bank_journal_ids = journal_pool.search([('type', '=', 'bank')])
         if not len(bank_journal_ids):
             return True
         self._context.update({
                 'default_partner_id': inv_obj.partner_id.id,
                 'default_amount': inv_obj.amount_total,
                 'default_name':inv_obj.name,
                 'close_after_process': True,
                 'invoice_type':inv_obj.type,
                 'invoice_id':inv_obj.id,
                 'journal_id':bank_journal_ids[0],
                 'default_type': inv_obj.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
         })
         if inv_obj.type in ('out_refund','in_refund'):
             self._context.update({'default_amount':-inv_obj.amount_total})
         tax_id = self._get_tax()

         account_data = self.get_accounts(inv_obj.partner_id.id,bank_journal_ids[0])
         date = time.strftime('%Y-%m-%d')
         voucher_data = {
                 'period_id': inv_obj.period_id.id,
                 'account_id': account_data['value']['account_id'],
                 'partner_id': inv_obj.partner_id.id,
                 'journal_id':bank_journal_ids[0],
                 'currency_id': inv_obj.currency_id.id,
                 'reference': inv_obj.name,
                 'amount': inv_obj.amount_total,
                 'type':account_data['value']['type'],
                 'state': 'draft',
                 'pay_now': 'pay_later',
                 'name': '',
                 'date': time.strftime('%Y-%m-%d'),
                 'company_id': self.pool.get('res.company')._company_default_get(cr, uid, 'account.voucher',context=None),
                 'tax_id': tax_id,
                 'payment_option': 'without_writeoff',
                 'comment': _('Write-Off'),
             }
         if inv_obj.type in ('out_refund','in_refund'):
             voucher_data.update({'amount':-inv_obj.amount_total})
         if not voucher_data['period_id']:
             period_ids = period_obj.find(inv_obj.date_invoice,)
             period_id = period_ids and period_ids[0] or False
             voucher_data.update({'period_id':period_id})
         voucher_id = voucher_pool.create(voucher_data)
         if voucher_id:
             if inv_obj.type in ('out_refund','in_refund'):
                 amount=-inv_obj.amount_total
                 res = voucher_pool.onchange_partner_id([voucher_id], inv_obj.partner_id.id, bank_journal_ids[0], amount, inv_obj.currency_id.id, account_data['value']['type'], date, context=context)
             else:
                 res = voucher_pool.onchange_partner_id([voucher_id], inv_obj.partner_id.id, bank_journal_ids[0], inv_obj.amount_total, inv_obj.currency_id.id, account_data['value']['type'], date, context=context)
             for line_data in res['value']['line_cr_ids']:
                 if line_data['name'] in [invoice_number]:
                     voucher_lines = {
                         'move_line_id': line_data['move_line_id'],
                         'amount': inv_obj.amount_total,
                         'name': line_data['name'],
                         'amount_unreconciled': line_data['amount_unreconciled'],
                         'type': line_data['type'],
                         'amount_original': line_data['amount_original'],
                         'account_id': line_data['account_id'],
                         'voucher_id': voucher_id,
                     }
                     
                     voucher_line_id = self.env['account.voucher.line'].create(voucher_lines)
             for line_data in res['value']['line_dr_ids']:
                 if line_data['name'] in [invoice_number]:
                     voucher_lines = {
                         'move_line_id': line_data['move_line_id'],
                         'amount': inv_obj.amount_total,
                         'name': line_data['name'],
                         'amount_unreconciled': line_data['amount_unreconciled'],
                         'type': line_data['type'],
                         'amount_original': line_data['amount_original'],
                         'account_id': line_data['account_id'],
                         'voucher_id': voucher_id,
                     }
                     voucher_line_id = self.env['account.voucher.line'].create(voucher_lines)

             #Add Journal Entries
             voucher_pool.action_move_line_create([voucher_id])

         return voucher_id

    def get_accounts(self,partner_id=False, journal_id=False,):

        """price
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        default = {
            'value':{},
        }
        if not partner_id or not journal_id:
            return default

        partner_pool = self.env['res.partner']
        journal_pool = self.env['account.journal']

        journal = journal_pool.browse(journal_id)
        partner = partner_pool.browse(partner_id)
        account_id = False
        tr_type = False
        if journal.type in ('sale','sale_refund'):
            account_id = partner.property_account_receivable.id
            tr_type = 'sale'
        elif journal.type in ('purchase', 'purchase_refund','expense'):
            account_id = partner.property_account_payable.id
            tr_type = 'purchase'
        else:
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id
            tr_type = 'receipt'

        default['value']['account_id'] = account_id
        default['value']['type'] = tr_type

        return default
    
    def _get_tax(self):
        if self._context is None: self._context = {}
        journal_pool = self.env['account.journal']
        journal_id = self._context.get('journal_id', False)
        if not journal_id:
            ttype = self._context.get('type', 'bank')
            res = journal_pool.search([('type', '=', ttype)], limit=1)
            if not res:
                return False
            journal_id = res[0]

        if not journal_id:
            return False
        journal = journal_pool.browse(journal_id)
        account_id = journal.default_credit_account_id or journal.default_debit_account_id
        if account_id and account_id.tax_ids:
            tax_id = account_id.tax_ids[0].id
            return tax_id
        return False

account_invoice()


