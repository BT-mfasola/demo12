from odoo import models,fields

class SaleReport(models.Model):
    _inherit = "sale.report"
    
    intercompany_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT", copy=False)    
    
    def _select(self):
        qry = super(SaleReport,self)._select()
        
        qry += ', s.intercompany_transfer_id as intercompany_transfer_id '
        return qry

    def _group_by(self):
        qry = super(SaleReport,self)._group_by()
        qry += ', s.intercompany_transfer_id '
        return qry