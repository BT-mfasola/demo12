from odoo import api, models

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'
    _description = 'Mail Message'

    @api.multi
    def send_mail(self, auto_commit=False):
        mark_waiting = self._context.get('mark_requisition_as_waiting', False)
        mark_rejected = self._context.get('mark_requisition_as_rejected', False)
        if self._context.get('default_model') == 'requisition.process.ept' and self._context.get('default_res_id') and (mark_waiting or mark_rejected):
            order = self.env['requisition.process.ept'].browse([self._context['default_res_id']])
            if order.state == 'generated' and mark_waiting :
                order.state = 'waiting'
            if order.state == 'waiting' and mark_rejected :
                order.state = 'rejected'
                order.reject_reason = self._context.get('reject_reason', '')
        elif self._context.get('default_model') == 'warehouse.requisition.process.ept' and self._context.get('default_res_id') and (mark_waiting or mark_rejected):
            order = self.env['warehouse.requisition.process.ept'].browse([self._context['default_res_id']])
            if order.state == 'generated' and mark_waiting :
                order.state = 'waiting'
            if order.state == 'waiting' and mark_rejected :
                order.state = 'rejected'
                order.reject_reason = self._context.get('reject_reason', '') 
        return super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)
