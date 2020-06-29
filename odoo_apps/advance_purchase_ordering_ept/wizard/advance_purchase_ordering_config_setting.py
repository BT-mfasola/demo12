from odoo import fields, models, api

class AdvancePurchaseOrderingConfigSetting(models.TransientModel): 
    _inherit = 'res.config.settings'
    _description = 'Advance Purchase Order Setting'
    
    requisition_send_email = fields.Boolean(string='Send Email ', default=False)
    approval_by_authorised = fields.Boolean(string="Approval By Authorised User", default=False)
    
    @api.model
    def get_values(self):
        res = super(AdvancePurchaseOrderingConfigSetting, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(requisition_send_email=eval(params.get_param('advance_purchase_ordering_ept.requisition_send_email', default='False')),
                    approval_by_authorised=eval(params.get_param('advance_purchase_ordering_ept.approval_by_authorised', default='False')))
        return res
    

   
    def set_values(self):
        super(AdvancePurchaseOrderingConfigSetting, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("advance_purchase_ordering_ept.requisition_send_email", repr(self.requisition_send_email))
        ICPSudo.set_param("advance_purchase_ordering_ept.approval_by_authorised", repr(self.approval_by_authorised))
        
