# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
import time
from odoo import models, fields, api, _

class ShipmentReportEpt(models.TransientModel):
    _name = "shipment.report.ept"
    _description="Shipment Report"
    
    from_date = fields.Date('From')
    to_date = fields.Date('To') 