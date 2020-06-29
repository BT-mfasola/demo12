from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import datetime

module_name = [('inter.company.transfer.ept', 'Inter Company Transfer')]

class InterCompanyTransferLog(models.Model):
    _name = 'inter.company.transfer.log.ept'
    _description = 'Inter company Transfer Log Process'
    
    
    name = fields.Char(string="Name")
    ict_log_date = fields.Datetime(string="Log Date")
    ict_process = fields.Selection(module_name, string="Application")
    ict_operation = fields.Selection([('import', 'Import')], string="Operation")
    intercompany_transfer_id = fields.Many2one('inter.company.transfer.ept', string="Inter company Transfer ID")
    
    ict_log_line_ids = fields.One2many('inter.company.transfer.log.line.ept', 'ict_log_id')

    def return_log_record(self, model_name, operation_type):
        sequence_id = self.env.ref('intercompany_transaction_ept.inter_company_process_log_seq').ids
        if sequence_id:
            record_name = self.env['ir.sequence'].browse(sequence_id).next_by_id()
        else:
            record_name = '/'
        log_vals = {
                'name' : record_name,
                'ict_log_date': datetime.datetime.now(),
                'ict_process':model_name._name,
                'ict_operation':operation_type,
                'intercompany_transfer_id':model_name.id
            }
        log_record = self.create(log_vals)
            
        return log_record
    
    
    @api.multi
    def post_log_line(self, message , type='error'):
        self.ensure_one()
        intercompany_transfer_logline_obj = self.env['inter.company.transfer.log.line.ept']
        log_line_vals = {
            'ict_message':message,
            'ict_log_type': type,
            'ict_log_id': self.id,
        }
        log_line_id = intercompany_transfer_logline_obj.create(log_line_vals)
        return log_line_id


class InterCompanyTransferLogLine(models.Model):
    
    _name = "inter.company.transfer.log.line.ept"
    _description = 'Inter company Transfer Log Line Process'
    _rec_name = "ict_log_id"

    ict_message = fields.Text(string="Message")
    ict_log_type = fields.Selection([('error', 'Error'), ('mismatch', 'Mismatch'), ('info', 'Info')], string="Log Type")
    ict_log_id = fields.Many2one('inter.company.transfer.log.ept', string="ICT Process Log", ondelete='cascade')
    
