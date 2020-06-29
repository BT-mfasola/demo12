# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Devintelle Software Solutions (<http://devintellecs.com>).
#
##############################################################################

from odoo import models, fields, api, _

from odoo.exceptions import ValidationError

class dev_export_fields(models.Model):
    _name = 'dev.export.fields'
    
    _order = 'sequence, id'
    
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Many2one('ir.model.fields', 'Name', required="1")
    label = fields.Char('Label')
    ref_field =fields.Many2one('ir.model.fields', 'Relation Field')
    model_id = fields.Many2one('ir.model',string="model")
    export_id = fields.Many2one('dev.export',string='Export')
    
    
    @api.onchange('name')
    def change_name(self):
        if self.name:
            self.label = self.name.field_description
            if self.name.ttype == 'many2one':
                model_pool= self.env['ir.model']
                model_ids = model_pool.search([('model','=',self.name.relation)],limit=1)
                self.model_id = model_ids.id
            
#    @api.onchange('ref_field')
#    def change_ref_field(self):
#        if self.ref_field:
#            self.label = self.ref_field.field_description

class dev_relational_field(models.Model):
    _name = 'dev.relational.field'
    
    _order = 'sequence, id'
    
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Many2one('ir.model.fields', 'Name')
    label = fields.Char('Label')
    ref_field =fields.Many2one('ir.model.fields', 'Relation Field')
    model_id = fields.Many2one('ir.model',string="model")
    export_id = fields.Many2one('dev.export',string='Export')
    
    @api.onchange('name')
    def change_name(self):
        if self.name:
            self.label = self.name.field_description
            if self.name.ttype == 'many2one':
                model_pool= self.env['ir.model']
                model_ids = model_pool.search([('model','=',self.name.relation)],limit=1)
                self.model_id = model_ids.id
            
#    @api.onchange('ref_field')
#    def change_ref_field(self):
#        if self.ref_field:
#            self.label = self.ref_field.field_description
    

  
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
