from odoo import models, api, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from calendar import monthrange

class RequisitionPeriod(models.Model):
    _name = "requisition.period.ept"
    _description = "Reorder Period"
    _order = "date_start , date_stop desc"
    
    @api.multi
    def set_previous_period(self):
        for rec in self:
            d1_obj = datetime.strptime(rec.date_start, "%Y-%m-%d")
            d1_obj = d1_obj - timedelta(days=1)
            period = False
            try:
                period = self.find(dt=d1_obj.strftime("%Y-%m-%d"))
            except Exception:
                pass
            rec.previous_period_id = period and period.id or False
    
    @api.multi
    def set_next_period(self):
        for rec in self:
            d1_obj = datetime.strptime(rec.date_stop, "%Y-%m-%d")
            d1_obj = d1_obj + timedelta(days=1)
            period = False
            try:
                period = self.find(dt=d1_obj.strftime("%Y-%m-%d"))
            except Exception:
                pass
            rec.next_period_id = period and period.id or False
    
    @api.multi
    def _compute_month_days(self):
        
        for rec in self:
            d1_obj = datetime.strptime(rec.date_start, "%Y-%m-%d")
            rec.month_days = monthrange(d1_obj.year, d1_obj.month)[1] or 0
            
    @api.multi
    def set_month(self):
        for rec in self:
            d1_obj = datetime.strptime(rec.date_stop, "%Y-%m-%d")
            rec.month = d1_obj and d1_obj.month or 0

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code" , size=7, required=True)
    
    special = fields.Boolean(string='Opening/Closing Period', help="These periods can overlap.")
    state = fields.Selection([('draft', 'Open'), ('done', 'Closed')], 'states', readonly=True, copy=False, default="draft", help='When monthly periods are created. The states is \'Draft\'. At the end of monthly period it is in \'Done\' states.')
   
    date_start = fields.Date(string="Start Date", required=True, state={'done':[('readonly', True)]})
    date_stop = fields.Date(string="End Date", required=True , state={'done':[('readonly', True)]})
  
    month = fields.Integer(string="Month", compute=set_month, store=True)
    month_days = fields.Integer(string="Month Days", compute="_compute_month_days")
    
    previous_period_id = fields.Many2one('requisition.period.ept', compute=set_previous_period, string='Previous Period', index=True, store=True)
    next_period_id = fields.Many2one('requisition.period.ept', compute=set_next_period, string='Next Period', index=True, store=True)
    fiscalyear_id = fields.Many2one("requisition.fiscal.year.ept", string="Year")
    
    @api.constrains('date_stop')
    def _check_description(self):
        for period_obj in self:
            if period_obj.date_stop < period_obj.date_start:
                raise ValidationError("The duration of the Period(s) is invalid.")
            if period_obj.special:
                continue
            if period_obj.fiscalyear_id.date_stop < period_obj.date_stop or \
                period_obj.fiscalyear_id.date_stop < period_obj.date_start or \
                period_obj.fiscalyear_id.date_start > period_obj.date_start or \
                period_obj.fiscalyear_id.date_start > period_obj.date_stop:
                raise ValidationError("The period is invalid. Either some periods are overlapping or the period\'s dates are not matching the scope of the fiscal year.")
            period_objs = self.search([('date_stop', '>=', period_obj.date_start), ('date_start', '<=', period_obj.date_stop), ('special', '=', False), ('id', '<>', period_obj.id)])
            if period_objs:
                raise ValidationError("The period is invalid. Either some periods are overlapping or the period\'s dates are not matching the scope of the fiscal year.")
            return True
        
    @api.returns('self')
    def find(self, dt=None, context=None):
        if context is None:
            context = {}
        if not dt:
            return False
        args = [('date_start', '<=' , dt), ('date_stop', '>=', dt)]
        result = self.search(args , context)
        if not result:
            msg = _('There is no period defined for this date: %s.\nPlease go to Inventory/Advance Reordering/Forecast Sales/Periods to create Periods. ') % (dt) 
            raise ValidationError(msg)
        return result
        
