from odoo import fields, models, api
from datetime import date

class RequisitionLog(models.Model):
    _name = 'requisition.log.ept'
    _description = "Reorder Log"
    _order = 'id desc'
    
    name = fields.Char(string='Name')
    log_date = fields.Date(string='Log Date', default=date.today())
    user_id = fields.Many2one('res.users', string='Responsible', index=True, default=lambda self:self.env.uid)
    log_type = fields.Selection([('success', 'Success'), ('failure', 'Failure'),
                               ('Import_forcasted_sales', 'Import forecasted sales'),
                               ('Import_forcasted_sales_rule', 'Import forecasted sales rule'),
                               ('Export_forcasted_sales', 'Export forecasted sales')], string='Log Type')
    message = fields.Text(string='Result')
    line_ids = fields.One2many('requisition.log.line.ept', 'log_id', string='Logs')
    state = fields.Selection([ ('success', 'Succeed'), ('fail', 'Failure') ], string='Status',copy=False, readonly=True, help=" * Succeed: Process Done Successfully .\n"" * Failure: Some issue Generated while proccessing Please refer log.\n")
       
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('requisition.log.ept')
        result = super(RequisitionLog, self).create(vals)
        return result
    
    
class RequisitionLogLine(models.Model):
    _name='requisition.log.line.ept'
    _description = "Reorder Log Line"
    
    log_type=fields.Selection([('Import_forcasted_sales','Import forecasted sales'),
                               ('Export_forcasted_sales', 'Export forecasted sales'),
                               ('Import_forcasted_sales_rule','Import forcasted sales rule')],string='Log Type')
    message=fields.Text(string='Message')
    log_id=fields.Many2one('requisition.log.ept',string='Log')
    
