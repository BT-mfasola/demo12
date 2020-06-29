from odoo import models, fields, api, _
from collections import defaultdict



class RequisitionProductSuggestion(models.TransientModel):
    _inherit = 'requisition.product.suggestion.ept'
    _description = 'Requistion Product Suggestion'
    
    
    @api.multi
    def create_requisition_process(self, suggestion_lines=None):
        self.ensure_one()
        requisition_obj = self.env['requisition.process.ept']
        
        lines = self.product_suggestion_line_ids
        if suggestion_lines :
            lines = suggestion_lines
        
        supplier_wise_lines = defaultdict(self.env['requisition.product.suggestion.line.ept'].browse)
        for line in lines :
            if not line.supplier_id :
                continue
            supplier_wise_lines[line.supplier_id] += line
            
        requisition_processes = requisition_obj.browse()
        
        for supplier, supplier_lines in supplier_wise_lines.items() :
            vals = self.prepare_requisition_process_vals(supplier, supplier_lines)
            requisition_process = requisition_obj.create(vals)
            config_line_vals = {}
            for line in supplier_lines :
                if line.warehouse_id not in config_line_vals :
                    vals = self.prepare_requisition_process_config_line_vals(requisition_process, line)
                    config_line_vals.update({line.warehouse_id:(0, 0, vals)})
                else :
                    continue
            requisition_process.write({'configuration_line_ids':config_line_vals.values()})
            requisition_processes += requisition_process
        action = {}
        if requisition_processes :
            tree_view_id = self.env.ref('advance_purchase_ordering_ept.requisition_process_ept_tree_view').id
            form_view_id = self.env.ref('advance_purchase_ordering_ept.requisition_process_ept_form_view').id
            requisition_process_ids = requisition_processes and requisition_processes.ids or []
            
            action = {
                'name': 'Reorder Process',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'res_model': 'requisition.process.ept',
                'target': 'current',
                'context': self._context,
                }
            
            if len(requisition_process_ids) == 1 :
                action.update({'view_id':form_view_id,
                               'res_id':requisition_process_ids[0],
                               'view_mode': 'form', })    
            else :
                action.update({'view_id':False,
                               'view_mode': 'tree,form',
                                'views': [(tree_view_id, 'tree'), (form_view_id, 'form'), ],
                               'domain':"[('id','in',%s)]" % (requisition_process_ids), })
        return action
    
    
    @api.multi
    def prepare_requisition_process_vals(self, supplier, lines):
        requisition_obj = self.env['requisition.process.ept']
        requisition_record = requisition_obj.new({
                                'partner_id':supplier,
                                'product_ids':lines.mapped('product_id'),
                            })
        requisition_record.onchange_partner_id()
        requisition_record.product_ids = lines.mapped('product_id')
        vals = requisition_record._convert_to_write(requisition_record._cache)
        return vals
    
    
    @api.multi
    def create_procurement_process(self, suggestion_lines=None):
        """ Create Procurement for recommended products which may go out of stock
            @author : Er. Vaidehi Vasani, Emipro Technologies Pvt Ltd
            @date   : 20th Nov, 2018
        """
        procurement_vals = {}
        for suggestion_line in suggestion_lines:
            if not suggestion_line.procurement_source_warehouse_id:
                continue
            if suggestion_line.procurement_source_warehouse_id in procurement_vals:
                procurement_line_detail = procurement_vals.get(suggestion_line.procurement_source_warehouse_id)
                product_ids = procurement_line_detail.get('product_ids')
                warehouse_ids = procurement_line_detail.get('warehouse_ids')
                if suggestion_line.product_id not in product_ids:
                    procurement_vals.get(suggestion_line.procurement_source_warehouse_id).get('product_ids').append(suggestion_line.product_id.id)
                if suggestion_line.warehouse_id not in warehouse_ids:
                    procurement_vals.get(suggestion_line.procurement_source_warehouse_id).get('warehouse_ids').append(suggestion_line.warehouse_id)
            else:
                procurement_vals.update({
                        suggestion_line.procurement_source_warehouse_id :
                            {
                                'product_ids' : [suggestion_line.product_id.id],
                                'warehouse_ids' : [suggestion_line.procurement_source_warehouse_id, suggestion_line.warehouse_id] 
                            }
                    })
        
        procurement_processes = self.env['warehouse.requisition.process.ept']
        for source_warehouse, line_vals in procurement_vals.items():
            procurement_id = self.env['warehouse.requisition.process.ept'].create({
                    'source_warehouse_id' : source_warehouse.id,
                    'product_ids' : [(6, 0, line_vals.get('product_ids'))]
                })
            procurement_processes += procurement_id
            for warehouse_id in line_vals.get('warehouse_ids'):
                self.env['warehouse.requisition.configuration.line.ept'].create({
                        'warehouse_requisition_process_id' : procurement_id.id,
                        'warehouse_id' : warehouse_id.id,
                        'destination_warehouse_id' : warehouse_id.id, 
                        'requisition_backup_stock_days' : self.inventory_analysis_of_x_days 
                    })
        action = {}
        if procurement_processes :
            tree_view_id = self.env.ref('advance_purchase_ordering_ept.warehouse_requisition_process_ept_tree_view').id
            form_view_id = self.env.ref('advance_purchase_ordering_ept.warehouse_requisition_process_ept_form_view').id
            procurement_process_ids = procurement_processes and procurement_processes.ids or []
            
            action = {
                'name': 'Procurement Process',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'res_model': 'warehouse.requisition.process.ept',
                'target': 'current',
                'context': self._context,
                }
            
            if len(procurement_process_ids) == 1 :
                action.update({'view_id':form_view_id,
                               'res_id':procurement_process_ids[0],
                               'view_mode': 'form', })    
            else :
                action.update({'view_id':False,
                               'view_mode': 'tree,form',
                                'views': [(tree_view_id, 'tree'), (form_view_id, 'form'), ],
                               'domain':"[('id','in',%s)]" % (procurement_process_ids), })
        return action
    
    
    
    @api.multi
    def prepare_requisition_process_config_line_vals(self, requisition_process, line):
        requisition_config_line_obj = self.env['requisition.configuration.line.ept']
        sellers = line.product_id.seller_ids.filtered(lambda seller : seller.name == requisition_process.partner_id)
        product_sellers = sellers.filtered(lambda seller : seller.product_id and seller.product_id == line.product_id)
        lead_time = sellers[0].delay
        if product_sellers :
            lead_time = product_sellers[0].delay
        requisition_record = requisition_config_line_obj.new({
                                'warehouse_id':line.warehouse_id,
                                'requisition_process_id':requisition_process,
                                'destination_warehouse_id':line.warehouse_id,
                                'requisition_estimated_delivery_time':lead_time
                            })
        requisition_record.onchange_destination_warehouse_id()
        vals = requisition_record._convert_to_write(requisition_record._cache)
        return vals
    

