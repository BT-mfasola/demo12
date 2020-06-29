# Copyright (c) 2018 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import models, fields, api, _
import os
import base64
from odoo.exceptions import Warning, ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)

class StockPickingBatchEpt(models.Model):
    _inherit = "stock.picking.batch"
    ready_for_download = fields.Boolean('ReadyForDownload', help="It's True when done wave.", default=False, copy=False)
    delivery_type_ept= fields.Selection([('fixed','Fixed Price'),('base_on_rule','based_on_rule')], string='Provider', default='fixed',help="Display pickings, Those are included in selected provider",copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'Running'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('send_to_shipper', 'Send To Shipper')], default='draft',
        copy=False, track_visibility='onchange', required=True)
    carrier_id = fields.Many2one('delivery.carrier', string="Delivery Method",help="According to the provider, Visible the delivery method.",copy=False)
    batch_processed_using_cron = fields.Boolean('Batch Processed Using CronJob', help="If Batch Process Completed Using The CronJob Than Valuse Is TRUE..", default=False, copy=False)

    @api.multi
    def done(self):
        """ Checked the some condition like button validate.
            @param: none
            @return: If issue in picking than raise the warning other wise working good.
            @author: Emipro Technologies - Jigar v vagadiya on date 12 sep 2018.
        """
        pickings = self.mapped('picking_ids').filtered(lambda picking: picking.state not in ('cancel', 'done'))
        for picking in pickings:
            try:
                picking.button_validate()
            except Exception as e:
                raise UserError(_("Issue While validate the picking : %s, %s" % (picking.name, e)))
        return super(StockPickingBatchEpt,self).done()

    @api.multi
    def send_to_shipper_ept(self):
        """ Execute these method when clicking on send_to_shipper button.
            @param: none
            @return: Pass all request to provider.
            @author: Emipro Technologies - Jigar v vagadiya on date 6 feb 2018.
        """
        self.ensure_one()
        pickings = self.picking_ids.filtered(lambda x: x.picking_type_code in ('outgoing') and x.state in (
        'done') and x.carrier_id and x.send_to_ship_using_batch_picking == False and not x.carrier_tracking_ref)
        if pickings:
            for picking in pickings:
                try:
                    if picking.carrier_id and picking.carrier_id.delivery_type not in ['fixed','base_on_rule'] and picking.carrier_id.integration_level == 'rate_and_ship':
                        picking.send_to_shipper()
                    picking.send_to_ship_using_batch_picking = True
                    if picking.carrier_tracking_ref:
                        self.ready_for_download = True
                except Exception as e:
                    message="Delivery Order : %s Description : %s"%(picking.name,e)
                    self.message_post(body=message)
                    _logger.info("Error while processing for send to Shipper - Picking : %s " % (picking.name))
        pickings = self.picking_ids.filtered(lambda x: x.picking_type_code in ('outgoing') and x.state in (
        'done') and x.carrier_id and x.send_to_ship_using_batch_picking == False and not x.carrier_tracking_ref)

        if len(pickings) < 1:
            self.write({'state': 'send_to_shipper'})

    @api.multi
    def download_labels(self):
        """Download labels, In wave all labels download those are generated.
            @param: none
            @return: Zip file for all labels.
            @author: Emipro Technologies - Jigar v vagadiya on date 6 feb 2018.
        """
        self.ensure_one()
        file_path = "/tmp/waves/"
        directory = os.path.dirname(file_path)
        try:
            os.stat(directory)
        except:
            os.system("mkdir %s" % (file_path))

        pickings=self.picking_ids.filtered(lambda x: x.picking_type_code in ('outgoing') and x.state in ('done') and x.carrier_id and x.carrier_tracking_ref)
        for picking in pickings:
            file_name = picking.name
            file_name = file_name.replace('/', '_')
            label_attachments=self.env['ir.attachment'].search([('res_model','=','stock.picking'),('res_id','=',picking.id)])
            if not label_attachments:
                continue
            for sequence, label_attachment in enumerate(label_attachments, start=1):
#             for label_attachment in label_attachments:
                file_extension=label_attachment.name.split('.')[1] if label_attachment.name.split('.')[1] else "pdf"
                with open("%s%s_%s.%s" % (file_path,sequence, file_name,file_extension), "wb") as f:
                    f.write(base64.b64decode(label_attachment and label_attachment.datas))
        file_name = "%s.tar.gz" %(self.name and self.name.replace('/', '_') or 'Shipping_Labels')
        if os.stat(directory):
            os.system("tar -czvf /tmp/%s %s"%(file_name,directory))
            os.system("rm -R %s"%(directory))
        with open("/tmp/%s" % (file_name), "rb") as f1:
            f1.seek(0)
            buffer = data = f1.read()
            f1.close()
            file_data_temp = base64.b64encode(buffer)
        att_id = self.env['ir.attachment'].create({'name':"Wave -%s"%(file_name or ""),'datas_fname':"Wave - %s.pdf"%(file_name or ""), 'type':'binary', 'datas': file_data_temp or "",'mimetype':'application/pdf' , 'res_model': 'stock.picking.batch', 'res_id':self.id, 'res_name' :self.name })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=ir.attachment&field=datas&id=%s&filename=Shipping_Labels.tar.gz' % (
                att_id.id),
            'target': 'self'
        }

    @api.multi
    def download_invoices(self):
        """download_invoices, In wave all picking though generate the invoices.
            @param: none
            @return: Zip file for all Invoices.
            @author: Emipro Technologies - Jigar v vagadiya on date 19 Sep 2018.
        """
        # for picking_id in self.picking_ids:
        #     if picking_id.sale_id and picking_id.sale_id.invoice_ids
        self.ensure_one()
        allow_partial_invoice = self.env['ir.config_parameter'].sudo().get_param('batch_pickings_validate_ept.download_partial_invoice')
        invoice_ids=[]
        invoice_messgages=[]
        not_allow_invoice=False
        for picking_id in self.picking_ids:
            if picking_id.sale_id and picking_id.sale_id.invoice_ids:
                for invoice_id in picking_id.sale_id.invoice_ids:
                    invoice_ids.append(invoice_id.id)
            else:
                not_allow_invoice=True
                invoice_messgages.append("Invoice Is Not Created For This Order %s (%s)."%(picking_id.origin,picking_id.name))
        if not invoice_ids:
            raise ValidationError("Invoice is not available.!")
        if not allow_partial_invoice and not_allow_invoice:
            raise ValidationError("Invoice Is Not Available In Following Order\n %s"%('\n'.join(invoice_messgages)))
        invoices = self.env['account.invoice'].search([('id', 'in', invoice_ids)])
        return self.env.ref('account.account_invoices').report_action(invoices)