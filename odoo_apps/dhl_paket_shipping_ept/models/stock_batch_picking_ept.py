# Copyright (c) 2018 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import models, fields, api, _

class DHLPacketStockPickingBatchEpt(models.Model):
    _inherit = "stock.picking.batch"
    delivery_type_ept = fields.Selection(selection_add=[('dhl_de_ept', 'DHL DE')])
    
    dhl_recipient_add_method = fields.Selection([('dhl_street', ' Street'), ('dhl_packstation', ' Packstation'), ('dhl_filiale', ' Filiale'), ('dhl_parcelshop', ' Parcelshop')], 'Recipient Address Type', required=True, help="Select the Recipient address type and set method.", default="dhl_street")


class DHLPacketStockPickingToBatchEpt(models.TransientModel):
    _inherit = 'stock.picking.to.batch.ept'
    delivery_type_ept = fields.Selection(selection_add=[('dhl_de_ept', 'DHL DE')])