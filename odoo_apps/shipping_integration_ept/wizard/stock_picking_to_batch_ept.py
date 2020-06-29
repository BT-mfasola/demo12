# Copyright (c) 2018 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
# -*- coding: utf-8 -*-
import ast
from odoo import api, fields, models, _
from odoo.exceptions import Warning, ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class StockPickingToBatchEpt(models.TransientModel):
    _name = 'stock.picking.to.batch.ept'
    _description = 'Add pickings to a batch picking'

    delivery_type_ept = fields.Selection(
        [('fixed','Fixed Price'),('base_on_rule','based_on_rule')],
        string='Provider', default='fixed',
        help="Display pickings, Those are included in selected provider", copy=False)
    carrier_id = fields.Many2one('delivery.carrier', string="Delivery Method",
                                 help="According to the provider, Visible the delivery method.", copy=False)
    start_date = fields.Date(string="Start Date",
                             help="When create the batch picking at that time consider this start date")
    end_date = fields.Date(string="End Date",
                           help="When create the batch picking at that time consider this EndDate")
    batch_id = fields.Many2one('stock.picking.batch', string="Use Existing Batch",
                                 help="If Batch Is Selectes Than Add All Pickings Inside Selected Pickings..", copy=False)

    def create_batch_manually(self):
        """Create batch Using the wizard functionality.
              @param: none
              @return: Create the Batch and Return Batch details.
              @author: Emipro Technologies - Jigar v vagadiya on date 12 sep 2018.
        """
        self.ensure_one()
        batch = self.create_batches(self.carrier_id.id, self.delivery_type_ept, self.start_date, self.end_date,self.batch_id and self.batch_id.id)

        return {
            'name': _("Batch Pickings"),
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('stock_picking_batch.stock_picking_batch_form').id,
            'res_model': 'stock.picking.batch',
            'type': 'ir.actions.act_window',
            'res_id': batch and batch.id,
            'target': 'current',
        }

    @api.multi
    def create_batches(self, carrier_id, provider, start_date=False, end_date=False,batch=False):
        """Create batch. Using this method check the picking and set the batch Id in perticular picking.
              @param: carrier_id,provider,start_date,end_date
              @return: Return Batch details.
              @author: Emipro Technologies - Jigar v vagadiya on date 12 sep 2018.
        """
        batch_picking_obj = self.env['stock.picking.batch']
        qry = "select sp.id from stock_picking sp join stock_picking_type spt on spt.id=sp.picking_type_id where batch_id Is Null and carrier_id=%s and spt.code='outgoing' and state not in('done','cancel') and scheduled_date >= '%s' and scheduled_date<= '%s'" % (carrier_id, start_date,end_date) if start_date and end_date else "select sp.id from stock_picking sp join stock_picking_type spt on spt.id=sp.picking_type_id where batch_id Is Null and carrier_id=%s and spt.code='outgoing' and state not in('done','cancel')" % (carrier_id)
        self._cr.execute(qry)
        pickings = self._cr.fetchall()
        picking_ids = []
        for picking in pickings:
            picking_ids.append(str(picking[0]))
        if not picking_ids:
            raise Warning("Picking is not available according to the filter!")
        # Note : If Found batch for this carrier id that just write batch picking in all pickings otherwise create new batch picking
        if batch:
            batch = batch_picking_obj.browse(batch)
            self._cr.execute('update stock_picking set batch_id=%s WHERE id in (%s)'%(batch.id,','.join(picking_ids)))
        else:
            batch = batch_picking_obj.create({'carrier_id': carrier_id, 'delivery_type_ept': provider})
            self._cr.execute('update stock_picking set batch_id=%s WHERE id in (%s)' % (batch.id, ','.join(picking_ids)))
        carrier_id = self.env['delivery.carrier'].browse(carrier_id)
        batch.write({'user_id': carrier_id.user_id.id if carrier_id and carrier_id.user_id else self.env.user.id})
        return batch

    def create_batch_using_cronjob(self):
        """Using the cronjob create the batch and confirm the batch, Done Batch and generate the label according to the configuration.
              @param: None
              @return: Return Batch details in log.
              @author: Emipro Technologies - Jigar v vagadiya on date 12 sep 2018.
        """
        pick_to_do = self.env['stock.picking']
        batch_picking_obj = self.env['stock.picking.batch']
        pick_to_backorder = self.env['stock.picking']
        carrier_ids = self.env['delivery.carrier'].search([('auto_create_batch', '=', True)])
        batch = self.env['stock.picking.batch']
        for carrier_id in carrier_ids:
            if carrier_id.auto_create_batch:
                batch_id = batch_picking_obj.search([('carrier_id', '=', carrier_id.id), ('state', '=', 'draft'),
                                                     ('batch_processed_using_cron', '=', True)],limit=1)
                batch = self.create_batches(carrier_id.id, carrier_id.delivery_type,False,False,batch_id and batch_id.id if carrier_id.use_existing_batch_cronjob else False)
            if batch and carrier_id.auto_done_pickings:
                self._cr.commit()
                _logger.info("Batch Created : %s" % (batch.name))
                try:
                    batch.confirm_picking()
                    for picking in batch.picking_ids:
                        if picking.state == 'draft':
                            picking.action_confirm()
                            if picking.state != 'assigned':
                                picking.action_assign()
                        for move in picking.move_lines:
                            if move.move_line_ids:
                                for move_line in move.move_line_ids:
                                    move_line.qty_done = move_line.product_uom_qty
                            else:
                                move.quantity_done = move.product_uom_qty
                        if picking._check_backorder():
                            pick_to_backorder |= picking
                            continue
                        pick_to_do |= picking
                        # Process every picking that do not require a backorder, then return a single backorder wizard for every other ones.
                    if pick_to_do:
                        pick_to_do.action_done()
                    if pick_to_backorder:
                        _logger.info("Back Orders Are Available, Please Do Further Process! %s " % (pick_to_backorder))
                    pickings = batch.mapped('picking_ids').filtered(
                        lambda picking: picking.state not in ('cancel', 'done'))
                    if not pickings:
                        batch.done()
                    self._cr.commit()
                    if carrier_id.auto_get_shipping_label and batch.state == "done":
                        batch.send_to_shipper_ept()
                except Exception as e:
                    _logger.info("Done / SendToShipper Process Issue.%s" % (e))
            batch.batch_processed_using_cron = True
            self._cr.commit()
        return True
