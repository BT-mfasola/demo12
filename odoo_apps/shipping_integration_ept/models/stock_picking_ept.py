# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import models, fields, api
from odoo.exceptions import Warning, ValidationError, UserError
from odoo.addons.delivery.models.stock_picking import StockPicking as BaseStockPicking
import logging
_logger = logging.getLogger(__name__)

class StockPickingEpt(models.Model):
    _inherit = 'stock.picking'
    @api.multi
    def action_done(self):
        """send_to_shipper process skip(Dividing whole order process).
           @param: none
           @return: send_to_shipper Process skip while validate order.
           @author: Emipro Technologies - Jigar v vagadiya on date 6 feb 2018.
       """
        res = super(BaseStockPicking, self).action_done()
        for id in self:
            if id.carrier_id and id.carrier_id.delivery_type in ['base_on_rule', 'fixed'] and id.carrier_id.integration_level == 'rate_and_ship':
                id.send_to_shipper()

            if id.carrier_id:
                id._add_delivery_cost_to_so()
        return res
    BaseStockPicking.action_done = action_done
    send_to_ship_using_batch_picking = fields.Boolean('Send To Ship Using Waves', copy=False, readonly=True,
                                                      help="When completed the Send To Ship process, Set the True automatically.")


