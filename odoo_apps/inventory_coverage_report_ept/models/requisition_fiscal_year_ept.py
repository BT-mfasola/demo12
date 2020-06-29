from odoo import models, api, fields, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError

class RequisitionFiscalYear(models.Model):
    _name = "requisition.fiscal.year.ept"
    _description = "Reorder Year"
    _order = "date_start, id"
    
    name = fields.Char(string='Year', required=True, copy=False)
    code = fields.Char(string='Code' , size=7, required=True, copy=False)
    date_start = fields.Date(string='Start Date', required=True)
    date_stop = fields.Date(string='End Date', required=True)
    
    state = fields.Selection([('draft', 'Open'), ('done', 'Closed')], string='States', readonly=True, copy=False, default="draft")    
    
    requisition_period_ids = fields.One2many('requisition.period.ept', 'fiscalyear_id')
    
    @api.multi
    @api.constrains('date_start', 'date_stop')
    def _check_duration(self):
        for fiscal_year_obj in self:
            if fiscal_year_obj.date_stop < fiscal_year_obj.date_start:
                raise ValidationError("The start date of a fiscal year must precede its end date.")

    @api.multi
    def create_periods(self):
        interval = 1
        period_obj = self.env['requisition.period.ept']
        for fiscal_year in self:
            ds = datetime.strptime(str(fiscal_year.date_start), '%Y-%m-%d')

            while ds.strftime('%Y-%m-%d') < str(fiscal_year.date_stop):
                de = ds + relativedelta(months=interval, days=-1)
                if de.strftime('%Y-%m-%d') > str(fiscal_year.date_stop):
                    de = datetime.strptime(fiscal_year.date_stop, '%Y-%m-%d')
                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%b%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fiscal_year.id,
                })
                ds = ds + relativedelta(months=interval)
        return True
            
            
