from odoo import models, fields, api, _

class Stock_Quant_Package(models.Model):
    _inherit = 'stock.quant.package'

    handling_instructions =fields.Selection([('BIG','Oversized'),('CRU','Fragile'),('EAT','Food'),('HWC','Handle with Care')], string = 'Handling Instructions')
    amazon_carrier_code = fields.Char("Amazon Carrier Reference")
    amazon_package_weight = fields.Float("Amazon Package Weight")
    package_type = fields.Selection([('pallet','Pallet'),('carton','Carton')],'Package Types')
    
    '''
     get package quantity necessary Custom fields. 
    '''
    
    move_line_ids_ept = fields.One2many('stock.move.line', 'result_package_id')
    current_picking_move_line_ids_ept = fields.One2many('stock.move.line', compute="_compute_current_picking_info")
    current_picking_id_ept = fields.Boolean(string="Current Picking",compute="_compute_current_picking_info")
    current_source_location_id_ept = fields.Many2one('stock.location',string="Source Location" ,compute="_compute_current_picking_info")
    current_destination_location_id_ept = fields.Many2one('stock.location', string="Destination Location",compute="_compute_current_picking_info")
    is_processed_ept = fields.Boolean(string="Is Processed",compute="_compute_current_picking_info")
    
    def _compute_current_picking_info(self):
        """ When a package is in displayed in picking, it gets the picking id trough the context, and this function
        populates the different fields used when we move entire packages in pickings.
        """
        for package in self:
            picking_id = self.env.context.get('picking_id')
            if not picking_id:
                package.current_picking_move_line_ids_ept = False
                package.current_picking_id_ept = False
                package.is_processed_ept = False
                package.current_source_location_id_ept = False
                package.current_destination_location_id_ept = False
                continue
            package.current_picking_move_line_ids_ept = package.move_line_ids_ept.filtered(lambda ml: ml.picking_id.id == picking_id)
            package.current_picking_id_ept = True
            package.current_source_location_id_ept = package.current_picking_move_line_ids_ept[:1].location_id
            package.current_destination_location_id_ept = package.current_picking_move_line_ids_ept[:1].location_dest_id
            package.is_processed_ept = not bool(package.current_picking_move_line_ids_ept.filtered(lambda ml: ml.qty_done < ml.product_uom_qty))

