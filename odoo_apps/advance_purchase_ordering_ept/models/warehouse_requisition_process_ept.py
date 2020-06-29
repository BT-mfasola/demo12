from odoo import fields, models, api, _
from datetime import timedelta
import datetime
from odoo.exceptions import UserError, Warning
import math

_state_tuple = [('draft', 'Draft'),
                ('generated', 'Calculated'),
                ('waiting', 'Waiting For Approval'),
                ('approved', 'Approved'),
                ('rejected', 'Rejected'),
                ('verified', 'Verified'),
                ('done', 'Done'),
                ('cancel', 'Cancelled')]
from odoo.addons.advance_purchase_ordering_ept.models.requisition_process_ept import _deliver_to_type 

class WarehouseRequisitionProcess(models.Model):
    _name = 'warehouse.requisition.process.ept'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Procurement Process"    
    _order = "requisition_date desc, id desc"
    
    
      
    def _compute_approval_buttons(self):
        for record in self :
            if record.is_approval_by_authorised :
                if record.state == 'waiting' : 
                    if record.approval_user_id.id == self._uid :
                        show_approval_buttons = True
                    else : 
                        show_approval_buttons = False
                else :
                    show_approval_buttons = False
            else :
                show_approval_buttons = False
                
            record.show_approval_buttons = show_approval_buttons
            
    
    def _compute_is_approved_by_authorised(self):
        for record in self :
            record.is_approval_by_authorised = eval(self.env['ir.config_parameter'].sudo().get_param('advance_purchase_ordering_ept.approval_by_authorised', False))
    
    
    
    @api.model
    def get_default_approval_by_authorised(self):
        return eval(self.env['ir.config_parameter'].sudo().get_param('advance_purchase_ordering_ept.approval_by_authorised'))
    
    def default_is_use_forecast_sale_for_requisition(self):
        return eval(self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.use_forecasted_sales_for_requisition'))
        
    @api.model
    def get_default_date(self):
        return datetime.datetime.now().strftime("%Y-%m-%d")
    
    @api.multi
    def _set_purchase_order_count(self):
        for reorder in self:
            reorder.purchase_order_count = len(reorder.purchase_ids)
    
    @api.multi
    def _set_sale_order_count(self):
        for reorder in self:
            reorder.sale_order_count = len(reorder.sale_ids)
            
    @api.multi
    def _set_account_invoice_count(self):  
        for reorder in self:
            invoice_ids = self.env['account.invoice'].search([('intercompany_transfer_id', 'in', reorder.ict_ids.ids), ('type', 'in', ['out_invoice', 'out_refund'])])
            reorder.account_invoice_count = len(invoice_ids)
    
    @api.multi        
    def _set_supplier_invoice_count(self):
        for reorder in self:
            invoice_ids = self.env['account.invoice'].search([('intercompany_transfer_id', 'in', reorder.ict_ids.ids), ('intercompany_transfer_id', '!=', False), ('type', 'in', ['in_invoice', 'in_refund'])])
            reorder.supplier_invoice_count = len(invoice_ids)
    
    @api.multi
    def _set_ict_count(self):
        for reorder in self:
            reorder.ict_count = len(reorder.ict_ids)
            
    @api.multi
    def _set_picking_count(self):
        for reorder in self:
            picking_ids = self.env['stock.picking'].search([('intercompany_transfer_id', 'in', reorder.ict_ids.ids), ('intercompany_transfer_id', '!=', False)])
            reorder.picking_count = len(picking_ids)   
            
    @api.model
    def get_default_past_sale_start_from(self):
        start_date = fields.Date.context_today(self)
        start_date_obj = str(start_date)
        return start_date_obj 
    
    
    name = fields.Char(string='Name', index=True, copy=False, default=lambda self: _('New'))
    
    show_approval_buttons = fields.Boolean(compute=_compute_approval_buttons)
    is_approval_by_authorised = fields.Boolean("Approval By Authorised", default=get_default_approval_by_authorised, copy=False)
    
    
    ict_count = fields.Integer(string='ICT Count', compute=_set_ict_count)
    sale_order_count = fields.Integer(string='Sale Order Count', compute=_set_sale_order_count)
    purchase_order_count = fields.Integer(string='Purchase Order Count', compute=_set_purchase_order_count)
    picking_count = fields.Integer(string='Picking Count', compute=_set_picking_count)
    account_invoice_count = fields.Integer(string='Account Invoice Count', compute=_set_account_invoice_count)
    is_use_forecast_sale_for_requisition = fields.Boolean("Use Forecast sale", default=default_is_use_forecast_sale_for_requisition, copy=False)
    supplier_invoice_count = fields.Integer(string='Supplier Invoice Count', compute=_set_supplier_invoice_count)
    
    
    requisition_date = fields.Date(string='Date', index=True, default=get_default_date)
    requisition_past_sale_start_from = fields.Date(string='Past Sales Start From', default=get_default_past_sale_start_from)
    
    reject_reason = fields.Text("Reject Reason")
    
    state = fields.Selection(_state_tuple, string='Status', default='draft', required=True, index=True, copy=False)
    deliver_to = fields.Selection(_deliver_to_type, string="Deliver To", default="general")
    
    
    user_id = fields.Many2one('res.users', string='Responsible User ', index=True, default=lambda self:self.env.uid)
    source_warehouse_id = fields.Many2one('stock.warehouse', string='Source Warehouse', index=True)
    approval_user_id = fields.Many2one('res.users', 'Authorised User', domain=lambda self:[('groups_id', '=', self.env.ref('advance_purchase_ordering_ept.group_approve_purchase_requisition_ept').id)])
    product_id = fields.Many2one(string="Requisition Process Products", related="warehouse_requisition_process_line_ids.product_id")
    warehouse_id = fields.Many2one(string="Warehouse", related="warehouse_configuration_line_ids.warehouse_id")
    
    
    warehouse_configuration_line_ids = fields.One2many('warehouse.requisition.configuration.line.ept', 'warehouse_requisition_process_id', string='Procurement Process Planning', copy=False)
    warehouse_requisition_process_line_ids = fields.One2many('warehouse.requisition.process.line.ept', 'warehouse_requisition_process_id', string='Warehouse Process Lines')
    warehouse_requisition_summary_ids = fields.One2many('warehouse.requisition.summary.line.ept', 'warehouse_requisition_process_id', string='Procurement Summary', copy=False)
    ict_ids = fields.One2many('inter.company.transfer.ept', 'warehouse_requisition_process_id', string='Inter Company Transactions')
    sale_ids = fields.One2many('sale.order', 'warehouse_requisition_process_id', string='Sales Order')
    purchase_ids = fields.One2many('purchase.order', 'warehouse_requisition_process_id', string='Purchase Order')
    picking_ids = fields.One2many('stock.picking', 'warehouse_requisition_process_id', string='Picking Lists')
    invoice_ids = fields.One2many('account.invoice', 'warehouse_requisition_process_id', string='Invoices')
   
   
    product_ids = fields.Many2many('product.product', string='Products')
    
    
   
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            sequence_id = self.env.ref('advance_purchase_ordering_ept.sequence_warehouse_requisition_process_ept').ids
            if sequence_id:
                record_name = self.env['ir.sequence'].browse(sequence_id).next_by_id()
            else:
                record_name = 'New'   
            vals['name'] = record_name
        return super(WarehouseRequisitionProcess, self).create(vals)
   
    
    @api.multi
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_so_as_sent'):
            mark_waiting = self._context.get('mark_requisition_as_waiting', False)
            mark_rejected = self._context.get('mark_requisition_as_rejected', False)
            order = self.browse([self._context['default_res_id']])
            if order.state == 'generated' and mark_waiting :
                order.state = 'waiting'
            if order.state == 'waiting' and mark_rejected :
                order.state = 'rejected'
                order.reject_reason = self._context.get('reject_reason', '')
        return super(WarehouseRequisitionProcess, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)
    

    
   
    @api.model
    def domain_warehouse_id_for_general_requisition(self):
        """
        This method will be used if wants to set domain in configuration line warehouse 
        """
        return []
    
    @api.model
    def domain_destination_warehouse_for_general_requisition(self):
        """
        This method will be used if wants to set domain in configuration line destionation warehouse 
        """
        return []
    
    @api.model
    def domain_source_warehouse_for_general_requisition(self):
        """
        This method will be used if wants to set domain in Source warehouse 
        """
        return []
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(WarehouseRequisitionProcess, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form' : 
            if self._context.get('default_deliver_to') == 'general':
                warehouse_domain = self.domain_warehouse_id_for_general_requisition()
                if warehouse_domain : 
                    res['fields']['warehouse_configuration_line_ids']['views']['tree']['fields']['warehouse_id']['domain'] = warehouse_domain
                dest_warehouse_domain = self.domain_destination_warehouse_for_general_requisition()
                if dest_warehouse_domain :
                    res['fields']['warehouse_configuration_line_ids']['views']['tree']['fields']['destination_warehouse_id']['domain'] = dest_warehouse_domain
            source_domain = self.domain_source_warehouse_for_general_requisition()
            if source_domain : 
                res['fields']['source_warehouse_id']['domain'] = source_domain
        return res
    
    
    
    api.multi
    def action_cancel(self):        
        return self.write({'state':'cancel'})

    @api.multi
    def action_draft(self):
        line_ids = self.mapped('warehouse_requisition_process_line_ids')
        line_ids and line_ids.sudo().unlink()
        is_approve_by_authorized = self.get_default_approval_by_authorised()
        is_use_forecast_sale_for_requisition = self.default_is_use_forecast_sale_for_requisition()
        summary_line_ids = self.mapped('warehouse_requisition_summary_ids')
        summary_line_ids and summary_line_ids.sudo().unlink()
        return self.write({'state':'draft', 'is_approval_by_authorised':is_approve_by_authorized, 'is_use_forecast_sale_for_requisition':is_use_forecast_sale_for_requisition})
    
    
    
    @api.multi
    def unlink(self):
        for reorder in self:
            if reorder and reorder.state == 'done':
                raise Warning("You can not delete transaction, if it is in Done state !!")
        res = super(WarehouseRequisitionProcess, self).unlink()
        return res
    
    
    
    
    @api.multi
    def view_requisition_demand_in_detail(self):
        self.ensure_one()
        view_id = self.env.ref('advance_purchase_ordering_ept.export_requisition_demand_form_view').id
        context = {'is_default_requisition_process_id':self.id}
        res = {
            'name':'View Demand Calculation',
            'view_type':'form',
            'view_mode':'tree',
            'views' : [(view_id, 'form')],
            'res_model':'export.requistion.demand.ept',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'view_id':'view_id.id',
            'target':'new',
            'context':context,
        }
        return res
    
    
    
    @api.multi
    def get_pending_moves(self, warehouse, product_ids=[]):
        product_ids = product_ids and product_ids or self.product_ids and self.product_ids.ids or []
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        locations = self.env['stock.location'].search([('location_id','child_of',warehouse.view_location_id.id),('usage', '=', 'internal')])
        domain = [('date_expected', '<', current_date), ('state', '=', 'assigned'),
                  ('location_dest_id', 'in', locations and locations.ids or []),
                  ('product_id', 'in', product_ids)]
        moves = self.env['stock.move'].search(domain, order='date_expected')
        pickings = []
        for move in moves:
            if not move.picking_id in pickings:
                pickings.append(move.picking_id)
        return pickings
    
    
    @api.multi
    def action_confirm(self):
        line_obj = self.env['warehouse.requisition.process.line.ept']
        for warehouse_requisition in self :
            if not warehouse_requisition.product_ids :
                raise UserError(_("Please add some products!!!"))
            if not warehouse_requisition.warehouse_configuration_line_ids:
                raise UserError(_("Please select  Warehouse!!!!"))
        for warehouse_config_line in self.mapped('warehouse_configuration_line_ids'):
            pickings = self.get_pending_moves(warehouse_config_line.warehouse_id)
            if pickings:
                msg = """
                    You cannot confirm that process, because some pickings need to be rescheduled.!!! \n
                """
                for picking in pickings:
                    msg += " Picking => %s / Source Document => %s \n" % (picking.name, picking.origin and picking.origin or " ")
                raise UserError(_(msg))
        
        if self.is_use_forecast_sale_for_requisition:
            list_of_period_ids = []
            warehouse_ids = []
            product_ids = self.product_ids.ids
            product_ids_str = '(' + str(product_ids or [0]).strip('[]') + ')'
            total_time = 0 
            for config_line in self.mapped('warehouse_configuration_line_ids'):
                warehouse_id = config_line.warehouse_id
                warehouse_ids.append(warehouse_id.id)
                total_time = config_line.requisition_estimated_delivery_time + config_line.requisition_backup_stock_days
                total = datetime.datetime.strptime(str(self.requisition_date), '%Y-%m-%d').date() + timedelta(days=int(total_time))
                requisition_period_ids = self.env['requisition.period.ept'].search([('date_start', '<=', total), ('date_stop', '>=', self.requisition_date)])
                for period_id in requisition_period_ids:
                    if period_id.id not in list_of_period_ids:
                        list_of_period_ids.append(period_id.id)
            
            period_ids_str = '(' + str(list_of_period_ids or [0]).strip('[]') + ')'
            warehouse_ids_str = '(' + str(warehouse_ids or [0]).strip('[]') + ')'
            not_found_lines = []
            not_found_query = """
                    Select 
                        product.id as product_id, 
                        warehouse.id as warehouse_id,
                        period.id as period_id
                    From 
                        product_product product, stock_warehouse warehouse, requisition_period_ept period
                    Where 
                        product.id in %s And 
                        warehouse.id in %s And 
                        period.id in %s
                    
                    Except
                    
                    Select 
                        product_id, 
                        warehouse_id, 
                        period_id
                    from forecast_sale_ept
                    Where 
                        product_id in %s And 
                        warehouse_id in %s And 
                        period_id in %s
                        
                """ % (str(product_ids_str), str(warehouse_ids_str), str(period_ids_str) , str(product_ids_str), str(warehouse_ids_str), str(period_ids_str))
            self._cr.execute(not_found_query)
            res_dict = self._cr.dictfetchall()
            if res_dict:
                for record in res_dict:
                    not_found_lines.append((0, 0, record))
            if not_found_lines:
                vals = {
                        'warehouse_requisition_process_id' : self.id,
                        'mismatch_lines' : not_found_lines,
                        'warehouse_ids' : [(6, 0, warehouse_ids)]
                        }
                context = vals.copy()
                mismatch = self.env['mismatch.data.ept'].with_context(context).create(vals)
                if mismatch:
                    return mismatch.wizard_view()
        for product in self.product_ids:
            for warehouse_config_line in self.warehouse_configuration_line_ids:
                vals = {
                        'warehouse_requisition_process_id' : warehouse_config_line.warehouse_requisition_process_id.id,
                        'warehouse_configuraiton_line_id' : warehouse_config_line.id,
                        'product_id' : product.id,
                        'warehouse_id' : warehouse_config_line.warehouse_id.id
                       }
                
                existing_line = self.reqisition_line_can_be_created(product, warehouse_config_line)
#                 existing_line = line_obj.search([('warehouse_requisition_process_id', '=', warehouse_config_line.warehouse_requisition_process_id.id,),
#                                  ('warehouse_configuraiton_line_id', '=', warehouse_config_line.id),
#                                  ('product_id', '=', product.id),
#                                  ('warehouse_id', '=', warehouse_config_line.warehouse_id.id),
#                                  ])
                if existing_line : 
                    line_obj.create(vals)
                    
                    
                    
    @api.multi
    def reqisition_line_can_be_created(self, product_id, configuraiton_line_id): 
        warehouse_requistion_process_line_obj = self.env['warehouse.requisition.process.line.ept']   
        if self.deliver_to == 'general': 
            warehouse_requistion_process_line_id = warehouse_requistion_process_line_obj.search([('product_id', '=', product_id.id), ('warehouse_configuraiton_line_id', '=', configuraiton_line_id.id),('warehouse_requisition_process_id', '=', configuraiton_line_id.warehouse_requisition_process_id.id),('warehouse_id', '=', configuraiton_line_id.warehouse_id.id)])
            if  warehouse_requistion_process_line_id:
                 return False
            else:
                return True    
    
    def get_next_date(self, date, days=1):
        d1_obj = datetime.datetime.strptime(str(date), "%Y-%m-%d")
        d2_obj = d1_obj + datetime.timedelta(days=days)
        return d2_obj.strftime("%Y-%m-%d")
    
    
    @api.multi
    def get_live_stock(self, product):
        product_obj = self.env['product.product'].browse(product)
        outgoing_qty = product_obj.with_context({'location':self.source_warehouse_id.view_location_id.id}).outgoing_qty
        qty_available = product_obj.with_context({'location':self.source_warehouse_id.view_location_id.id}).qty_available
        return (qty_available - outgoing_qty)
    
    
    
    @api.multi
    def action_calculate(self):
        confirm = self.action_confirm()
        if confirm:
            return confirm
        for line in self.warehouse_requisition_process_line_ids:
            config_line = line.warehouse_configuraiton_line_id
            # past_sale_start_date = line.warehouse_requisition_process_id.requisition_past_sale_start_from
            
            t1_start_date = line.warehouse_requisition_process_id.requisition_date
            t1_end_date = self.get_next_date(t1_start_date, days=config_line.requisition_estimated_delivery_time - 1)
            
            t2_start_date = self.get_next_date(t1_end_date, days=1)
            t2_end_date = self.get_next_date(t2_start_date, days=config_line.requisition_backup_stock_days - 1)
            
            t1_dict = line.get_data_for_subframes(t1_start_date, t1_end_date, is_first_frame=True)
            t1_opening_closing_frames = t1_dict.get('opening_closing_frames', {})
            
            t1_sales = t2_sales = 0
            for key in t1_opening_closing_frames:
                value = t1_opening_closing_frames[key]
                t1_sales += value.get('sales', 0.0)
            
            stock_level_after_t1 = 0
            opening_stock = 0
            frame_list = t1_opening_closing_frames.keys()
            t1_last_dic_data = {}
            if frame_list:
                stock_level_after_t1 = t1_opening_closing_frames.get(max(frame_list), {}).get('closing_stock', 0.0)
                t1_last_dic_data = t1_opening_closing_frames.get(max(frame_list), {})
                opening_stock = t1_opening_closing_frames.get(min(frame_list), {}).get('opening_stock', 0.0)
            t2_forecast_sales = 0
            demand = 0
            
            t2_dict = line.get_data_for_subframes(t2_start_date, t2_end_date, is_first_frame=False, last_dic_data=t1_last_dic_data)
            t2_opening_closing_frames = t2_dict.get('opening_closing_frames', {})
            for key in t2_opening_closing_frames:
                value = t2_opening_closing_frames[key]
                    
                t2_sales += value.get('sales', 0.0)
                t2_forecast_sales += value.get('forecast_sales', 0.0)
                            
            demand = t2_sales
            
            ordered_qty = demand if demand > 0 else 0
            t1_sales = round(t1_sales, 0) if t1_sales > 0 else 0
            t2_forecast_sales = round(t2_forecast_sales, 0) if t2_forecast_sales > 0 else 0
            dict_vals = {
                        'state' : 'generated',
                        'forecasted_stock' : round(stock_level_after_t1, 0),
                        'qty_available_for_sale' : round(t1_sales, 0),
                        'expected_sale' : round(t2_forecast_sales, 0),
                        'requisition_qty' : round(ordered_qty, 0),
                        'opening_stock':round(opening_stock, 0),
                        }
            if line.can_be_update :
                dict_vals.update({'adjusted_requisition_qty':round(ordered_qty, 0), })
            line.write(dict_vals)
        self.write({'state':'generated'})
        self.generate_summary()
        return True
    
    @api.multi
    def action_re_calculate(self):
        return self.action_calculate()
    
    
    @api.multi
    def write(self, vals):
        result = super(WarehouseRequisitionProcess, self).write(vals)
        if 'warehouse_requisition_process_line_ids' in vals :
            if list(filter(lambda v : isinstance(v[2], dict) and 'adjusted_requisition_qty' in v[2], vals['warehouse_requisition_process_line_ids'])) : 
                for record in self :
                    record.generate_summary()
        return result
    
    
    @api.multi
    def generate_summary(self):
        self.ensure_one()
        res = {}
        res_dict = {}
        # wh_dict = {}
        summary_obj = self.env['warehouse.requisition.summary.line.ept']
        
        summary_data = summary_obj.search([('warehouse_requisition_process_id', 'in', self.ids)])
        if summary_data:
            summary_data.sudo().unlink()
        
        for line in self.warehouse_requisition_process_line_ids:
            if line.adjusted_requisition_qty <= 0:
                continue
            if res.get(line.product_id.id, False):
                res[line.product_id.id] = res[line.product_id.id] + line.adjusted_requisition_qty
                res_dict[line.product_id.id].append(line)                
            else:
                res[line.product_id.id] = line.adjusted_requisition_qty
                res_dict[line.product_id.id] = [line]
        
        for key, value in res.items():
            available_qty = self.get_live_stock(key)
                
            available_qty = available_qty if available_qty >= 0 else 0  
            avail_stock = available_qty if available_qty >= 0 else 0
            avail_stock = math.ceil(avail_stock)
                      
            vals = {
                    'product_id' : key,
                    'warehouse_requisition_process_id' : self.id,
                    'available_qty' : math.ceil(available_qty),
                    'requisition_qty' : value,
                    'deliver_qty' : value if avail_stock >= value else avail_stock ,
                    'is_sufficient_stock' : True if avail_stock >= value else False,
                    }
            
            summary = summary_obj.create(vals)
            for line_obj in res_dict[key]:
                line_obj.write({'warehouse_requisition_summary_id' : summary.id})

        self.generate_sharing_data()
        return True
    
    
    @api.multi
    def generate_sharing_data(self):
        warehouse_wise_product_share = self.get_product_sharing_details()
        
        for summary in self.warehouse_requisition_summary_ids:        
            if summary.requisition_qty <= 0:
                continue
            for line in summary.warehouse_requisition_process_line_ids:
                share_percent = warehouse_wise_product_share[line.warehouse_id.id].get(line.product_id.id, 0)
                line.write({'sharing_percent':share_percent})                   
        return True
    
    
    
    @api.multi
    def get_product_sharing_details(self):
        self.ensure_one()
        warehouse_wise_product_share = {}
       
        group_wise_share_qry = """
            with order_line_calc as (
            Select 
                id,  warehouse_requisition_process_id, product_id, warehouse_id, qty_available_for_sale, expected_sale, 
                (adjusted_requisition_qty::Float) as TotalSales  
            from warehouse_requisition_process_line_ept 
            where warehouse_requisition_process_id = %s and adjusted_requisition_qty > 0
            )
            
            Select 
                product_id,
                warehouse_id,
                TotalSales as ads,
                case when (select sum(TotalSales) from order_line_calc where product_id = v.product_id) <= 0 then 0 else 
                round(cast(TotalSales / (select sum(TotalSales) from order_line_calc where product_id = v.product_id) * 100 as numeric),6) end as share_group
            from order_line_calc v
        """ % (str(self.id))
        self._cr.execute(group_wise_share_qry)
        res_dict = self._cr.dictfetchall()
        for dict_data in res_dict:
            prod_dict = warehouse_wise_product_share.get(dict_data['warehouse_id'], {})
            prod_dict.update({dict_data['product_id'] : (dict_data['share_group'] or 0.0)})
            warehouse_wise_product_share.update({dict_data['warehouse_id'] : prod_dict})

        return warehouse_wise_product_share
    
    
    
    @api.multi
    def action_reject(self):
        ctx = self._context.copy()
        action = {
                'name': _('Reorder Reject Reason'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'requisition.reject.reason.ept',
                'view_id': self.env.ref('advance_purchase_ordering_ept.requisition_reject_reason_ept_form_view').id,
                'type': 'ir.actions.act_window',
                'context': ctx,
                'target': 'new'
                    }
        return action
    
    
    
    @api.multi
    def action_approve(self):
        self.warehouse_requisition_process_line_ids.write({'state' : 'approved' })
        self.write({'state':'approved'})
        return True
    
    
    
    @api.multi
    def action_update_requisition(self):
        self.write({'state':'generated'})
        return True
    
    @api.multi
    def action_verify(self):
        self.write({'state':'verified'})
        return True
    
    
    
    
    @api.multi
    def action_requisition_email_sent(self, template_id):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        template = self.env['mail.template'].browse(template_id)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='warehouse.requisition.process.ept',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            custom_layout="advance_purchase_ordering_ept.mail_template_data_notification_email_requisition",
            force_email=True
        )
        
        mark_waiting = self._context.get('mark_requisition_as_waiting', False)
        mark_rejected = self._context.get('mark_requisition_as_rejected', False)
        if mark_waiting:
            ctx.update({'mark_requisition_as_waiting':mark_waiting})
        if mark_rejected : 
            ctx.update({'mark_requisition_as_rejected':mark_rejected,
                        'reject_reason':self._context.get('reject_reason', '')
                        })
        
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
    
    
    @api.multi
    def reject_warehouse_requisition_with_reason(self, reason):
        approval_by_authorised = self.is_approval_by_authorised
        send_email = eval(self.env['ir.config_parameter'].sudo().get_param('advance_purchase_ordering_ept.requisition_send_email'))
        reject_email_template_id = self.env.ref('advance_purchase_ordering_ept.mail_template_warehouse_reqisition_reject_ept').id
        action = {}
        if approval_by_authorised and send_email:
            if not reject_email_template_id :
                raise (_("Email Template for Reject not Found !!!"))
            action = self.with_context(mark_requisition_as_rejected=True, reject_reason=reason).action_requisition_email_sent(reject_email_template_id)
        else : 
            self.write({'state':'rejected', 'reject_reason':reason})
        return action
    
    
    
     
    @api.multi
    def action_request_for_approval(self):
        self.ensure_one()
        approval_by_authorised = self.is_approval_by_authorised
        send_email = eval(self.env['ir.config_parameter'].sudo().get_param('advance_purchase_ordering_ept.requisition_send_email'))
        approve_email_template_id = self.env.ref('advance_purchase_ordering_ept.mail_template_warehouse_reqisition_approve_ept').id
        action = {}
        if approval_by_authorised and send_email:
            if not approve_email_template_id :
                raise UserError(_("Email Template for Request For Approval not Found !!!"))
            if not self.approval_user_id :
                raise UserError(_("Please set Authorised User For Procurement Process !!!."))
            action = self.with_context(mark_requisition_as_waiting=True).action_requisition_email_sent(approve_email_template_id)
        else :
            self.write({'state':'waiting'})
        return action
    
    
    
    @api.multi  
    def action_view_sale_order(self):
        form_view_id = self.env.ref('sale.view_order_form').id
        tree_view_id = self.env.ref('sale.view_order_tree').id
        resource_ids = self.sale_ids.ids 
        action = {
            'name': _('Sale Order'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'sale.order',
            'target':'current',
            'domain':"[('id','in',%s)]" % (resource_ids),
        }
        return self._open_form_tree_view(action, form_view_id, tree_view_id, resource_ids)
    
    
    
    @api.multi
    def action_view_ICT_order(self):
        form_view_id = self.env.ref('intercompany_transaction_ept.inter_company_transfer_ept_form_view').id
        tree_view_id = self.env.ref('intercompany_transaction_ept.inter_company_transfer_ept_tree_view').id
        resource_ids = self.ict_ids.ids
        action = {
            'name': _('ICT Order'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'target': 'current',
            'res_model': 'inter.company.transfer.ept',
            'domain':"[('id','in',%s)]" % (resource_ids),
        }
        return self._open_form_tree_view(action, form_view_id, tree_view_id, resource_ids)
        
    @api.multi
    def action_view_purchase_order(self):
        tree_view_id = self.env.ref('purchase.purchase_order_tree').id
        form_view_id = self.env.ref('purchase.purchase_order_form').id
        resource_ids = self.purchase_ids.ids
        action = {
            'name': _('Purchase Order'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'purchase.order',
            'target':'current',
            'domain':"[('id','in',%s)]" % (resource_ids),
        }
        return self._open_form_tree_view(action, form_view_id, tree_view_id, resource_ids)
        
    @api.multi
    def action_view_invoices(self):
        tree_view_id = self.env.ref('account.invoice_tree').id
        form_view_id = self.env.ref('account.invoice_form').id
        resource_ids = self.ict_ids.ids
        action = {
            'name': _('Customer Invoice'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'account.invoice',
            'target':'current',
            'domain':"[('intercompany_transfer_id','in',%s),('type','in',['out_invoice','out_refund'])]" % (resource_ids),
        }
        return self._open_form_tree_view(action, form_view_id, tree_view_id, resource_ids)
    
    @api.multi
    def action_view_supplier_invoices(self):
        tree_view_id = self.env.ref('account.invoice_supplier_tree').id
        form_view_id = self.env.ref('account.invoice_supplier_form').id
        resource_ids = self.ict_ids.ids
        action = {
            'name': _('Supplier Invoice'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'account.invoice',
            'target':'current',
            'domain':"[('intercompany_transfer_id','in',%s),('intercompany_transfer_id','!=',False),('type','in',['in_invoice','in_refund'])]" % (resource_ids),
        }
        return self._open_form_tree_view(action, form_view_id, tree_view_id, resource_ids)        
    
    @api.multi
    def action_view_picking(self):
        form_view_id = self.env.ref('stock.view_picking_form').id
        tree_view_id = self.env.ref('stock.vpicktree').id
        resource_ids = self.ict_ids.picking_ids.ids
        action = {
            'name':_('Pickings'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'stock.picking',
            'target':'current',
            'domain':"[('intercompany_transfer_id','in',%s),('intercompany_transfer_id','!=',False)]" % (resource_ids),
            }
        return self._open_form_tree_view(action, form_view_id, tree_view_id, resource_ids)
    
    
    
    @api.multi
    def _open_form_tree_view(self, action, form_view_id, tree_view_id, resource_ids):
        if len(resource_ids) == 1 :
            action.update({'view_id':form_view_id,
                           'res_id':resource_ids[0],
                           'view_mode': 'form'})    
        else :
            action.update({'view_id':False,
                           'view_mode': 'tree,form',
                            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')]})
                            
        return action
    
    
    
    
    @api.multi
    def action_transfer(self):
        self.ensure_one()
        ict_obj = self.env['inter.company.transfer.ept']
        dest_warehouse_wise_ict_order = {}
        
        ict_order_wise_product_qty = {}
        for summary in self.warehouse_requisition_summary_ids:
            if summary.available_qty > 0:
                for line in summary.warehouse_requisition_process_line_ids :
                    product = summary.product_id
                    if line.adjusted_requisition_qty <= 0 :
                        continue 
                    if not line.warehouse_configuraiton_line_id.is_create_intercompany_transfer():
                        continue
                                       
                    dest_warehouse_id = line.warehouse_configuraiton_line_id.destination_warehouse_id
                    avail_qty = round(summary.deliver_qty * line.sharing_percent / 100, 0)
                    ICT_order = dest_warehouse_wise_ict_order.get(dest_warehouse_id.id, '')
                    if not ICT_order:
                        order_vals = {}
                        if self.source_warehouse_id.id == dest_warehouse_id.id:
                            continue
                        if self.source_warehouse_id.company_id.id != dest_warehouse_id.company_id.id:
                            order_vals = self.prepare_ict_order_vals(line.warehouse_configuraiton_line_id, ict_type='ict')
                        else:
                            order_vals = self.prepare_ict_order_vals(line.warehouse_configuraiton_line_id, ict_type='internal')
                        if order_vals :
                            ICT_order = ict_obj.create(order_vals)
                            ICT_order.write({'price_list_id': ICT_order.destination_company_id.sudo().partner_id.sudo(ICT_order.source_company_id.intercompany_user_id.id).property_product_pricelist.id,
                                             'crm_team_id':ICT_order.destination_company_id.sudo().partner_id.sudo(ICT_order.source_company_id.intercompany_user_id.id).team_id.id})
                            dest_warehouse_wise_ict_order.update({dest_warehouse_id.id:ICT_order})
                        else :
                            continue
                    line.warehouse_configuraiton_line_id.write({'intercompany_transfer_id':ICT_order.id})
                    if ict_order_wise_product_qty.get(ICT_order, ''):
                        if product in ict_order_wise_product_qty[ICT_order]:
                            ict_order_wise_product_qty[ICT_order][product] += avail_qty
                        else :
                            ict_order_wise_product_qty[ICT_order].update({product:avail_qty})
                    else :
                        ict_order_wise_product_qty.update({ICT_order:{product:avail_qty}})
            
        # if not ict_order_wise_product_qty:
        #    return
        for ict_order in  ict_order_wise_product_qty :
            lines = []
            for product in ict_order_wise_product_qty[ict_order] :
                line_vals = self.prepare_ict_order_line_vals(ict_order, product, ict_order_wise_product_qty[ict_order][product])
                lines.append((0, 0, line_vals))
            order_vals = {'warehouse_requisition_process_id':self.id, 'intercompany_transferline_ids':lines}
            ict_order.write(order_vals)
        self.write({'state':'done'})
        return True
    
    
    
    @api.multi
    def prepare_ict_order_vals(self, warehouse_configuraiton_line, ict_type):
        self.ensure_one()
        dest_warehouse = warehouse_configuraiton_line.get_warehouse_for_ict()
        # dest_warehouse = warehouse_configuraiton_line.destination_warehouse_id
        ict_obj = self.env['inter.company.transfer.ept'].with_context(force_company=dest_warehouse.company_id.id)
        # picking_type = warehouse and warehouse.in_type_id
        
        #Take change for ticket: 03587
        new_record = ict_obj.new({'source_warehouse_id':self.source_warehouse_id.id,
                                  'source_company_id':self.source_warehouse_id.company_id.id,
                                  'destination_warehouse_id':dest_warehouse.id,
                                  'destination_company_id':dest_warehouse.company_id.id,
                                   'type':ict_type})
                                       
#         new_record.company_id = dest_warehouse.company_id
        new_record.source_warehouse_id_onchange()
#         new_record.destination_warehouse_id = dest_warehouse
        new_record.onchange_destination_warehouse_id()
        vals = new_record._convert_to_write(new_record._cache)
        return vals
    
    @api.multi
    def prepare_ict_order_line_vals(self, ict_order, product, ordered_qty):
        self.ensure_one()
        ict_order_line_obj = self.env['inter.company.transfer.line.ept']
        order_line_data = {'product_id':product.id,
                           'transfer_id':ict_order.id,
                           'quantity' :ordered_qty,
            }
        order_line = ict_order_line_obj.new(order_line_data)
        order_line.default_price_get()
        vals = order_line._convert_to_write(order_line._cache)
        return vals
    
