from odoo import fields, models, api, _
from datetime import timedelta
import datetime
from odoo.exceptions import UserError, Warning
import logging
_logger = logging.getLogger(__name__)


_state_tuple = [('draft', 'Draft'),
                ('generated', 'Calculated'),
                ('waiting', 'Waiting For Approval'),
                ('approved', 'Approved'),
                ('rejected', 'Rejected'),
                ('verified', 'Verified'),
                ('done', 'Done'),
                ('cancel', 'Cancelled')]
                

_deliver_to_type = [('general', 'General')]


class RequisitionProcess(models.Model):
    _name = 'requisition.process.ept'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Reorder Process"
    _order = 'requisition_date desc, id desc'
    
    
    
    @api.model
    def get_default_approval_by_authorised(self):
        return eval(self.env['ir.config_parameter'].sudo().get_param('advance_purchase_ordering_ept.approval_by_authorised'))
    
    @api.model
    def get_default_date(self):
        return datetime.datetime.now().strftime("%Y-%m-%d")
    
         
    @api.multi
    def _set_purchase_order_count(self):
        for reorder in self:
            reorder.purchase_order_count = len(reorder.purchase_order_ids)
            
    @api.model
    def get_default_past_sale_start_from(self):
        start_date = fields.Date.context_today(self)
        return str(start_date)
    

    
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
    
    def default_is_use_forecast_sale_for_requisition(self):
        return eval(self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.use_forecasted_sales_for_requisition'))
        
        
        
    name = fields.Char(string='Name', index=True, copy=False, default=lambda self: _('New'))
    
    is_approval_by_authorised = fields.Boolean("Approval By Authorised", default=get_default_approval_by_authorised, copy=False)
    is_use_forecast_sale_for_requisition = fields.Boolean("Use Forecast sale For Requisition", default=default_is_use_forecast_sale_for_requisition, copy=False)
    show_approval_buttons = fields.Boolean(compute=_compute_approval_buttons)
   
    purchase_order_count = fields.Integer(string='Purchase Order Count', compute=_set_purchase_order_count)
    
    requisition_date = fields.Date(string='Date', index=True, default=get_default_date)
    requisition_past_sale_start_from = fields.Date(string='Past Sales Start From', default=get_default_past_sale_start_from)
   
    state = fields.Selection(_state_tuple, string='Status', default='draft', index=True, copy=False, track_visibility="onchange")
    deliver_to = fields.Selection(_deliver_to_type, string="Deliver To", default="general")
    
    reject_reason = fields.Text("Reject Reason")
   

    partner_id = fields.Many2one('res.partner', string='Vendor', index=True)
    user_id = fields.Many2one('res.users', string='Responsible User ', index=True, default=lambda self:self.env.uid, help="Resposible user for Reorder process")
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
    approval_user_id = fields.Many2one('res.users', 'Authorised User', domain=lambda self:[('groups_id', '=', self.env.ref('advance_purchase_ordering_ept.group_approve_purchase_requisition_ept').id)], help="Authorized user to approve/reject Reorder process ")
    warehouse_id = fields.Many2one('stock.warehouse', related='configuration_line_ids.warehouse_id', string='Warehouse')
    product_id = fields.Many2one('product.product', related='requisition_process_line_ids.product_id', string='Product')
    
    configuration_line_ids = fields.One2many('requisition.configuration.line.ept', 'requisition_process_id', string='Reorder Planning', copy=False)
    requisition_process_line_ids = fields.One2many('requisition.process.line.ept', 'requisition_process_id', string='Reorder Process Calculation')
    requisition_summary_ids = fields.One2many('requisition.summary.line.ept', 'requisition_process_id', string='Reorder Summary', copy=False)
    purchase_order_ids = fields.One2many('purchase.order', 'requisition_process_id', string='Purchase Orders')
    
    
    product_ids = fields.Many2many('product.product', string='Products')
    
    
    
    
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            sequence_id = self.env.ref('advance_purchase_ordering_ept.sequence_requisition_process').ids
            if sequence_id:
                record_name = self.env['ir.sequence'].browse(sequence_id).next_by_id()
            else:
                record_name = 'New'   
            vals['name'] = record_name
        result = super(RequisitionProcess, self).create(vals)
        return result
    
    
    
    @api.multi
    def write(self, vals):
        result = super(RequisitionProcess, self).write(vals)
        if 'requisition_process_line_ids' in vals :
            if list(filter(lambda v : isinstance(v[2], dict) and 'adjusted_requisition_qty' in v[2], vals['requisition_process_line_ids'])) : 
                for record in self :
                    record.generate_summary()
        return result 
    
    
    
    
    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        supplier_id = self.partner_id and self.partner_id.id or False
        domain = {'product_ids':  [('type', '=', 'product'), ('can_be_used_for_coverage_report_ept', '=', True)]}
        res = {'domain': domain}
        product_ids = []
        self.product_ids = [(6, 0, [])]
        if supplier_id:
            supplierinfos = self.env['product.supplierinfo'].search([('name', 'child_of', supplier_id)])
            product_ids = []
            if supplierinfos:
                for supplierinfo in supplierinfos:
                    if supplierinfo.product_tmpl_id and supplierinfo.product_tmpl_id.product_variant_ids:
                        product_ids.extend(supplierinfo.product_tmpl_id.product_variant_ids.ids)
        domain['product_ids'].append(('id', 'in', product_ids))
        return res
    
    
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
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(RequisitionProcess, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form' : 
            if self._context.get('default_deliver_to') == 'general':
                warehouse_domain = self.domain_warehouse_id_for_general_requisition()
                if warehouse_domain : 
                    res['fields']['configuration_line_ids']['views']['tree']['fields']['warehouse_id']['domain'] = warehouse_domain
                dest_warehouse_domain = self.domain_destination_warehouse_for_general_requisition()
                if dest_warehouse_domain :
                    res['fields']['configuration_line_ids']['views']['tree']['fields']['destination_warehouse_id']['domain'] = dest_warehouse_domain
        return res
    
    @api.multi
    def generate_summary(self):
        self.ensure_one()
        res = {}
        res_dict = {}
        summary_obj = self.env['requisition.summary.line.ept']
        
        summary_data = summary_obj.search([('requisition_process_id', 'in', self.ids)])
        if summary_data:
            summary_data.sudo().unlink()
        
        for line in self.requisition_process_line_ids:
            if line.adjusted_requisition_qty <= 0:
                continue
            if res.get(line.product_id.id, False):
                res[line.product_id.id] = res[line.product_id.id] + line.adjusted_requisition_qty
                res_dict[line.product_id.id].append(line)
            else:
                res[line.product_id.id] = line.adjusted_requisition_qty
                res_dict[line.product_id.id] = [line]
        
        products_min_qty = self.get_product_min_order_qty(prod_dict=res)
        
        for key in res:
            value = res[key]
            moq_qty = products_min_qty[key]           
            vals = {
                    'product_id' : key,
                    'requisition_process_id' : self.id,
                    'minimum_requisition_qty' : moq_qty,
                    'requisition_qty' : value,
                    'po_qty' : value if moq_qty < value else moq_qty ,
                    'supplier_rule_satisfied' : False if moq_qty > value else True,
                    }
            
            summary = summary_obj.create(vals)
            for line_obj in res_dict[key]:
                line_obj.write({'requisition_summary_id' : summary.id})

        self.generate_sharing_data()
        return True
    
    
    
    @api.multi
    def get_product_min_order_qty(self, prod_dict={}):
        self.ensure_one()
        products_min_qty = {}
        for product in self.product_ids:
            product_sellers = product.seller_ids.filtered(lambda s : s.name.id in  [self.partner_id.id] + self.partner_id.child_ids.ids)
            variant_sellers = product_sellers.filtered(lambda s : s.product_id and s.product_id == product)
            seller = variant_sellers and variant_sellers[0] or product_sellers and product_sellers[0]
            if not seller : 
                seller = product._select_seller(
                    partner_id=self.partner_id,
                    date=self.requisition_date and self.requisition_date[:10],
                    uom_id=False)
      
            products_min_qty[product.id] = seller.min_qty

        return products_min_qty
    
    
    
    @api.multi
    def generate_sharing_data(self):
        warehouse_wise_product_share = self.get_product_sharing_details()
        
        for summary in self.requisition_summary_ids:
            if summary.po_qty <= 0:
                continue
            for line in summary.requisition_process_line_ids:
                share_percent = warehouse_wise_product_share[line.warehouse_id.id].get(line.product_id.id, 0)
                line.write({'sharing_percent':share_percent})                   
        return True
    
    
    
    
    @api.multi
    def get_product_sharing_details(self):
        self.ensure_one()
        warehouse_wise_product_share = {}
       
        group_wise_share_qty = """
            with order_line_calc as (
            Select 
                id,  requisition_process_id, product_id, warehouse_id, qty_available_for_sale, expected_sale, 
                (adjusted_requisition_qty::Float) as TotalSales  
            from requisition_process_line_ept 
            where requisition_process_id = %s and adjusted_requisition_qty > 0
            )
            
            Select 
                product_id,
                warehouse_id,
                TotalSales as ads,
                case when (select sum(TotalSales) from order_line_calc where product_id = v.product_id) <= 0 then 0 else 
                round(cast(TotalSales / (select sum(TotalSales) from order_line_calc where product_id = v.product_id) * 100 as numeric),6) end as share_group
            from order_line_calc v
        """ % (str(self.id))
        self._cr.execute(group_wise_share_qty)
        res_dict = self._cr.dictfetchall()
        for dict_data in res_dict:
            prod_dict = warehouse_wise_product_share.get(dict_data['warehouse_id'], {})
            prod_dict.update({dict_data['product_id'] : (dict_data['share_group'] or 0.0)})
            warehouse_wise_product_share.update({dict_data['warehouse_id'] : prod_dict})

        return warehouse_wise_product_share
    
    
    
    @api.multi
    def action_calculate(self):
        confirm = self.action_confirm()
        if confirm:
            return confirm
        for line in self.requisition_process_line_ids:
            config_line = line.configuraiton_line_id
            
            # requisition_date + estimated_delivery_days -1 = estimated_delivery_days
            t1_start_date = line.requisition_process_id.requisition_date
            t1_end_date = self.get_next_date(t1_start_date, days=config_line.requisition_estimated_delivery_time - 1)
             
            t2_start_date = self.get_next_date(t1_end_date, days=1)
            t2_end_date = self.get_next_date(t2_start_date, days=config_line.requisition_backup_stock_days - 1)
            
            t1_dict = line.get_data_for_subframes(t1_start_date, t1_end_date, is_first_frame=True)
            t1_opening_closing_frames = t1_dict.get('opening_closing_frames', {})
             
            t1_sales = t2_sales = 0
            for key in t1_opening_closing_frames:
                value = t1_opening_closing_frames[key]
                t1_sales += value.get('sales', 0.0)
                 
            opening_stock = 0   
            stock_level_after_t1 = 0
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
    def action_draft(self):
        is_approval_by_authorised = self.get_default_approval_by_authorised()
        is_use_forecast_sale_for_requisition = self.default_is_use_forecast_sale_for_requisition()
        line_ids = self.mapped('requisition_process_line_ids')
        line_ids and line_ids.sudo().unlink()
        summary_line_ids = self.mapped('requisition_summary_ids')
        summary_line_ids and summary_line_ids.sudo().unlink()
        self.write({'state':'draft', 'is_approval_by_authorised':is_approval_by_authorised, 'is_use_forecast_sale_for_requisition':is_use_forecast_sale_for_requisition})
        return True
    
    
    @api.multi
    def action_cancel(self):
        return self.write({'state': 'cancel'})
    
    
    @api.multi
    def action_re_calculate(self):
        return self.action_calculate()
    
    
    
    @api.multi
    def unlink(self):
        for reorder in self:
            if reorder and reorder.state == 'done':
                raise Warning("You can not delete transaction, if it is in Done state !!")
        res = super(RequisitionProcess, self).unlink()
        return res
    
    @api.multi
    def action_confirm(self):
        line_obj = self.env['requisition.process.line.ept']
        
        for requisition_process in self :
            if not requisition_process.product_ids :
                raise UserError(_("Please add some products!!!"))
            if not requisition_process.configuration_line_ids:
                raise UserError(_("Please select  Warehouse!!!!"))
            
            requisition_process.product_ids.mapped('seller_ids').filtered(lambda s : s.name != requisition_process.partner_id)
        not_seller_product = self.product_ids - self.product_ids.filtered(lambda p : p.seller_ids.filtered(lambda s : s.name.id in [self.partner_id.id] + self.partner_id.child_ids.ids))
        if not_seller_product :
            not_seller_product_codes = not_seller_product.mapped('default_code')
            raise UserError(_("Supplier %s is not in following products : \n %s" % (self.partner_id.name, "\n\t".join(not_seller_product_codes))))
        
        for config_line in self.mapped('configuration_line_ids'):
            pickings = self.get_pending_moves(config_line.warehouse_id)
            if pickings:
                msg = """ You cannot confirm that process, because some pickings need to be rescheduled.!!! \n """
                for picking in pickings:
                    msg += " Picking => %s / Source Document => %s \n" % (picking.name, picking.origin and picking.origin or "")
                raise UserError(_(msg))
       
        # use_forecast_sale_for_requisition = self.env['ir.config_parameter'].sudo().get_param('inventory_coverage_report_ept.use_forecasted_sales_for_requisition')
        if self.is_use_forecast_sale_for_requisition:
            list_of_period_ids = []
            warehouse_ids = []
            product_ids = self.product_ids.ids
            product_ids_str = '(' + str(product_ids or [0]).strip('[]') + ')'
            total_time = 0 
            for config_line in self.mapped('configuration_line_ids'):
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
                        'requisition_process_id' : self.id,
                        'mismatch_lines' : not_found_lines,
                        'warehouse_ids' : [(6, 0, warehouse_ids)]
                        }
                context = vals.copy()
                mismatch = self.env['mismatch.data.ept'].with_context(context).create(vals)
                if mismatch:
                    return mismatch.wizard_view()     
        for product in self.product_ids:
            for config_line in self.configuration_line_ids:
                    vals = {'requisition_process_id' : config_line.requisition_process_id.id,
                            'configuraiton_line_id' : config_line.id,
                            'product_id' : product.id,
                            'warehouse_id' : config_line.warehouse_id.id,
                           }
                    
                    existing_line = self.reqisition_line_can_be_created(product, config_line)
#                     existing_line = line_obj.search([('requisition_process_id', '=', config_line.requisition_process_id.id,),
#                                      ('configuraiton_line_id', '=', config_line.id),
#                                      ('product_id', '=', product.id),
#                                      ('warehouse_id', '=', config_line.warehouse_id.id),
#                                      ])
                    if existing_line : 
                        line_obj.create(vals)
                    
                    
    @api.multi
    def reqisition_line_can_be_created(self, product_id, configuraiton_line_id): 
        reqistion_process_line_obj = self.env['requisition.process.line.ept']
        if self.deliver_to == 'general': 
            requsition_process_line_id = reqistion_process_line_obj.search([('product_id', '=', product_id.id), ('configuraiton_line_id', '=', configuraiton_line_id.id),('requisition_process_id', '=', configuraiton_line_id.requisition_process_id.id),('warehouse_id', '=', configuraiton_line_id.warehouse_id.id)])
            if  requsition_process_line_id:
                 return False
            else:
                return True    

    def get_next_date(self, date, days=1):
        d1_obj = datetime.datetime.strptime(str(date), "%Y-%m-%d")
        d2_obj = d1_obj + datetime.timedelta(days=days)
        return d2_obj.strftime("%Y-%m-%d")
    
    
    
    
      
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
    def print_requisition_process(self):
        return self.env.ref('advance_purchase_ordering_ept.action_report_requisition_process_line_ept').report_action(self)
    
 
    
    @api.multi
    def get_pending_moves(self, warehouse, product_ids=[]):
        product_ids = product_ids and product_ids or self.product_ids and self.product_ids.ids or []
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        locations = self.env['stock.location'].search([('location_id', 'child_of', warehouse.view_location_id.id), ('usage', '=', 'internal')])
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
    def action_approve(self):
        self.requisition_process_line_ids.write({'state' : 'approved' })
        self.write({'state':'approved'})
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
            default_model='requisition.process.ept',
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
                        'reject_reason':self._context.get('reject_reason', '')})
                        
        
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
    def action_request_for_approval(self):
        self.ensure_one()
        approval_by_authorised = self.is_approval_by_authorised
        send_email = eval(self.env['ir.config_parameter'].sudo().get_param('advance_purchase_ordering_ept.requisition_send_email'))
        approve_email_template_id = self.env.ref('advance_purchase_ordering_ept.mail_template_reqisition_approve_ept').id
        action = {}
        if approval_by_authorised and send_email:
            if not approve_email_template_id :
                raise UserError(_("Email Template for Request For Approval not Found !!!"))
            if not self.approval_user_id :
                raise UserError(_("Please set Authorised User For Reorder Process !!!."))
            action = self.with_context(mark_requisition_as_waiting=True).action_requisition_email_sent(approve_email_template_id)
        else :
            self.write({'state':'waiting'})
        return action
    
    
    
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
    def reject_requisition_with_reason(self, reason):
        approval_by_authorised = self.is_approval_by_authorised
        send_email = eval(self.env['ir.config_parameter'].sudo().get_param('advance_purchase_ordering_ept.requisition_send_email'))
        reject_email_template_id = self.env.ref('advance_purchase_ordering_ept.mail_template_reqisition_reject_ept').id
        action = {}
        if approval_by_authorised and send_email:
            if not reject_email_template_id :
                raise (_("Email Template for Reject not Found !!!"))
            action = self.with_context(mark_requisition_as_rejected=True, reject_reason=reason).action_requisition_email_sent(reject_email_template_id)
        else : 
            self.write({'state':'rejected', 'reject_reason':reason})
        return action
    
    @api.multi
    def action_update_requisition(self):
        self.write({'state':'generated'})
        return True
    
    
    
    @api.multi
    def prepare_po_vals(self, requisition_configuration_line):
        self.ensure_one()
        warehouse = requisition_configuration_line.get_warehouse_for_purchase_order()
        purchase_obj = self.env['purchase.order'].with_context(force_company=warehouse.company_id.id)
        picking_type = warehouse and warehouse.in_type_id
        
        new_record = purchase_obj.new({'partner_id':self.partner_id.id, 'picking_type_id':picking_type.id,
                                       'origin':self.name,
                                       'date_order':str(self.requisition_date),
                                       })
        new_record.company_id = warehouse.company_id
        new_record.onchange_partner_id()
        new_record.currency_id = requisition_configuration_line.purchase_currency_id
        new_record._compute_tax_id()
        new_record.picking_type_id = picking_type
        new_record._onchange_picking_type_id()
        vals = new_record._convert_to_write(new_record._cache)
        return vals



    @api.multi
    def prepare_po_line_vals(self, purchase_order, product, ordered_qty):
        self.ensure_one()
        purchase_order_line_obj = self.env['purchase.order.line'].with_context(force_company=purchase_order.company_id and purchase_order.company_id.id or self._uid.company_id.id, from_requisition_process=True)
        
        order_line_data = {'product_id':product.id,
                           'order_id':purchase_order.id,
                           'product_qty' :ordered_qty,
            }
        po_line = purchase_order_line_obj.new(order_line_data)
        po_line.onchange_product_id()
        po_line.product_qty = ordered_qty
        po_line._onchange_quantity()
        po_vals = po_line._convert_to_write(po_line._cache)
        price_unit = self.get_purchase_product_price(purchase_order, product, po_line)
        po_vals.update({'price_unit': price_unit})
        return po_vals

    @api.multi
    def get_purchase_product_price(self, purchase_order, product,  po_line):
        price_unit = 0.0
        suppiler_info_obj = self.env['product.supplierinfo']
        partner_id = purchase_order.partner_id
        supplier_id = partner_id and partner_id.id or False

        if partner_id:
            supplierinfos = suppiler_info_obj.search([('name', '=', partner_id.id), ('product_id', '=', product.id)],
                                                     limit=1)

        if not supplierinfos:
            supplierinfos = self.env['product.supplierinfo'].search(
                [('name', 'child_of', supplier_id), ('product_id', '=', product.id)])

        if supplierinfos:
            seller = supplierinfos[0]

        if not supplierinfos:
            supplierinfos = self.env['product.supplierinfo'].search(
                ['|', ('name', '=', partner_id.id), ('name', 'child_of', supplier_id), ('product_id', '=', False),('product_tmpl_id','=',product and product.product_tmpl_id.id)])

        if supplierinfos:
            seller = supplierinfos[0]

        if not seller:
            return

        company_id = self.company_id.id or purchase_order.company_id.id or self.env.user.company_id.id
        price_unit = self.env['account.tax']._fix_tax_included_price(seller.price, product.supplier_taxes_id.filtered(
            lambda r: r.company_id.id == company_id), po_line.taxes_id) if seller else 0.0

        if price_unit and seller and purchase_order.currency_id and seller.currency_id != purchase_order.currency_id:
            price_unit = seller.currency_id.compute(price_unit, purchase_order.currency_id)

#         if seller and product.uom_id and seller.product_uom != product.uom_id:
#             price_unit = self.env['product.uom']._compute_price(seller.product_uom.id, price_unit,
#                                                                 to_uom_id=product.uom_id.id)
            
#       Take change for ticket : 03587     
        if seller and product.uom_id and seller.product_uom != product.uom_id:
            price_unit=seller.product_uom._compute_price(price_unit,product.uom_id)

        return price_unit

    
    @api.multi
    def action_done(self):
        self.ensure_one()
        purchase_order_obj = self.env['purchase.order']
        
        dest_warehouse_wise_po = {}
        po_wise_product_qty = {}
        for summary in self.requisition_summary_ids:
            for line in summary.requisition_process_line_ids :
                product = summary.product_id
                if line.adjusted_requisition_qty <= 0 :
                    continue                    
                dest_warehouse_id = line.configuraiton_line_id.destination_warehouse_id.id
                po_qty = round(summary.po_qty * line.sharing_percent / 100, 0)
                purchase_order = dest_warehouse_wise_po.get(dest_warehouse_id)
                
                if not purchase_order :
                    po_vals = self.prepare_po_vals(line.configuraiton_line_id)
                    purchase_order = purchase_order_obj.create(po_vals)
                    dest_warehouse_wise_po.update({dest_warehouse_id:purchase_order})
            
                line.configuraiton_line_id.write({'purchase_order_id' : purchase_order.id})
                if po_wise_product_qty.get(purchase_order):
                    if product in po_wise_product_qty[purchase_order]:
                        po_wise_product_qty[purchase_order][product] += po_qty
                    else :
                        po_wise_product_qty[purchase_order].update({product:po_qty})
                else :
                    po_wise_product_qty.update({purchase_order:{product:po_qty}})
        for po in  po_wise_product_qty :
            lines = []
            for product in po_wise_product_qty[po] :
                line_vals = self.prepare_po_line_vals(po, product, po_wise_product_qty[po][product])
                lines.append((0, 0, line_vals))
            po_vals = {'requisition_process_id':self.id, 'order_line':lines}
            po.write(po_vals)
        self.write({'state':'done'})
        return True
    
    
    
        
    @api.multi
    def action_view_purchase_orders(self):
        self.ensure_one()
        tree_view_id = self.env.ref('purchase.purchase_order_tree').id
        form_view_id = self.env.ref('purchase.purchase_order_form').id
        purchase_order_ids = self.purchase_order_ids and self.purchase_order_ids.ids or []
        
        action = {'name': 'Purchase Order',
                 'type': 'ir.actions.act_window',
                  'view_type': 'form',
                  'res_model': 'purchase.order',
                  'target': 'current',
                  'context': self._context}
           
        
        if len(purchase_order_ids) == 1 :
            action.update({'view_id':form_view_id, 'res_id':purchase_order_ids[0], 'view_mode': 'form'}) 
        else :
            action.update({'view_id':False, 'view_mode': 'tree,form',
                            'views': [(tree_view_id, 'tree'), (form_view_id, 'form'), ], 'domain':"[('id','in',%s)]" % (purchase_order_ids)})
                           
        return action
    
    
    @api.model
    def update_multi_company_rule(self):
        multi_company_ir_rules = {'stock.stock_warehouse_comp_rule':'stock.group_stock_user',
                                  'stock.stock_location_comp_rule':'stock.group_stock_user',
                                  'product.product_supplierinfo_comp_rule':'base.group_user',
                                  'base.res_company_rule_public':'base.group_user',
                                  'stock.stock_picking_rule':'stock.group_stock_user',
                                  'stock.stock_move_rule':'stock.group_stock_user',
                                  'stock.stock_quant_rule':'stock.group_stock_user',
                                  'stock.stock_picking_type_rule':'stock.group_stock_user',
                                  'purchase.purchase_order_comp_rule':'purchase.group_purchase_user',
                                  'purchase.purchase_order_line_comp_rule':'purchase.group_purchase_user',
                                  'account.account_fiscal_position_comp_rule':'account.group_account_invoice',
                                  'account.tax_comp_rule':'account.group_account_invoice',
                                  'intercompany_transaction_ept.inter_company_transfer_ept_multi_company_record_rule':'intercompany_transaction_ept.intercompany_transfer_manager_group',
                                  'inventory_coverage_report_ept.rule_forecast_sale_ept_report_multi_company':'stock.group_stock_user',
                                  'inventory_coverage_report_ept.rule_forecast_and_actual_sale_report_multi_company':'stock.group_stock_user',
                                  'inventory_coverage_report_ept.rule_forecast_sale_ept_multi_company':'stock.group_stock_user',
                                  'inventory_coverage_report_ept.rule_forecast_rule_ept_multi_company':'stock.group_stock_user',
                                }
        for rule_xml_id, group_xml_id in multi_company_ir_rules.items() :
            rule = self.env.ref(rule_xml_id)
            group = self.env.ref(group_xml_id)
            if rule and group :
                if group not in rule.groups :
                    rule.write({'groups':[(4, group.id)]})

