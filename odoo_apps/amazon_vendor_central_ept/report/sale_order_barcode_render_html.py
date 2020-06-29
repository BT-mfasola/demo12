from odoo import models, fields, api, _

class AmazonSaleOrderBarcodeLabel(models.AbstractModel):
    _name = 'report.amazon_vendor_central_ept.report_edi_barcode'
    _description = 'Report Amazon Vendor Central Ept Report Edi Barcode'

    @api.model
    def render_html(self, docids, data=None):
        self.model = 'sale.order'
        docs = self.env[self.model].browse(docids)
        package_information = self.env['sale.order'].get_package_information(order_id=docs.id)
        report_obj = self.env['report']
        paperformat_id = self.env.ref('amazon_vendor_central_ept.paperformate_edi_sale_order')
        report = report_obj._get_report_from_name('amazon_vendor_central_ept.report_edi_barcode')
        if not report.paperformat_id:
            report.write({'paperformat_id':paperformat_id.id})

        docargs = {
            'doc_ids':self.ids,
            'doc_model':self.model,
            'docs':docs,
            'packages':package_information,
            'total_packages':len(package_information),
        }
        return self.env['report'].render('amazon_vendor_central_ept.report_edi_barcode', docargs)