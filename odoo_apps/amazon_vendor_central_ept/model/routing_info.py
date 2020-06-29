from odoo import models, fields, api, _
from odoo.osv import expression,osv
from odoo.exceptions import Warning
from ftplib import FTP
from tempfile import NamedTemporaryFile
from amazon_edi_interface import AmazonEDIInterface
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
#import paramiko
import base64
import csv
import logging
_logger = logging.getLogger(__name__)

class Routing_Information(models.Model):
    """
    Manage routing request and routing instruction detail and manage Pending order
    """
    _name = 'routing.information'

    name = fields.Char(string = 'Name')
    state = fields.Selection([('routing_request_sent','Routing Request Sent'),('routing_instruction_received','Routing Instruction Received'),('delivered','Delivered'),])
    sale_order_id = fields.Many2one('sale.order', string = 'Sale Order')
    vendor_id = fields.Many2one('amazon.vendor.instance', string = 'Vendor')
    stock_picking_id = fields.Many2one('stock.picking', string = 'Stock Picking')
    package_ids = fields.Many2many('stock.quant.package', string = 'Packages')
    warehouse_id = fields.Many2one('stock.warehouse', string = 'Warehouse')
    carrier_id = fields.Many2one('delivery.carrier', string = 'Delivery Carrier')
    booking_ref_number = fields.Char(string = 'Booking Reference Number')
    delivery_date = fields.Datetime(string = 'Delivery Date')
