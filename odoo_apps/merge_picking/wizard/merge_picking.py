# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError, RedirectWarning, ValidationError, Warning

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    merged = fields.Boolean(string='Merged')

    @api.multi
    @api.depends('order_line.move_ids')
    def _compute_picking(self):
        for order in self:
            pickings = self.env['stock.picking']
            for line in order.order_line:
                # We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
                # do some recursive search, but that could be prohibitive if not done correctly.
                moves = line.move_ids | line.move_ids.mapped('returned_move_ids')
                moves = moves.filtered(lambda r: r.state != 'cancel')
                pickings |= moves.mapped('picking_id')
            order.picking_ids = pickings
        for order in self:
            if order.merged:
                for a in self.env['stock.picking'].search([]):
                    if a.purchase_ids:
                        for b in a.purchase_ids:
                            if order.id == b.id:
                                order.picking_ids = [(4, a.id)]
        for order in self:
            order.picking_count = len(order.picking_ids)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sale_ids = fields.Many2many('sale.order',string = 'sale references')
    purchase_ids = fields.Many2many('purchase.order',string = 'Purchase references')

class SaleOrder(models.Model):
    _inherit = "sale.order"

    merged = fields.Boolean(string='Merged')

    @api.multi
    @api.depends('procurement_group_id')
    def _compute_picking_ids(self):
        for order in self:
            order.picking_ids = self.env['stock.picking'].search([('group_id', '=', order.procurement_group_id.id)]) if order.procurement_group_id else []
            order.delivery_count = len(order.picking_ids)
        for order in self:
            if order.merged:
                for a in self.env['stock.picking'].search([]):
                    if a.sale_ids:
                        for b in a.sale_ids:
                            if order.id == b.id:
                                order.picking_ids = [(4, a.id)]
        for order in self:
            order.delivery_count = len(order.picking_ids)
            
            

    picking_ids = fields.Many2many('stock.picking', compute='_compute_picking_ids', string='Picking associated to this sale')
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')
    
class MergePicking(models.TransientModel):
    _name = "merge.picking"
    _description = "merge pickings"
    

    @api.model
    def default_get(self, fields):
        rec = super(MergePicking, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        
        if active_ids:
            pick_ids = []
            picks = self.env['stock.picking'].browse(active_ids)
            
            if any(pick.state == 'done' for pick in picks):
                raise Warning ('Merging is Not allowed on Done Pickings.')
                    
            pick_ids = [pick.id for pick in picks if pick.state in ('draft', 'confirmed', 'assigned')]
                 
            if 'pickings_ids' in fields:
                rec.update({'pickings_ids': pick_ids})
        return rec
            
    
    pickings_ids = fields.Many2many('stock.picking',  'merge_picking_rel', 'merge_id', 'picking_id', 'Pickings',  domain=[('state', '!=', 'done')])
    
    @api.multi
    def merge_pickings(self):
        pick_obj = self.env['stock.picking']
        mod_obj = self.env['ir.model.data']
        move_obj = self.env['stock.move']
        action = mod_obj.xmlid_to_object('stock.stock_picking_action_picking_type')
        form_view_id = mod_obj.xmlid_to_res_id('stock.view_picking_form')
        pickings = pick_obj.browse(self._context.get('active_ids', []))
        invoice_status = []
        pick_state = []
        pick_ids = []
        pick_partner = []
        moves_product = []
        pick_type = []
        origin = ''
        type_new_pick = 0
        location_id = 0
        location_dest_id = 0
        custom_sale_list = []
        custom_purchase_list = []
        
        if len(pickings) < 2:
            raise Warning ('Please select multiple picking to merge in the list view.')
                    
        if any(pick.state == 'done' for pick in pickings):
            raise Warning ('Merging is Not allowed on Done Pickings.')

        for pick in pickings:
            pick_type.append(pick.picking_type_id)
            
            if not pick_type[1:] == pick_type[:-1]:
                raise Warning ('Merging is only allowed on Pickings of same Types.')
                
            else:
                type_new_pick = pick.picking_type_id.id
                location_dest_id = pick.location_dest_id.id
                location_id = pick.location_id.id

        new_pick = pick_obj.create({'picking_type_id':type_new_pick, 'location_dest_id':location_dest_id, 'location_id':location_id, 'state': 'draft'})
        pick_name = new_pick.name


        for pick in pickings:
            origin += pick.name
            pick_state.append(pick.state)
            pick_partner.append(pick.partner_id)
            pick_type.append(pick.picking_type_id)
            invoice_status.append(pick.sale_id.invoice_status)
            
            if not pick_type[1:] == pick_type[:-1]:
                raise Warning ('Merging is only allowed on Pickings of same Types.')
            
            if not pick_state[1:] == pick_state[:-1]:
                raise Warning ('Merging is only allowed on Pickings of same State.')
                
            if not pick_partner[1:] == pick_partner[:-1]:
                raise Warning ('Merging is only allowed on Pickings of same Partner.')
                
            if not invoice_status[1:] == invoice_status[:-1]:
                raise Warning ('Merging is only allowed on Pickings of same Invoice Status.')
            msg_origin = ""
            origin_list = []

            for i in range(len(origin_list)):
                if i == len(origin_list) - 1:
                    msg_origin = msg_origin + origin_list[i] + "."
                else :
                    msg_origin = msg_origin + origin_list[i] + ","

            for move in pick.move_lines:
                new_move = move_obj.create({
		                'name': move.name or '',
		                'product_id': move.product_id and move.product_id.id or False,
		                'product_uom_qty': move.product_qty,
		                'product_uom': move.product_uom and move.product_uom.id or False,
		                'date': move.date,
		                'date_expected': move.date_expected,
		                'location_id':move.location_id and move.location_id.id or False,
		                'location_dest_id':move.location_dest_id and move.location_dest_id.id or False,
		                'picking_id': new_pick.id,
		                'partner_id': move.partner_id and move.partner_id.id or False,
		                'move_dest_ids': [(6,0,move.move_dest_ids.ids)] or False,
		                'state': move.state,
		                'company_id': move.company_id.id,
		                'price_unit': move.price_unit,
                        'group_id':move.group_id.id,

        			})
                moves_product.append(move.product_id.id)
                if move.purchase_line_id:
                    new_move.purchase_line_id = move.purchase_line_id
                if move.sale_line_id:
                    new_move.sale_line_id = move.sale_line_id
            if pick.sale_id:
                custom_sale_list.append(pick.sale_id.id)
                pick.sale_id.merged = True 
            else:
                custom_purchase_list.append(pick.purchase_id.id)
                if pick.purchase_id:
                    pick.purchase_id.merged = True 
                       
            new_pick.write({'invoice_state': pick.sale_id.invoice_status, 'state': pick.state, 'partner_id': pick.partner_id and pick.partner_id.id or False,'origin':origin})      
            origin += '-'
            if pick_ids:
                new_id = pick.id
                pick_ids.append(new_id)
            else:
                pick_ids.append(pick.id)
            new_pick.write({'pick_name': pick_ids})   
            new_pick.action_confirm()
            new_pick.action_assign()
            pick.action_cancel()    
            msg_body = _("This delivery order has been created from: <b>%s</b>") % (msg_origin)
            new_pick.message_post(body=msg_body)
        new_pick.sale_ids = [(6,0,custom_sale_list)]
        new_pick.purchase_ids = [(6,0,custom_purchase_list)]    

        result =  {
        'type': 'ir.actions.act_window',
        'res_model': 'stock.picking',
        'view_mode': 'form',
        'view_type': 'form',
        'res_id': new_pick.id,
        'views': [(False, 'form')],
    }
        return result
            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
