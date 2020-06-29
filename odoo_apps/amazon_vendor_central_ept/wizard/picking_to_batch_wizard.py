from odoo import fields, models, api, _
from odoo import models,fields,api,_
from odoo.exceptions import Warning
from odoo.osv import expression,osv
from datetime import datetime
from ftplib import FTP
from tempfile import NamedTemporaryFile
import time
#import paramiko
import base64
import csv
import time
from io import StringIO,BytesIO

class picking_to_batch_wizard(models.TransientModel):
    _name = 'picking.to.batch.wizard'
    _description = 'picking to batch wizard'
    
    batch_id = fields.Many2one('stock.picking.batch', string="Batch",domain="[('vendor_id', '!=', False)]")
    picking_ids = fields.Many2many('stock.picking',string="Select Pickings",domain="[('vendor_id', '!=', False)]")
    
       
    @api.onchange('batch_id')
    def pickings_set(self):
        self.picking_ids = self.batch_id.mapped('picking_ids')
      
    @api.multi
    def batch_report(self):
        packages = self.picking_ids.mapped('package_ids')
        
        if not packages:
            raise Warning("Picking has no Packages")
        
        if self.batch_id:
            return self.batch_id.batch_report()
        else:
            return self.picking_ids.batch_picking_package_report()
    
    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}