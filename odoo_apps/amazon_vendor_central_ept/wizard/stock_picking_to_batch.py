# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockPickingToBatch(models.TransientModel):
    _inherit = 'stock.picking.to.batch'
    
    #batch_id = fields.Many2one('stock.picking.batch', string='Batch Picking', oldname="wave_id")
    @api.multi
    def attach_pickings(self):
        # use active_ids to add picking line to the selected batch
        res = super(StockPickingToBatch,self).attach_pickings()
        picking_ids = self.env.context.get('active_ids')
        picking_ids = self.env['stock.picking'].browse(picking_ids)
        packages = picking_ids.mapped('package_ids')
        vendor = picking_ids[0].vendor_id
        carrier_type = picking_ids[0].carrier_type
        self.batch_id.write({'package_ids' : [(6,0,packages.ids)],'vendor_id' : vendor.id ,'carrier_type' : carrier_type})
        return res   