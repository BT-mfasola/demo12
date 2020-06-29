from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import datetime
from lxml import etree


class InterCompanyTransfer(models.Model):
    
    _name = 'inter.company.transfer.ept'
    _description = "Internal Company Transfer"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'barcodes.barcode_events_mixin']
    _order = 'id desc'
    
    def on_barcode_scanned(self, barcode):
        product_obj = self.env['product.product']
        intercompany_transferline_obj = self.env['inter.company.transfer.line.ept']
        
        product_id = product_obj.search(['|', ('barcode', '=', barcode), ('default_code', '=', barcode)], limit=1)
        if not product_id:
            return {'warning': {
                'title': _('Warning'),
                'message': _('Product Not Found')
                },
            }
        current_id = self._origin
        line = intercompany_transferline_obj.search([('inter_transfer_id', '=', current_id.id), ('product_id', '=', product_id.id)], limit=1)
        if line:
            line.write({'quantity':line.quantity + 1})
        else:
            intercompany_transferline_obj.create({'inter_transfer_id':current_id.id,
                                             'product_id':product_id.id,
                                            'quantity':1})
  
    
    
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()
    
    @api.depends('log_ids')
    def _compute_log_ids(self):
        for ict in self:
            ict.log_count = len(ict.log_ids)
    
    name = fields.Char('Name')
    message = fields.Char("Message", copy=False)

    state = fields.Selection([('draft', 'Draft'), ('processed', 'Processed'), ('cancel', 'Cancelled')], string='State', copy=False, default='draft')
    type = fields.Selection([('ict', 'ICT'), ('ict_reverse', 'Reverce ICT'), ('internal', 'Internal')], string='Type', readonly=True, copy=False, default='ict')
    log_count = fields.Integer(string='Inter Company Log Count', compute='_compute_log_ids')

    processed_date = fields.Datetime("Processed Date", copy=False)

    source_warehouse_id = fields.Many2one('stock.warehouse', string='From Warehouse')
    source_company_id = fields.Many2one(related='source_warehouse_id.company_id', string="Source Company")
    destination_warehouse_id = fields.Many2one('stock.warehouse', string='To Warehouse')
    destination_company_id = fields.Many2one(related='destination_warehouse_id.company_id', string="Destination Company")
    
    crm_team_id = fields.Many2one('crm.team', string="Sales Team", default=_get_default_team)
    price_list_id = fields.Many2one('product.pricelist', string="Price List")
    currency_id = fields.Many2one('res.currency', related="price_list_id.currency_id", string="Currency")
    incoming_shipment_id = fields.Many2one('stock.picking', string="Incoming Shipment", copy=False)
    group_id = fields.Many2one('procurement.group', string="Procurement Group", copy=False)
    
    intercompany_transfer_id = fields.Many2one('inter.company.transfer.ept', string="ICT")
    reverse_intercompanytransfer_ids = fields.One2many('inter.company.transfer.ept', 'intercompany_transfer_id', string="Reverse ICT")

    log_ids = fields.One2many('inter.company.transfer.log.ept', 'intercompany_transfer_id', string="Inter Company Log")

    saleorder_ids = fields.One2many('sale.order', 'intercompany_transfer_id', sring='Sale Orders', copy=False)    
    purchaseorder_ids = fields.One2many('purchase.order', 'intercompany_transfer_id', string="Purchase Order", copy=False)
    invoice_ids = fields.One2many('account.invoice', 'intercompany_transfer_id', String="Invoices", copy=False)
    picking_ids = fields.One2many('stock.picking', 'intercompany_transfer_id', string="Pickings", copy=False)
    intercompany_transferline_ids = fields.One2many('inter.company.transfer.line.ept', 'inter_transfer_id', string="Transfer Lines", copy=True)
   
    _sql_constraints = [('src_dest_company_uniq', 'CHECK(source_warehouse_id!=destination_warehouse_id)', 'Source Warehouse and Destination warehouse must be different!')]
    
    
    
    @api.model
    def create(self, vals):
        res = super(InterCompanyTransfer, self).create(vals)
        record_name = "NEW"
        if res.type == 'ict' or not res.type:
            sequence_id = self.env.ref('intercompany_transaction_ept.ir_sequence_intercompany_transaction').ids
            if sequence_id:
                record_name = self.env['ir.sequence'].browse(sequence_id).next_by_id()
            res.update({'name':record_name})
        elif res.type == 'ict_reverse':
            sequence_id = self.env.ref('intercompany_transaction_ept.ir_sequence_reverse_intercompany_transaction').ids
            if sequence_id:
                record_name = self.env['ir.sequence'].browse(sequence_id).next_by_id()
            res.update({'name':record_name})
        elif res.type == 'internal':
            sequence_id = self.env.ref('intercompany_transaction_ept.ir_sequence_internal_transfer_intercompany_transaction').ids
            if sequence_id:
                record_name = self.env['ir.sequence'].browse(sequence_id).next_by_id()
            res.update({'name':record_name})
        return res
    
    
       
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        context = self._context
        res = super(InterCompanyTransfer, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type in ['form', 'tree']:
            if context.get('type', 'ict_reverse') == 'ict_reverse':
                for node in doc.xpath("//tree[@string='Inter Company Transfer']"):
                    node.set('create', 'false')
                for node in doc.xpath("//form[@string='Inter Company Transfer']"):
                    node.set('create', 'false')
            res['arch'] = etree.tostring(doc)
        return res
    
    @api.onchange('source_warehouse_id')
    def source_warehouse_id_onchange(self):
        if not self.source_warehouse_id:
            self.destination_warehouse_id = False
            return
        if self.source_warehouse_id == self.destination_warehouse_id:
            self.destination_warehouse_id = False
        self.currency_id = self.source_company_id.currency_id
        
        res = {}
        if self.type == 'internal':
            domain = {'destination_warehouse_id':  [('company_id', '=', self.source_company_id.id), ('id', '!=', self.source_warehouse_id.id)]}
            return {'domain': domain}
        elif self.type != 'internal':
            domain = {'destination_warehouse_id':  [('company_id', '!=', self.source_company_id.id)]}
            return {'domain': domain}
        return res
    
    
    @api.onchange('destination_warehouse_id')
    def onchange_destination_warehouse_id(self):
        if not self.destination_warehouse_id:
            return False
        
        if not self.source_company_id.sudo().intercompany_user_id:
            msg = 'Please Specify Inter Company User for Source Company'
            raise Warning(msg)

        if not self.destination_company_id.sudo().intercompany_user_id:
            msg = 'Please Specify Inter Company User for Destination Company'
            raise Warning(msg)
        
        self.price_list_id = self.destination_company_id.sudo().partner_id.sudo(self.source_company_id.intercompany_user_id.id).property_product_pricelist
        self.crm_team_id = self.destination_company_id.sudo().partner_id.sudo(self.source_company_id.intercompany_user_id.id).team_id
        return 
    
    
    @api.onchange('price_list_id')
    def default_price(self):
        for record in self:
            for line in record.reverse_intercompanytransfer_ids:
                line.default_price_get()
        return
    
    @api.multi
    def action_process(self):
        invoice_obj = self.env['account.invoice']
        stock_immediate_transfer_obj = self.env['stock.immediate.transfer']
        sale_advance_paymentobj = self.env['sale.advance.payment.inv']
        
        context = self._context.copy() or {}
        for record in self:
            sale_journal = record.source_company_id.sale_journal
            purchase_journal = record.destination_company_id.purchase_journal
            if not record.with_context(context).check_user_validation():
                continue
            
           
            if not record.intercompany_transferline_ids:
                msg = "Please Add the Product to Process Transaction" 
                raise ValidationError(msg)

            sale_user_id = record.sudo().source_company_id.intercompany_user_id.id
            purchase_user_id = record.sudo().destination_company_id.intercompany_user_id.id
            purchase_partner_id = record.source_company_id.sudo().partner_id
            
            configuration_record = record.env.ref('intercompany_transaction_ept.intercompany_transaction_config_record')
    
            if  record.source_company_id == record.destination_company_id: 
                is_create_transfer = self.create_internal_transfer()
                if is_create_transfer:
                    record.write({'state':'processed', 'processed_date':datetime.today(), 'message':'ICT processed successfully by %s' % (self.env.user.name)})
                return
    
            sale_orders = record.auto_create_saleorder()
            purchase_orders = record.auto_create_purchaseorder()
            
            if configuration_record:
                if configuration_record.auto_confirm_orders:
                    for order in sale_orders:
                        order.write({'origin':record.name or ''})
                        order.sudo(sale_user_id).action_confirm()
                                
                    for order in purchase_orders:
                        order.write({'origin':record.name or ''})
                        order.sudo(purchase_user_id).button_confirm()
                    
                            
                
                if configuration_record.auto_create_invoices:
                    invoice_id = False
                    for order in sale_orders:
                        context = {"active_model": 'sale.order', "active_ids": [order.id], "active_id": order.id, 'open_invoices':True}
                        if sale_journal:
                            context.update({'default_journal_id':sale_journal.id})
                        payment_id = sale_advance_paymentobj.sudo(sale_user_id).create({'advance_payment_method': 'delivered'})
                        result = payment_id.with_context(context).sudo(sale_user_id).create_invoices()
                        result = result.get('res_id', False)
                        invoice_id = invoice_obj.sudo(sale_user_id).browse(result)
                        invoice_id.sudo(sale_user_id).write({'date_invoice':str(datetime.today()), 'intercompany_transfer_id':self.id})

                     
                    vendor_bill_id = False
                    for porder in purchase_orders:
                        context = {'default_type': 'in_invoice', 'type': 'in_invoice', 'journal_type': 'purchase', 'default_purchase_id': porder.id}
                        if purchase_journal:
                            context.update({'default_journal_id':record.destination_company_id.purchase_journal.id})
                        
                        invoice_dict = self.prepare_invoice_dict(record, purchase_partner_id, porder)
                        invoice_vals = invoice_obj.sudo(purchase_user_id).with_context(context).new(invoice_dict)
                        invoice_vals.purchase_id = porder.id
                        invoice_vals.journal_id = invoice_vals.sudo(purchase_user_id)._default_journal()
                        invoice_vals.sudo(purchase_user_id).purchase_order_change()
                        invoice_vals.sudo(purchase_user_id)._onchange_partner_id()
                        invoice_vals.date_invoice = str(datetime.today())
                        invoice_vals.sudo(purchase_user_id)._onchange_payment_term_date_invoice()
                        invoice_vals.sudo(purchase_user_id)._onchange_origin()
                        invoice_vals.currency_id = record.currency_id
                        
                        for line in invoice_vals.invoice_line_ids:
                            line.quantity = line.purchase_line_id and line.purchase_line_id.product_qty or 0.0
                            line.sudo(purchase_user_id)._compute_price()
                            
                        vendor_bill_id = invoice_obj.sudo(purchase_user_id).with_context({'type':'in_invoice'}).create(invoice_vals._convert_to_write(invoice_vals._cache))
                        vendor_bill_id.intercompany_transfer_id = self.id
                    
                    if configuration_record.auto_validate_invoices:
                        invoice_id.sudo(sale_user_id).action_invoice_open()
                        vendor_bill_id.sudo(purchase_user_id).action_invoice_open()
                        
            record.write({'state':'processed', 'processed_date':datetime.today(), 'message':'ICT processed successfully by %s' % (self.env.user.name)})
               
        return True
                
    
    @api.multi
    def check_user_validation(self):
        context = self._context or {}
        for record in self:
            if not record.source_warehouse_id.sudo().company_id.intercompany_user_id:
                msg = 'Please Specify Inter Company user for Source Company'
                if context.get('is_auto_validate', False):
                    record.write({'message':msg})
                    return False
                raise ValidationError(msg)
            
            if not record.destination_warehouse_id.sudo().company_id.intercompany_user_id:
                msg = 'Please specify intercompany user for destination company'
                if context.get('is_auto_validate', False):
                    record.write({'message':msg})
                    return False
                raise ValidationError(msg)
            
            if record.source_warehouse_id.sudo().company_id not in self.env.user.company_ids :
                if record.source_warehouse_id.sudo().company_id not in self.env.user.company_id.child_ids :
                    msg = "User '%s' can not process this Inter Company Transfer.\n User from Source Warehouse Company can Process it !!!!\n\nPlease Process it with User of Source Warehouse Company." % (self.env.user.name)
                    raise ValidationError(msg)
        return True
    
    
    @api.multi
    def create_internal_transfer(self):
        picking_obj = self.env['stock.picking']
        procurementgroup_obj = self.env['procurement.group']
        stocklocation_route_obj = self.env['stock.location.route']
        
        source_wh = self.source_warehouse_id
        dest_wh = self.destination_warehouse_id
        
        group_id = procurementgroup_obj.create({'name': self.name, 'partner_id': dest_wh.partner_id.id})
        self.group_id = group_id.id     
        route_ids = stocklocation_route_obj.search([('supplied_wh_id', '=', dest_wh.id), ('supplier_wh_id', '=', source_wh.id)])
        if not route_ids:
            raise ValidationError(_("No routes are found. \n Please configure warehouse routes and set in products."))
        if not self.intercompany_transferline_ids :
            raise ValidationError(_("No Products found. \n Please add products to transfer."))            
               
        for line in self.intercompany_transferline_ids:
            procurementgroup_obj.run(line.product_id, line.quantity, line.product_id.uom_id, dest_wh.lot_stock_id, self.name, False, values={'warehouse_id':dest_wh, 'route_ids':route_ids and route_ids[0], 'group_id':self.group_id})
            
            
        pickings = picking_obj.search([('group_id', '=', group_id.id)])
        if not pickings:
            if not group_id:
                raise Warning("Problem with creation of procurement group.")
            else:
                raise Warning("NO Pickings are created for this record.")
        for picking in pickings:
            if not picking.intercompany_transfer_id:
                picking.intercompany_transfer_id = self.id
                picking.action_assign()
            picking_id = picking.search([('location_id', '=', self.source_warehouse_id.lot_stock_id.id)])
            if picking_id:
                picking_id.action_assign()
    
        return True
    
    @api.multi
    def auto_create_saleorder(self):
        sale_obj = self.env['sale.order']
        saleline_obj = self.env['sale.order.line']
        so_list = []
        
        for record in self:
            source_company = record.source_company_id
            source_warehouse_id = record.source_warehouse_id
            intercompany_user = source_company.sudo().intercompany_user_id.id or False
            partner_id = record.destination_company_id.sudo().partner_id
            order_vals = sale_obj.sudo(intercompany_user).new({'partner_id':partner_id.id, 'warehouse_id':source_warehouse_id.id, 'pricelist_id':self.price_list_id.id})
            order_vals.sudo(intercompany_user).onchange_partner_id()
            order_vals.warehouse_id = source_warehouse_id.id
            order_vals.sudo(intercompany_user)._onchange_warehouse_id()
            order_vals.fiscal_position_id = partner_id.sudo(intercompany_user).property_account_position_id.id
            order_vals.pricelist_id = self.price_list_id.id
            if record.crm_team_id:
                order_vals.team_id = record.crm_team_id.id
            order_vals = order_vals.sudo(intercompany_user)
            sale_order = sale_obj.sudo(intercompany_user).create(order_vals._convert_to_write(order_vals._cache))
            so_lines_list = []
            for line in record.intercompany_transferline_ids:
                line_vals = saleline_obj.sudo(intercompany_user).new({'order_id':sale_order.id, 'product_id':line.product_id})
                line_vals.sudo(intercompany_user).product_id_change()
                line_vals.sudo(intercompany_user).product_uom_qty = line.quantity
                line_vals.price_unit = line.price
                line_vals = line_vals.sudo(intercompany_user)._convert_to_write(line_vals._cache)
                so_lines_list.append((0, 0, line_vals))
            sale_order.sudo(intercompany_user).write({'order_line':so_lines_list, 'intercompany_transfer_id':record.id})
            so_list.append(sale_order)
        
        return so_list
       
    
    @api.multi
    def auto_create_purchaseorder(self):
        purchase_obj = self.env['purchase.order']
        purchase_line_obj = self.env['purchase.order.line']
        po_list = []
        for record in self:
            destination_company = record.destination_company_id
            intercompany_user = destination_company.sudo().intercompany_user_id.id or False
            order_vals = purchase_obj.sudo(intercompany_user).new({'currency_id':self.currency_id.id, 'partner_id':record.source_warehouse_id.sudo().company_id.partner_id.id, 'company_id':destination_company.id})
            order_vals.sudo(intercompany_user).onchange_partner_id()
            order_vals.currency_id = self.currency_id.id
            order_vals.picking_type_id = self.destination_warehouse_id.sudo().in_type_id
            purchase_order_id = purchase_obj.sudo(intercompany_user).create(order_vals.sudo(intercompany_user)._convert_to_write(order_vals._cache))
            po_lines_list = []
            for line in record.intercompany_transferline_ids:
                line_vals = purchase_line_obj.sudo(intercompany_user).new({'order_id':purchase_order_id.id, 'product_id':line.product_id, 'currency_id':self.currency_id})
                line_vals.sudo(intercompany_user).onchange_product_id()
                line_vals.product_qty = line.quantity
                line_vals.price_unit = line.price 
                line_vals.product_uom = line.product_id.uom_id
                line_vals = line_vals.sudo(intercompany_user)._convert_to_write(line_vals._cache)
                po_lines_list.append((0, 0, line_vals))
            purchase_order_id.sudo(intercompany_user).write({'order_line':po_lines_list, 'intercompany_transfer_id':record.id})
            po_list.append(purchase_order_id)
        
        return po_list
    
    
    @api.multi
    def prepare_invoice_dict(self, record, purchase_partner_id, porder):
        vals = {'company_id': record.destination_company_id.id or False,
                'currency_id':record.currency_id,
                'partner_id':purchase_partner_id.id,
                'type': 'in_invoice',
                'journal_type': 'purchase',
                'purchase_id': porder.id}
        return vals
    
    
    @api.multi
    def action_reverse_process(self):
        stockreturn_picking_obj = self.env['stock.return.picking']
        accountinvoice_refund_obj = self.env['account.invoice.refund']
        stock_move_obj = self.env['stock.move']
        stock_picking_obj = self.env['stock.picking']
        account_invoice_obj = self.env['account.invoice']
        
        
        picking_to_stock = []
        pickings = [] 
        internal_transfer = False
        if not self.intercompany_transferline_ids:
            raise Warning("There are no products in the record!!")
        
        if not self.intercompany_transfer_id.saleorder_ids and not self.intercompany_transfer_id.purchaseorder_ids:
            pickings = self.intercompany_transfer_id.picking_ids
            if not pickings:
                raise ValidationError(_("There are no pikings available in %s " % self.intercompany_transfer_id.name))
            if not pickings.filtered(lambda pc : pc.state == 'done'):
                raise ValidationError(_("%s have some pickings which are not in done state yet!! \n Please done pickings befor reverse it. " % self.intercompany_transfer_id.name))
            internal_transfer = True
            
        if internal_transfer:
            processed = False
            for picking in pickings:
                picking_to_stock = []
                for line in self.intercompany_transferline_ids:
                    for move_id in stock_move_obj.search([('picking_id', '=', picking.id), ('product_id', '=', line.product_id.id), ('state', '=', 'done')]):
                        line_tmp = (0, 0, {'product_id': move_id.product_id.id, 'move_id': move_id.id, 'quantity': line.quantity, 'to_refund': False})
                        picking_to_stock.append(line_tmp)
                
                default_vals = stockreturn_picking_obj.with_context({'active_id':picking.id}).default_get(['move_dest_exists', 'original_location_id', 'parent_location_id', 'location_id', 'product_return_moves'])
                default_vals.update({'product_return_moves':picking_to_stock})
                return_picking = stockreturn_picking_obj.with_context({'active_ids':[]}).create(default_vals)
                new_picking_ids = return_picking.with_context({'active_id':move_id.picking_id.id}).create_returns()
                stock_picking_lst = stock_picking_obj.browse(new_picking_ids.get('res_id'))
                if stock_picking_lst:
                    for picking in stock_picking_lst:
                        picking.intercompany_transfer_id = self.id
                    processed = True
            if processed:
                self.write({'state':'processed'})
                return True
            return False
            
        if self.intercompany_transfer_id.saleorder_ids:
            for sorder in self.intercompany_transfer_id.saleorder_ids:
                pickings += sorder.picking_ids and sorder.picking_ids.filtered(lambda picking : picking.picking_type_id.code == 'outgoing')
            if not pickings:
                raise ValidationError(_("No pickings are available in sale order"))
            
        for picking in pickings:
            for line in self.intercompany_transferline_ids:
                for move_id in stock_move_obj.search([('picking_id', '=', picking.id), ('product_id', '=', line.product_id.id), ('state', '=', 'done')]):
                    line_tmp = (0, 0, {'product_id': move_id.product_id.id, 'move_id': move_id.id, 'quantity': line.quantity, 'to_refund': False})
                    picking_to_stock.append(line_tmp)
                    
            default_vals = stockreturn_picking_obj.with_context({'active_id':picking.id}).default_get(['move_dest_exists', 'original_location_id', 'parent_location_id', 'location_id', 'product_return_moves'])
            default_vals.update({'product_return_moves':picking_to_stock})
            return_picking = stockreturn_picking_obj.with_context({'active_id':picking.id}).create(default_vals)
            new_picking_id = return_picking.with_context({'active_id':picking.id}).create_returns()
            stock_picking_id = stock_picking_obj.browse(new_picking_id.get('res_id'))
            if stock_picking_id:
                stock_picking_id.intercompany_transfer_id = self.id
                
                
                
        incoming_picking_stock_lst = []
        incoming_pickings_lst = []
        if self.intercompany_transfer_id.purchaseorder_ids:
            for porder in self.intercompany_transfer_id.purchaseorder_ids:
                incoming_pickings_lst += porder.picking_ids and porder.picking_ids.filtered(lambda pck : pck.picking_type_id.code == 'incoming')
        for incoming_picking in incoming_pickings_lst:
            for line in self.intercompany_transferline_ids:
                for move_id in stock_move_obj.search([('picking_id', '=', incoming_picking.id), ('product_id', '=', line.product_id.id), ('state', '=', 'done')]):
                    line_tmp = (0, 0, {'product_id': move_id.product_id.id, 'move_id': move_id.id, 'quantity': line.quantity})
                    incoming_picking_stock_lst.append(line_tmp)
    
            default_incoming_vals = stockreturn_picking_obj.with_context({'active_id':incoming_picking.id}).default_get(['move_dest_exists', 'original_location_id', 'parent_location_id', 'location_id', 'product_return_moves'])
            default_incoming_vals.update({'product_return_moves':incoming_picking_stock_lst})
            return_picking = stockreturn_picking_obj.with_context({'active_ids':[]}).create(default_incoming_vals)
            new_picking_id = return_picking.with_context({'active_id':incoming_picking.id}).create_returns()
            stock_picking = self.env['stock.picking'].browse(new_picking_id.get('res_id'))
        
            if stock_picking:
                stock_picking.intercompany_transfer_id = self.id
        
        
        for sorder in self.intercompany_transfer_id.saleorder_ids:
            for invoice in sorder.invoice_ids.filtered(lambda inv : inv.type == 'out_invoice'):
                customer_invoice_id = invoice.search([('refund_invoice_id', '=', invoice.id)], order='id desc' , limit=1)
                default_inovoice_vals = accountinvoice_refund_obj.with_context({'active_id':invoice.id}).default_get(['filter_refund', 'description', 'date_invoice', 'date'])
                configuration_record = self.env.ref('intercompany_transaction_ept.intercompany_transaction_config_record')
                if configuration_record.filter_refund:
                    default_inovoice_vals['filter_refund'] = configuration_record.filter_refund
                default_inovoice_vals.update({'description':'%s' % (configuration_record and configuration_record.description or ('for %s' % self.name))})
                customer_refund = accountinvoice_refund_obj.with_context({'active_id':invoice.id}).create(default_inovoice_vals)
                if customer_refund.with_context({'active_ids':invoice.id}).invoice_refund():
                    invoice_id = account_invoice_obj.search([('refund_invoice_id', '=', invoice.id)], order='id desc', limit=1)
                    if invoice_id:
                        invoice_id.intercompany_transfer_id = self.id
                        for invoice_line in invoice_id.invoice_line_ids:
                            match_line = self.intercompany_transferline_ids.filtered(lambda ln : ln.product_id.id == invoice_line.product_id.id)
                            if match_line:
                                invoice_line.quantity = match_line.quantity
                        if invoice_id.state == "draft":
                            invoice_id.with_context({'active_ids':invoice.id}).action_invoice_open()
                            
                            
        for porder in self.intercompany_transfer_id.purchaseorder_ids:
            for vendor_invoice in porder.invoice_ids.filtered(lambda inv : inv.type == 'in_invoice'):
                default_inovoice_vals = accountinvoice_refund_obj.with_context({'active_id':vendor_invoice.id}).default_get(['filter_refund', 'description', 'date_invoice', 'date'])
                configuration_record = self.env.ref('intercompany_transaction_ept.intercompany_transaction_config_record')
                if configuration_record.filter_refund:
                        default_inovoice_vals['filter_refund'] = configuration_record.filter_refund
                default_inovoice_vals.update({'description':'%s' % (configuration_record and configuration_record.description or ('for %s' % self.name))})
                vendor_refund = accountinvoice_refund_obj.with_context({'active_id':vendor_invoice.id}).create(default_inovoice_vals)
                invoice_id = False
                if vendor_refund.with_context({'active_ids':vendor_invoice.id}).invoice_refund():
                    invoice_id = account_invoice_obj.search([('refund_invoice_id', '=', vendor_invoice.id)], order='id desc', limit=1)
                    if invoice_id:
                        invoice_id.intercompany_transfer_id = self.id
                        for invoice_line in invoice_id.invoice_line_ids:
                            match_line = self.intercompany_transferline_ids.filtered(lambda ln : ln.product_id.id == invoice_line.product_id.id)
                            if match_line:
                                invoice_line.quantity = match_line.quantity
                        if invoice_id.state == "draft":
                            invoice_id.with_context({'active_ids':vendor_invoice.id}).action_invoice_open()

        self.write({'state':'processed'})
        return True
    
    @api.multi
    def action_create_reverse_process(self):
        reverse_ict_line_obj = self.env['reverse.inter.company.transfer.line.ept']
        created_reverse_ids = []
        
        for line in self.intercompany_transferline_ids:
            if line.qty_delivered != 0.0:
                qty_delivered = line.qty_delivered
                if line.qty_delivered <= line.quantity:
                    inter_company_transfer_ids = self.search([('intercompany_transfer_id', '=', self.id), ('type', '=', 'ict_reverse'), ('state', '!=', 'cancel')])
                    if inter_company_transfer_ids:
                        qty_delivered = 0.0
                        total_qty_deliverd = 0.0
                        if len(inter_company_transfer_ids) > 1: 
                            for inter_company_id in inter_company_transfer_ids:
                                for transferline in inter_company_id.intercompany_transferline_ids:
                                    if transferline.product_id == line.product_id:
                                        total_qty_deliverd += transferline.quantity
                            qty_delivered = line.qty_delivered - total_qty_deliverd 
                            if qty_delivered != 0.0 and qty_delivered > 0.0:
                                created_reverse_ids.append(reverse_ict_line_obj.create({'product_id':line.product_id.id, 'quantity':qty_delivered , 'qty_delivered': qty_delivered, 'price' : line.price}).id)
                        else:
                            for already_line in inter_company_transfer_ids.intercompany_transferline_ids:
                                if already_line.product_id == line.product_id:
                                    if already_line.quantity == line.quantity:
                                        continue
                                    elif already_line.quantity < line.quantity:
                                        qty_delivered = line.qty_delivered - already_line.quantity 
                                        if qty_delivered != 0.0 and qty_delivered > 0.0:
                                            created_reverse_ids.append(reverse_ict_line_obj.create({'product_id':line.product_id.id, 'quantity':qty_delivered, 'qty_delivered': qty_delivered, 'price' : line.price}).id)
                                    else:
                                        created_reverse_ids.append(reverse_ict_line_obj.create({'product_id':line.product_id.id, 'quantity':qty_delivered , 'qty_delivered': qty_delivered, 'price' : line.price}).id)
                    else:
                        created_reverse_ids.append(reverse_ict_line_obj.create({'product_id':line.product_id.id, 'quantity':qty_delivered , 'qty_delivered': qty_delivered, 'price' : line.price}).id)      
                else:
                    continue
        if created_reverse_ids:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'reverse.inter.company.transfer.ept',
                'view_type': 'form',
                'view_mode': 'form',
                'context' : {'default_intercompany_transfer_id':self.id, 'default_reverse_intercompanyline_ids':[(6, 0, created_reverse_ids)],
                             'default_destination_warehouse':self.destination_warehouse_id and self.destination_warehouse_id.id or False},
                'target': 'new',
                
            }
        else:
            raise Warning("There are no products found for the Reverse Transaction  !!")
        
        
    @api.multi
    def action_cancel(self):
        saleorder_ids = self.saleorder_ids.filtered(lambda so : so.state == 'draft')
        puchaseorder_ids = self.purchaseorder_ids.filtered(lambda po:po.state == 'draft')
        invoice_ids = self.invoice_ids.filtered(lambda inv: inv.state == 'draft')
        picking_ids = self.picking_ids.filtered(lambda pick:pick.state == 'draft')
        if self.state == 'processed':
            if saleorder_ids and puchaseorder_ids and invoice_ids and picking_ids:
                saleorder_ids.action_cancel()
                puchaseorder_ids.action_cancel()
                invoice_ids.action_cancel()
                picking_ids.action_cancel()
                self.reset_to_draft()
            else:
              raise  Warning("You Can not Cancel Inter Company Transaction Which All Transaction State is Done")
        else:
            self.write({'state':'cancel', 'message' : 'ICT has been cancelled by %s' % (self.env.user.name) })
        
   
   
    @api.multi
    def reset_to_draft(self):
        self.ensure_one()
        self.state = 'draft'
        
        
    @api.multi
    def unlink(self):
        picking_ids = [picking.state != 'done' for picking in self.picking_ids]
        if picking_ids and self.state == 'processed':
            raise Warning("You can not delete transaction, if it is in Processed state !!")
        res = super(InterCompanyTransfer, self).unlink()
        return res
        
        
    @api.multi
    def view_sale_order(self):
        form_id = self.env.ref('sale.view_order_form').id
        tree_id = self.env.ref('sale.view_order_tree').id
        resource_ids = self.saleorder_ids and self.saleorder_ids.ids or []
        action = {
            'name': 'Sale Order',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'sale.order',
            'domain':[('id', 'in', resource_ids)]
        }
        return self._open_form_tree_view(action, form_id, tree_id, resource_ids)
    
    @api.multi
    def view_reverse_ict(self):
        form_id = self.env.ref('intercompany_transaction_ept.inter_company_transfer_ept_form_view').id
        tree_id = self.env.ref('intercompany_transaction_ept.inter_company_transfer_ept_tree_view').id 
        resource_ids = self.reverse_intercompanytransfer_ids.ids
        action = {
            'name': 'Reverse ICT',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'inter.company.transfer.ept',
            'domain':[('id', 'in', resource_ids)]
        }
        return self._open_form_tree_view(action, form_id, tree_id, resource_ids)
    
    
    @api.multi
    def view_purchase_order(self):
        form_id = self.env.ref('purchase.purchase_order_form').id
        tree_id = self.env.ref('purchase.purchase_order_tree').id 
        resource_ids = self.purchaseorder_ids and self.purchaseorder_ids.ids or []
        action = {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain':[('id', 'in', resource_ids)]
        }
        return self._open_form_tree_view(action, form_id, tree_id, resource_ids)
        
    @api.multi
    def view_pickings(self):
        form_id = self.env.ref('stock.view_picking_form').id
        tree_id = self.env.ref('stock.vpicktree').id  
        resource_ids = self.picking_ids and self.picking_ids.ids or []
        action = {
            'name':_('Pickings'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'stock.picking',
            'domain':[('id', 'in', resource_ids)]
            }
        
        return self._open_form_tree_view(action, form_id, tree_id, resource_ids)
    
    @api.multi
    def view_invoice(self):
        tree_id = self.env.ref('account.invoice_tree').id
        form_id = self.env.ref('account.invoice_form').id
        resource_ids = self.env['account.invoice'].search([('intercompany_transfer_id', '=', self.id), ('type', '=', 'out_refund')]).ids or []
        action = {
            'name': _('Customer Invoice'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'account.invoice',
            'target':'current',
            'domain':[('id', 'in', resource_ids)]
        }
        return self._open_form_tree_view(action, form_id, tree_id, resource_ids)
    
    @api.multi
    def view_vendor_bill(self):
        tree_id = self.env.ref('account.invoice_supplier_tree').id
        form_id = self.env.ref('account.invoice_supplier_form').id
        resource_ids = self.env['account.invoice'].search([('intercompany_transfer_id', '=', self.id), ('type', '=', 'in_refund')]).ids or []
        action = {
            'name': _('Vendor Bill'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'account.invoice',
            'target':'current',
            'domain':[('id', 'in', resource_ids)]
        }
        return self._open_form_tree_view(action, form_id, tree_id, resource_ids)
        
        
        
    @api.multi
    def action_view_log(self):
        tree_id = self.env.ref('intercompany_transaction_ept.inter_company_transfer_process_log_tree_view').id
        form_id = self.env.ref('intercompany_transaction_ept.inter_company_transfer_process_log_form_view').id 
        resource_ids = self.log_ids.ids
        action = {
            'name': 'ICT Log',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'inter.company.transfer.log.ept',
            'domain':[('id', 'in', resource_ids)]
        }
        return self._open_form_tree_view(action, form_id, tree_id, resource_ids)
        
        
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
        
    def import_export_product_list_view(self):
        form_id = self.env.ref('intercompany_transaction_ept.import_export_product_list_ept_form_view').id
        ctx = self._context.copy() or {}
        ctx.update({'record':self.id or False})
        return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'import.export.product.list.ept',
                'views': [(form_id, 'form')],
                'view_id': form_id,
                'target': 'new',
                'context': ctx,
                }
        
        
    
    
    
    
    
   
    
    
    
