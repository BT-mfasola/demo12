from odoo import api, models
from odoo.exceptions import UserError
class report_shipping_instance_parser(models.AbstractModel):
    _name = 'report.shipping_integration_ept.report_shipping_instance_ept'
    _description="Report Shipping Instance"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['shipping.instance.ept'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'shipping.instance.ept',
            'docs': docs,
            'data': data,
            'display_delivery_method': self.display_delivery_method,
            'display_stock_picking_attribute': self.display_stock_picking_attribute,
        }
    @api.multi
    def display_delivery_method(self,shipping_instance_id):
        shipping_services_obj = self.env['delivery.carrier']
        services = shipping_services_obj.search([('shipping_instance_id','=',shipping_instance_id)])
        return services
    @api.multi
    def display_stock_picking_attribute(self,id):
        picking_obj = self.env['stock.picking']
        order_information = picking_obj.search([('carrier_id','=',id),('state','=',"done"),('carrier_tracking_ref' ,'!=',False)])
        return order_information