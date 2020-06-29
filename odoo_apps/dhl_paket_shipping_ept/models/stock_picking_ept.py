# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import models, fields, api, _
from odoo.exceptions import Warning
from odoo.addons.delivery.models.stock_picking import StockPicking as BaseStockPicking

class StockPickingEpt(models.Model):
    _inherit = 'stock.picking'
    delivery_carrier_type_ept = fields.Boolean(compute='delivery_carrier_type')

    def delivery_carrier_type(self):
        """ SendToShip button visible or Invisible as per situation.
            @param:
            @return: Visible or Invisible button
            @author: Jigar Vagadiya
        """
        for picking in self:
            if picking.carrier_id.delivery_type == "dhl_de_ept":
                picking.delivery_carrier_type_ept = True
            else:
                picking.delivery_carrier_type_ept = False

    @api.multi
    def action_done(self):
        '''added by Emipro Technologies Pvt Ltd'''
        res = super(BaseStockPicking, self).action_done()
        for id in self:
            if id.carrier_id and id.carrier_id.delivery_type not in ['dhl_de_ept'] and id.carrier_id.integration_level == 'rate_and_ship':
                id.send_to_shipper()

            if id.carrier_id:
                id._add_delivery_cost_to_so()
        return res
    BaseStockPicking.action_done = action_done