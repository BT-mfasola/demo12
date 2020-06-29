import json
from odoo import SUPERUSER_ID
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from datetime import datetime
from odoo.exceptions import Warning
import time


class magento_instance(models.Model):
    _inherit = 'magento.shop'
    _description = "The prestashop determines the prestashop view"
    # _order = 'sequence'

    magento_kanban_instance = fields.Text(compute='_magento_kanban_instace')

    
    @api.one
    def _magento_kanban_instace(self):
        order_obj = self.env['sale.order']
        invoice_obj = self.env['account.invoice']
        stock_obj = self.env['stock.picking']
        #shop_obj = self.env['sale.shop']
       
        #shop_id  = shop_obj.search([('prestashop_instance_id','=',self.id)])

        all_order_ids = order_obj.search([('store_id','=',self[0].id)]) 
        pending_order_ids = order_obj.search([('store_id','=',self[0].id),('state','in',('sale','sent'))])       
        complete_order_ids = order_obj.search([('store_id','=',self[0].id),('state','=','done')])
        draft_order_ids = order_obj.search([('store_id','=',self[0].id),('state','=','draft')])
        cancel_order_ids = order_obj.search([('store_id','=',self[0].id),('state','=','cancel')])
        
        origin_list = [s.name for s in all_order_ids]
        all_invoice_ids = invoice_obj.search([('is_magento','=',True),('invoice_store_id','=',self[0].id),('origin', 'in', origin_list)])
        pending_invoice_ids = invoice_obj.search([('is_magento','=',True),('origin', 'in', origin_list),('invoice_store_id','=',self[0].id),('state','=','open')])
        complete_invoice_ids = invoice_obj.search([('is_magento','=',True),('origin', 'in', origin_list),('invoice_store_id','=',self[0].id),('state','=','paid')])
        draft_invoice_ids = invoice_obj.search([('is_magento','=',True),('origin', 'in', origin_list),('invoice_store_id','=',self[0].id),('state','=','draft')])
        cancel_invoice_ids = invoice_obj.search([('is_magento','=',True),('origin', 'in', origin_list),('invoice_store_id','=',self[0].id),('state','=','cancel')])
        
        all_stock_ids = stock_obj.search([('is_magento','=',True),('magento_shop','=',self[0].id), ('origin', 'in', origin_list)])
        pending_stock_ids = stock_obj.search([('is_magento','=',True),('magento_shop','=',self[0].id),('origin', 'in', origin_list),('state','in',('confirmed','partially_available','assigned'))])
        complete_stock_ids = stock_obj.search([('is_magento','=',True),('magento_shop','=',self[0].id),('origin', 'in', origin_list),('state','=','done')])
#         late_delivey_ids = stock_obj.search([('is_presta','=',True),('origin', 'in', origin_list),('min_date','<',datetime.today())])
 #       back_order_ids = stock_obj.search([('is_presta','=',True),('origin', 'in', origin_list),('backorder_id','<>', False)])
#        
#        
        magento_webservices ={
                                 
        'all_order': len(all_order_ids),
        'pending_order': len(pending_order_ids),
        'complete_order': len(complete_order_ids),
        'draft_order': len(draft_order_ids),
        'cancel_order': len(cancel_order_ids),
        
        'all_invoice': len(all_invoice_ids),
        'pending_invoice': len(pending_invoice_ids),
        'complete_invoice': len(complete_invoice_ids),
        'draft_invoice': len(draft_invoice_ids),
        'cancel_invoice': len(cancel_invoice_ids),
#         
        'all_stock': len(all_stock_ids),
        'pending_stock': len(pending_stock_ids),
        'complete_stock': len(complete_stock_ids),
# #         'late_delivey':late_delivey_ids,
#        'back_order': len(back_order_ids),

        }
        self.magento_kanban_instance = json.dumps(magento_webservices)


    @api.multi
    def action_view_all_order(self):
        order_obj = self.env['sale.order']
        order_id = order_obj.search([('store_id','=',self.id),('magento_order','=',True)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_orders_to_invoice')
        list_view_id = imd.xmlid_to_res_id('sale.view_quotation_tree')
        form_view_id = imd.xmlid_to_res_id('sale.view_order_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(order_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % order_id.ids
#         elif len(order_id) == 1:
#             result['views'] = [(form_view_id, 'form')]
#             result['res_id'] = order_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    @api.multi
    def action_view_draft_order(self):
        order_obj = self.env['sale.order']
        order_id = order_obj.search([('store_id','=',self.id),('state','=','draft'),('magento_order','=',True)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_orders_to_invoice')
        list_view_id = imd.xmlid_to_res_id('sale.view_quotation_tree')
        form_view_id = imd.xmlid_to_res_id('sale.view_order_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(order_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % order_id.ids
#         elif len(order_id) == 1:
#             result['views'] = [(form_view_id, 'form')]
#             result['res_id'] = order_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    @api.multi
    def action_view_cancel_order(self):
        order_obj = self.env['sale.order']
        order_id = order_obj.search([('store_id','=',self.id),('state','=','cancel'),('magento_order','=',True)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_orders_to_invoice')
        list_view_id = imd.xmlid_to_res_id('sale.view_quotation_tree')
        form_view_id = imd.xmlid_to_res_id('sale.view_order_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(order_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % order_id.ids
#         elif len(order_id) == 1:
#             result['views'] = [(form_view_id, 'form')]
#             result['res_id'] = order_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    

    @api.multi
    def action_view_pending_order(self):
        order_obj = self.env['sale.order']
        order_id = order_obj.search([('store_id','=',self.id),('state','in',('sale','sent')),('magento_order','=',True)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_orders_to_invoice')
        list_view_id = imd.xmlid_to_res_id('sale.view_quotation_tree')
        form_view_id = imd.xmlid_to_res_id('sale.view_order_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(order_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % order_id.ids
#         elif len(order_id) == 1:
#             result['views'] = [(form_view_id, 'form')]
#             result['res_id'] = order_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


    @api.multi
    def action_view_complete_order(self):
        order_obj = self.env['sale.order']
        order_id = order_obj.search([('store_id','=',self.id),('state','=','done'),('magento_order','=',True)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_orders_to_invoice')
        list_view_id = imd.xmlid_to_res_id('sale.view_quotation_tree')
        form_view_id = imd.xmlid_to_res_id('sale.view_order_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(order_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % order_id.ids
#         elif len(order_id) == 1:
#             result['views'] = [(form_view_id, 'form')]
#             result['res_id'] = order_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


    @api.multi
    def action_view_all_invoice(self):
        invoic_obj = self.env['account.invoice']
        invoice_id  = invoic_obj.search([('is_magento','=',True),('invoice_store_id','=',self[0].id)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(invoice_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % invoice_id.ids
#         elif len(invoice_id) == 1:
#             result['views'] = [(form_view_id, 'form')]
#             result['res_id'] = invoice_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
 
 
    @api.multi
    def action_view_pending_invoice(self):
        invoic_obj = self.env['account.invoice']
        invoice_id = invoic_obj.search([('is_magento','=',True),('invoice_store_id','=',self[0].id),('state','=','open')])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(invoice_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % invoice_id.ids
#         elif len(invoice_id) == 1:
#             result['views'] = [(form_view_id, 'form')]
#             result['res_id'] = invoice_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    @api.multi
    def action_view_draft_invoice(self):
        invoic_obj = self.env['account.invoice']
        invoice_id = invoic_obj.search([('is_magento','=',True),('state','=','draft'),('invoice_store_id','=',self[0].id)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(invoice_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % invoice_id.ids
#         elif len(invoice_id) == 1:
#             result['views'] = [(form_view_id, 'form')]
#             result['res_id'] = invoice_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    @api.multi
    def action_view_cancel_invoice(self):
        invoic_obj = self.env['account.invoice']
        invoice_id = invoic_obj.search([('is_magento','=',True),('state','=','cancel'),('invoice_store_id','=',self[0].id)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(invoice_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % invoice_id.ids
#         elif len(invoice_id) == 1:
#             result['views'] = [(form_view_id, 'form')]
#             result['res_id'] = invoice_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
 
    @api.multi
    def action_view_complete_invoice(self):
        invoic_obj = self.env['account.invoice']
        invoice_id = invoic_obj.search([('is_magento','=',True),('state','=','paid'),('invoice_store_id','=',self[0].id)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(invoice_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % invoice_id.ids
#         elif len(invoice_id) == 1:
#             result['views'] = [(form_view_id, 'form')]
#             result['res_id'] = invoice_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result    
    
    
    @api.multi
    def action_view_all_stock(self):
        stock_obj = self.env['stock.picking']
        stock_id = stock_obj.search([('is_magento','=',True),('magento_shop','=',self[0].id)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('stock.action_picking_tree_all')
        list_view_id = imd.xmlid_to_res_id('stock.vpicktree')
        form_view_id = imd.xmlid_to_res_id('stock.view_picking_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(stock_id) > 1:
            result['domain'] = "[('id','in',%s)]" % stock_id.ids
#         elif len(stock_id) == 1:
#             result['views'] = [(form_view_id, 'form')]
#             result['res_id'] = stock_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
    
    
    @api.multi
    def action_view_pending_stock(self):
        stock_obj = self.env['stock.picking']
        stock_id = stock_obj.search([('is_magento','=',True),('magento_shop','=',self[0].id),('state','in',('confirmed','partially_available','assigned'))])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('stock.action_picking_tree_all')
        list_view_id = imd.xmlid_to_res_id('stock.vpicktree')
        form_view_id = imd.xmlid_to_res_id('stock.view_picking_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(stock_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % stock_id.ids
#         elif len(stock_id) == 1:
#             result['views'] = [(form_view_id, 'form')]
#             result['res_id'] = stock_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


    @api.multi
    def action_view_complete_stock(self):
        stock_obj = self.env['stock.picking']
        stock_id = stock_obj.search([('is_magento','=',True),('state','=','done'),('magento_shop','=',self[0].id)])
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('stock.action_picking_tree_all')
        list_view_id = imd.xmlid_to_res_id('stock.vpicktree')
        form_view_id = imd.xmlid_to_res_id('stock.view_picking_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(stock_id) >= 1:
            result['domain'] = "[('id','in',%s)]" % stock_id.ids
#         elif len(stock_id) == 1:
#             result['views'] = [(form_view_id, 'form')]
#             result['res_id'] = stock_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

#     @api.multi
#     def presta_action_picking_tree_late(self):
#         shop_obj = self.env['sale.shop']
#         order_obj =self.env['sale.order']
#         stock_obj = self.env['stock.picking']
#         shop_id  = shop_obj.search([('prestashop_instance_id','=',self.id)])
#         all_order_ids = order_obj.search([('shop_id','=',shop_id.id)])
#         origin_list = [s.name for s in all_order_ids] 
#         all_stock_ids = stock_obj.search([('is_presta','=',True), ('origin', 'in', origin_list)])
#     
#         imd = self.env['ir.model.data']
#         action = imd.xmlid_to_object('stock.action_picking_tree_late')
#         list_view_id = imd.xmlid_to_res_id('stock.vpicktree')
#         form_view_id = imd.xmlid_to_res_id('stock.view_picking_form')
#         result = {
#             'name': action.name,
#             'help': action.help,
#             'type': action.type,
#             'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
#             'target': action.target,
#             'context':{'search_default_late':1,'search_default_confirmed':1},
#             'res_model': action.res_model,
#         }
#         print "result", result
#         if len(all_stock_ids) >= 1:
#             result['domain'] = "[('id','in',%s)]" % all_stock_ids.ids
# #         elif len(stock_id) == 1:
# #             result['views'] = [(form_view_id, 'form')]
# #             result['res_id'] = stock_id.ids[0]
#         else:
#             result = {'type': 'ir.actions.act_window_close'}
#         return result
#     
#     @api.multi
#     def presta_action_picking_tree_backorder(self):
#         shop_obj = self.env['sale.shop']
#         order_obj =self.env['sale.order']
#         stock_obj = self.env['stock.picking']
#         shop_id  = shop_obj.search([('prestashop_instance_id','=',self.id)])
#         all_order_ids = order_obj.search([('shop_id','=',shop_id.id)])
#         origin_list = [s.name for s in all_order_ids] 
#         all_stock_ids = stock_obj.search([('is_presta','=',True), ('origin', 'in', origin_list)])
#     
#         imd = self.env['ir.model.data']
#         action = imd.xmlid_to_object('stock.action_picking_tree_backorder')
#         list_view_id = imd.xmlid_to_res_id('stock.vpicktree')
#         form_view_id = imd.xmlid_to_res_id('stock.view_picking_form')
#         result = {
#             'name': action.name,
#             'help': action.help,
#             'type': action.type,
#             'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
#             'target': action.target,
#             'context':{'search_default_backorder': 1,'search_default_confirmed': 1},
#             'res_model': action.res_model,
#         }
#         print "result", result
#         if len(all_stock_ids) >= 1:
#             result['domain'] = "[('id','in',%s)]" % all_stock_ids.ids
# #         elif len(stock_id) == 1:
# #             result['views'] = [(form_view_id, 'form')]
# #             result['res_id'] = stock_id.ids[0]
#         else:
#             result = {'type': 'ir.actions.act_window_close'}
#         return result
#     
#     
#     @api.multi
#     def presta_action_picking_tree_waiting(self):
#         shop_obj = self.env['sale.shop']
#         order_obj =self.env['sale.order']
#         stock_obj = self.env['stock.picking']
#         shop_id  = shop_obj.search([('prestashop_instance_id','=',self.id)])
#         all_order_ids = order_obj.search([('shop_id','=',shop_id.id)])
#         origin_list = [s.name for s in all_order_ids] 
#         all_stock_ids = stock_obj.search([('is_presta','=',True), ('origin', 'in', origin_list)])
#     
#         imd = self.env['ir.model.data']
#         action = imd.xmlid_to_object('stock.action_picking_tree_waiting')
#         list_view_id = imd.xmlid_to_res_id('stock.vpicktree')
#         form_view_id = imd.xmlid_to_res_id('stock.view_picking_form')
#         result = {
#             'name': action.name,
#             'help': action.help,
#             'type': action.type,
#             'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'kanban'], [False, 'pivot']],
#             'target': action.target,
#             'context':{'search_default_waiting': 1,},
#             'res_model': action.res_model,
#         }
#         print "result", result
#         if len(all_stock_ids) >= 1:
#             result['domain'] = "[('id','in',%s)]" % all_stock_ids.ids
# #         elif len(stock_id) == 1:
# #             result['views'] = [(form_view_id, 'form')]
# #             result['res_id'] = stock_id.ids[0]
#         else:
#             result = {'type': 'ir.actions.act_window_close'}
#         return result
# 
# 
#     