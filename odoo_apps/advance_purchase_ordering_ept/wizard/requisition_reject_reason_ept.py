from odoo import api, fields, models

class RequisitionRejectReason(models.TransientModel):
    """
        This wizard can be launched from an Requisition Process
    """

    _name = "requisition.reject.reason.ept"
    _description = "Reorder Reject Reason wizard"

    reason = fields.Text(string='Reason', required=True)
    requisition_process_id = fields.Many2one('requisition.process.ept')
    warehouse_requisition_process_id = fields.Many2one('warehouse.requisition.process.ept')
    
    @api.model
    def default_get(self, fields):
        res = super(RequisitionRejectReason, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        if self._context.get('active_model') == 'requisition.process.ept':
            res.update({'requisition_process_id':active_ids and active_ids[0]})
        else:
            res.update({'warehouse_requisition_process_id':active_ids and active_ids[0]})
        return res
    
    @api.multi
    def reject_requisition(self):
        if self.requisition_process_id:
            return self.requisition_process_id.reject_requisition_with_reason(self.reason)
        return
    
    @api.multi
    def warehouse_requisition(self):
        if self.warehouse_requisition_process_id:
            return self.warehouse_requisition_process_id.reject_warehouse_requisition_with_reason(self.reason)
        return
