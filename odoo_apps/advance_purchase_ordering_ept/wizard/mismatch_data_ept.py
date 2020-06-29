from odoo import models, fields, api

class MismatchData(models.TransientModel):
    _inherit = 'mismatch.data.ept'
    _description = 'Mismatch Data'

    @api.model
    def default_get(self, fields):
        context = self._context or {}
        res = super(MismatchData, self).default_get(fields)
        if context.get('requisition_process_id', False):
            res['requisition_process_id'] = context.get('requisition_process_id', False)
        if context.get('warehouse_requisition_process_id', False):
            res['warehouse_requisition_process_id'] = context.get('warehouse_requisition_process_id', False)
        res['warehouse_ids'] = context.get('warehouse_ids', [])
        lines = context.get('mismatch_lines', [])
        res['mismatch_lines'] = lines
        return res
        
    requisition_process_id = fields.Many2one('requisition.process.ept', string='Reorder Process')
    warehouse_requisition_process_id = fields.Many2one('warehouse.requisition.process.ept', string='Procurement Process')
