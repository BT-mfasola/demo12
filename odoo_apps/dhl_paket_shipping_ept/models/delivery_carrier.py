# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
import binascii
import requests
from requests.auth import HTTPBasicAuth
import time
from odoo import models, fields, api, _
from odoo.addons.dhl_paket_shipping_ept.dhl_api.dhl_response import Response
import xml.etree.ElementTree as etree
from odoo.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[('dhl_de_ept', 'DHL DE')])
    delivery_type_dhl_packet_ept = fields.Selection(
        [('fixed_ept', 'DHL DE Fixed Price'), ('base_on_rule_ept', 'DHL DE Based on Rules')], string='DHL DE Pricing',
        default='fixed_ept')
    services_name = fields.Selection([("V01PAK", "V01PAK-DHL PAKET"),
                                      ("V06PAK", "V06PAK-DHL PAKET the same day"),
                                      ("V53WPAK", "V53WPAK-DHL PAKET International"),
                                      ("V54EPAK", "V54EPAK-DHL Europaket"),
                                      ("V06WZ", "V06WZ-Courier desired time"),
                                      ("V06TG", "V06TG-Courier the same day"),
                                      ("V86PARCEL", "V86PARCEL-DHL PAKET Austria"),
                                      ("V87PARCEL", "V87PARCEL-DHL PAKET Connect"),
                                      ("V82PARCEL", "V82PARCEL-DHL PAKET International")], string="Product Name",
                                     help="Shipping Services those are accepted by DHL.")
    #   use_advance_services=fields.Boolean("Use advance services?",default=False,help="Use advance services than set value true.")
    #   shipment_handling=fields.Boolean("Use shipment handling tag ?",default=False,help="Shipment handling use for service V06TG:Courier Same day and V06WZ:Courier desired time.")
    #   shipment_endorsement=fields.Boolean("Endorsement",default=False,help="Service endorsement is used to specify handling if recipient not met.")
    shipment_endorsement_type = fields.Selection([("SOZU", "SOZU-Return immediately(For Germany)"),
                                                  ("ZWZU", "ZWZU-2nd attempt of Delivery(For Germany)"),
                                                  ("IMMEDIATE",
                                                   "IMMEDIATE-Sending back immediately to sender(For International)"),
                                                  ("AFTER_DEADLINE",
                                                   "AFTER_DEADLINE-Sending back immediately to sender after expiration of time(For International)"),
                                                  ("ABANDONMENT",
                                                   "ABANDONMENT-Abandonment of parcel at the hands of sender (free of charge and For International)")],
                                                 string="Endorsement Type",
                                                 help="Service endorsement is used to specify handling if recipient not met.Use for service V06TG:Courier Same day and V06WZ:Courier desired time.")
    shipment_handling_type = fields.Selection([("a", "a-Remove content,return box"),
                                               ("b", "b-Remove content, pick up and dispose cardboard packaging"),
                                               ("c", "c-Handover parcel/box to customer"),
                                               ("d", "d-Remove bag from of cooling unit and handover to customer"),
                                               ("e", "e-Remove content, apply return label und seal box, return box")],
                                              string="Shipment Handling Type",
                                              help="Shipment handling use for service V06TG:Courier Same day and V06WZ:Courier desired time.")
    shipment_is_out_of_country = fields.Boolean("Shipment Is Out Of Country?", default=False,
                                                help="If shipment is out of country than set true.")
    export_type = fields.Selection([("OTHER", "OTHER"),
                                    ("PRESENT", "PRESENT"),
                                    ("COMMERCIAL_SAMPLE", "COMMERCIAL_SAMPLE"),
                                    ("DOCUMENT", "DOCUMENT"),
                                    ("RETURN_OF_GOODS", "RETURN_OF_GOODS")], string="Export Type",
                                   help="Depends on chosen product only mandatory for international and non EU shipments.")
    exclude_country_groups = fields.Many2many('res.country.group', string="Exclude Country Group",
                                              help="Selected countries are not consider export document.")
    terms_of_trade = fields.Selection([("DDP", "DDP-Delivery Duty Paid"),
                                       ("DXV", "DXV-Delivery duty paid (excl. VAT )"),
                                       ("DDU", "DDU-Delivery Duty Paid"),
                                       ("DDX", "Delivery duty paid (excl. Duties, taxes and VAT)")],
                                      string="Terms Of Trade", help="Element provides terms of trades.")
    dhl_ekp_no = fields.Char(help="The EKP number sent to you by DHL and it must be maximum 10 digit allow.",
                             readonly=True, compute='_compute_dhl_ekp_no')
    dhl_procedure_no = fields.Char(
        help="The procedure refers to DHL products that are used for shipping and max length is 2 digit.")
    dhl_participation_no = fields.Char(
        help="participation number referred to as Partner ID in the web service.The participation is 2 numerical digits from 00 to 99 or alphanumerical digits from AA to ZZ.")

    @api.multi
    def _compute_dhl_ekp_no(self):
        '''added by Emipro Technologies Pvt Ltd'''
        for delivery_carrier in self:
            shipping_instance_id = delivery_carrier.shipping_instance_id or False
            if shipping_instance_id:
                delivery_carrier.dhl_ekp_no = shipping_instance_id.dhl_ekp_no or ''
            else:
                delivery_carrier.dhl_ekp_no = ''

    @api.onchange("delivery_type")
    def onchange_delivery_type(self):
        '''added by Emipro Technologies Pvt Ltd'''
        if self.delivery_type != 'dhl_de_ept':
            self.delivery_type_dhl_packet_ept = ''
        else:
            self.delivery_type_dhl_packet_ept = 'fixed_ept'

    def dhl_de_ept_rate_shipment(self, order):
        '''added by Emipro Technologies Pvt Ltd'''
        if self.delivery_type_dhl_packet_ept == 'fixed_ept':
            return self.fixed_rate_shipment(order)
        if self.delivery_type_dhl_packet_ept == 'base_on_rule_ept':
            return self.base_on_rule_rate_shipment(order)

    @api.onchange("services_name")
    def onchange_services_name(self):
        """ Set the participation number in DHL delivery method.
            @param 
            @return: Set the value of Participation number using the delivery type. 
            @author: Jigar v Vagadiya on dated 11-July-2017.
        """
        if self.services_name:
            procedure_number = str(self.services_name[1]) + str(self.services_name[2])
            self.dhl_procedure_no = procedure_number

    @api.onchange("shipping_instance_id")
    def onchange_shipping_instance(self):
        """When Create manully method in delivery carrier set the Ekp number automatically.
            @param
            @return: set ekp number for delivery method.
            @author: Jigar Vagadiya on dated 24-Aug-2017.
        """
        self.dhl_ekp_no = self.shipping_instance_id.dhl_ekp_no

    @api.multi
    def get_url(self):
        """ Set the URL using for DHL method
            @param 
            @return: Deside the URL(final data pass in to DHL).
            @author: Jigar v Vagadiya on dated 11-July-2017.
        """
        if not self.prod_environment:
            url = "https://cig.dhl.de/services/sandbox/soap"
        else:
            url = "https://cig.dhl.de/services/production/soap"
        return url

    def api_attribute_formater(self,picking,to_address,total_weight,pack=False,shipment_order_node=False):
        """ Generate the Lable of perticular shipping service for DHL
           @param : Picking Detail, TO Address, Weight of package,  packagename, API parent Node
           @return: Lable(final data pass in to DHL).
           @author: Jigar V Vagadiya - Emipro Technologies Pvt Ltd
        """
        res_country_group = self.env['res.country.group']
        picking_company_id = picking.picking_type_id and picking.picking_type_id.warehouse_id and picking.picking_type_id.warehouse_id.partner_id
        shipment_order = etree.SubElement(shipment_order_node,"ShipmentOrder")
        etree.SubElement(shipment_order, "sequenceNumber").text = "01"

        shipment = etree.SubElement(shipment_order, "Shipment")

        shipment_details = etree.SubElement(shipment, "ShipmentDetails")
        etree.SubElement(shipment_details, "product").text = str(self.services_name)

        account_number = self.dhl_ekp_no + self.dhl_procedure_no + self.dhl_participation_no

        etree.SubElement(shipment_details, "cis:accountNumber").text = str(account_number)

        etree.SubElement(shipment_details, "shipmentDate").text = time.strftime("%Y-%m-%d")
        shipment_item = etree.SubElement(shipment_details, "ShipmentItem")

        # if single_pack:
        #     etree.SubElement(shipment_item, "weightInKG").text = str(picking.weight)
        # else:

        if total_weight < 31 and total_weight > 0:
            etree.SubElement(shipment_item, "weightInKG").text = str(total_weight)
        else:
            raise Warning(_("%s Weight is to high, Maximum weight is allow 70 pound.") % pack if pack == 1 else pack.name)
            # This condition is true when use for service V06TG:Courier Same day and V06WZ:Courier desired time.
        if self.services_name in ['V06PAK', 'V06WZ', 'V06TG']:
            #Must Consider One things in this: This time consider UTC time.
            # Time formate like 18002000 this formate.
            current_hour = time.strftime('%H')
            time_frame = ""
            current_hour = int(current_hour)
            if current_hour >= 10 and current_hour < 12:
                time_frame = "10001200"
            elif current_hour >= 12 and current_hour < 14:
                time_frame = "12001400"
            elif current_hour >= 14 and current_hour < 16:
                time_frame = "14001600"
            elif current_hour >= 16 and current_hour < 18:
                time_frame = "16001800"
            elif current_hour >= 18 and current_hour < 20:
                time_frame = "18002000"
            elif current_hour >= 20 and current_hour < 21:
                time_frame = "19002100"
            service_info = etree.SubElement(shipment_details, "Service")

            preferred_time = etree.SubElement(service_info, "PreferredTime")
            preferred_time.attrib['active'] = "1"
            preferred_time.attrib['type'] = str(time_frame)

            day_of_delivery = etree.SubElement(service_info, "DayOfDelivery")
            day_of_delivery.attrib['active'] = "1"
            day_of_delivery.attrib['details'] =time.strftime("%Y-%m-%d")

            delivery_time_frame = etree.SubElement(service_info, "DeliveryTimeframe")
            delivery_time_frame.attrib['active'] = "1"
            delivery_time_frame.attrib['details'] = str(time_frame)

            shipment_handling = etree.SubElement(service_info, "ShipmentHandling")
            shipment_handling.attrib['active'] = "1"
            shipment_handling.attrib['type'] = self.shipment_handling_type

            delivery_time_frame = etree.SubElement(service_info, "Endorsement")
            delivery_time_frame.attrib['active'] = "1"
            delivery_time_frame.attrib['type'] = self.shipment_endorsement_type

        shipper_info = etree.SubElement(shipment, "Shipper")
        shipper_name = etree.SubElement(shipper_info, "Name")
        etree.SubElement(shipper_name, "cis:name1").text = str(picking_company_id.name)

        address_detail = etree.SubElement(shipper_info, "Address")
        etree.SubElement(address_detail, "cis:streetName").text = str(picking_company_id.street)
        etree.SubElement(address_detail, "cis:streetNumber").text = str(
            picking_company_id.street_no if picking_company_id.street_no else "")
        etree.SubElement(address_detail, "cis:addressAddition").text = str(
            picking_company_id.street2 if picking_company_id.street2 else "")
        etree.SubElement(address_detail, "cis:zip").text = str(picking_company_id.zip)
        etree.SubElement(address_detail, "cis:city").text = str(picking_company_id.city)
        origin_node = etree.SubElement(address_detail, "cis:Origin")
        etree.SubElement(origin_node, "cis:country").text = ""
        etree.SubElement(origin_node, "cis:countryISOCode").text = str(picking_company_id.country_id and picking_company_id.country_id.code or "")
        communication_node = etree.SubElement(shipper_info, "Communication")
        if picking_company_id.phone:
            etree.SubElement(communication_node, "cis:phone").text = str(picking_company_id.phone)
        
        if to_address:
            receiver_info = etree.SubElement(shipment, "Receiver")
            etree.SubElement(receiver_info, "cis:name1").text = str(to_address.name1)
            communication = etree.SubElement(receiver_info, "Communication")
            if to_address.res_phone:
                etree.SubElement(communication, "cis:phone").text = str(to_address.res_phone)
            if to_address.res_email:
                etree.SubElement(communication, "cis:email").text = str(to_address.res_email)
            address_info = etree.SubElement(receiver_info, "Address")
            
            if (to_address.name2 and to_address.dhl_recipient_add_method == 'dhl_street'):
                etree.SubElement(address_info, "cis:name2").text = str(to_address.name2 )
            if to_address.name3 :
                etree.SubElement(address_info, "cis:name3").text = str(to_address.name3 or "")
                etree.SubElement(address_info, "cis:streetName").text = str(to_address.street )
                etree.SubElement(address_info, "cis:streetNumber").text = str(to_address.street_no or "")
                etree.SubElement(address_info, "cis:zip").text = str(to_address.zip )
                etree.SubElement(address_info, "cis:city").text = str(to_address.city)
                origin = etree.SubElement(address_info, "cis:Origin")
                etree.SubElement(origin, "cis:country").text = ""
                etree.SubElement(origin, "cis:countryISOCode").text = str(to_address.country_id and to_address.country_id.code)
            
            if to_address.dhl_recipient_add_method == 'dhl_packstation':
            
                packstation_detail = etree.SubElement(receiver_info, "Packstation")
                etree.SubElement(packstation_detail, "cis:postNumber").text = str(to_address.post_no)
                if to_address.prefix in to_address.street_no:
                    pack_no = to_address.street_no
                    pack_no = pack_no.replace(to_address.prefix, "")
                    pack_no = pack_no.replace(" ", "")
                    etree.SubElement(packstation_detail, "cis:packstationNumber").text = str(
                        pack_no if pack_no else "")
            
           
                else:
                    etree.SubElement(packstation_detail, "cis:packstationNumber").text = str(to_address.street_no or "")
                etree.SubElement(packstation_detail, "cis:zip").text = str(to_address.zip )
                etree.SubElement(packstation_detail, "cis:city").text = str(to_address.city)
                packstation_origin = etree.SubElement(packstation_detail, "cis:Origin")
                etree.SubElement(packstation_origin, "cis:country").text = ""
                etree.SubElement(packstation_origin, "cis:countryISOCode").text = str(
                    (to_address.country_id and to_address.country_id.code))
            
            
            if to_address.dhl_recipient_add_method == 'dhl_filiale' or picking.batch_id.dhl_recipient_add_method=='dhl_filiale':
                postfiliale_detail = etree.SubElement(receiver_info, "Postfiliale")
            
                if to_address.prefix in to_address.street_no:
                    postfiliale_no = to_address.street_no
                    postfiliale_no = postfiliale_no.replace(to_address.prefix, "")
                    postfiliale_no = postfiliale_no.replace(" ", "")
                    etree.SubElement(postfiliale_detail, "cis:postfilialNumber").text = str(
                    postfiliale_no if postfiliale_no else "")
                else:
                    etree.SubElement(postfiliale_detail, "cis:postfilialNumber").text = str(to_address.street_no or "")
            
                etree.SubElement(postfiliale_detail, "cis:postNumber").text = str(to_address.post_no )
                etree.SubElement(postfiliale_detail, "cis:zip").text = str(to_address.zip )
                etree.SubElement(postfiliale_detail, "cis:city").text = str(to_address.city)
                postfiliale_origin = etree.SubElement(postfiliale_detail, "cis:Origin")
                etree.SubElement(postfiliale_origin, "cis:country").text = ""
                etree.SubElement(postfiliale_origin, "cis:countryISOCode").text = str((to_address.country_id and to_address.country_id.code)or "")
            
            if to_address.dhl_recipient_add_method == 'dhl_parcelshop' or picking.batch_id.dhl_recipient_add_method=='dhl_parcelshop':
                parcelshop_detail = etree.SubElement(receiver_info, "ParcelShop")
            
                if to_address.prefix in to_address.street_no:
                    parcelshop_no = to_address.street_no
                    parcelshop_no = parcelshop_no.replace(to_address.prefix, "")
                    parcelshop_no = parcelshop_no.replace(" ", "")
                    etree.SubElement(parcelshop_detail, "cis:parcelShopNumber").text = str(
                        parcelshop_no if parcelshop_no else "")
                else:
                    etree.SubElement(parcelshop_detail, "cis:parcelShopNumber").text = str(to_address.street_no or "")
            
                etree.SubElement(parcelshop_detail, "cis:zip").text = str(to_address.zip)
                etree.SubElement(parcelshop_detail, "cis:city").text = str(to_address.city )
                parcelshop_origin = etree.SubElement(parcelshop_detail, "cis:Origin")
                etree.SubElement(parcelshop_origin, "cis:country").text = ""
                etree.SubElement(parcelshop_origin, "cis:countryISOCode").text = str((to_address.country_id and to_address.country_id.code) or "")
        else:
            if picking.picking_type_id:
                pp=picking.partner_id
                receiver_info = etree.SubElement(shipment, "Receiver")
                etree.SubElement(receiver_info, "cis:name1").text = str(pp.name)
                communication = etree.SubElement(receiver_info, "Communication")
                if pp.phone:
                    etree.SubElement(communication, "cis:phone").text = str( pp.phone)
                if pp.email:
                    etree.SubElement(communication, "cis:email").text = str(pp.email)
                address_info = etree.SubElement(receiver_info, "Address")
            
                if pp.street2 and picking.batch_id.dhl_recipient_add_method=='dhl_street':
                    etree.SubElement(address_info, "cis:name2").text = str(pp.street2)
                if pp.street_no:
                    etree.SubElement(address_info, "cis:name3").text = str(pp.street_no or "")
                etree.SubElement(address_info, "cis:streetName").text = str(pp.street)
                etree.SubElement(address_info, "cis:streetNumber").text = str(pp.street or "")
                etree.SubElement(address_info, "cis:zip").text = str(pp.zip)
                etree.SubElement(address_info, "cis:city").text = str(pp.city)
                origin = etree.SubElement(address_info, "cis:Origin")
                etree.SubElement(origin, "cis:country").text = ""
                etree.SubElement(origin, "cis:countryISOCode").text = str(pp.country_id and pp.country_id.code)
            
                if picking.batch_id.dhl_recipient_add_method=='dhl_packstation':
            
                    packstation_detail = etree.SubElement(receiver_info, "Packstation")
                    etree.SubElement(packstation_detail, "cis:postNumber").text = str(pp.street)
                    if self.shipping_instance_id.dhl_packstation_prefix in pp.street_no:
                        pack_no = pp.street_no
                        pack_no = pack_no.replace(self.shipping_instance_id.dhl_packstation_prefix, "")
                        pack_no = pack_no.replace(" ", "")
                        etree.SubElement(packstation_detail, "cis:packstationNumber").text = str(
                        pack_no if pack_no else "")
                    else:
                        etree.SubElement(packstation_detail, "cis:packstationNumber").text = str(pp.street_no or "")
                    etree.SubElement(packstation_detail, "cis:zip").text = str(pp.zip)
                    etree.SubElement(packstation_detail, "cis:city").text = str(pp.city)
                    packstation_origin = etree.SubElement(packstation_detail, "cis:Origin")
                    etree.SubElement(packstation_origin, "cis:country").text = ""
                    etree.SubElement(packstation_origin, "cis:countryISOCode").text = str(pp.country_id and pp.country_id.code)
            
            
                if picking.batch_id.dhl_recipient_add_method=='dhl_filiale':
                    postfiliale_detail = etree.SubElement(receiver_info, "Postfiliale")
                
                    if self.shipping_instance_id.dhl_packstation_prefix in pp.street_no:
                        pack_no = pp.street_no
                        pack_no = pack_no.replace(self.shipping_instance_id.dhl_packstation_prefix, "")
                        pack_no = pack_no.replace(" ", "")
                        etree.SubElement(packstation_detail, "cis:postfilialNumber").text = str(
                            pack_no if pack_no else "")
                    else:
                        etree.SubElement(postfiliale_detail, "cis:postfilialNumber").text = str(pp.street_no or "")
            
                    etree.SubElement(postfiliale_detail, "cis:postNumber").text = str(pp.street_no)
                    etree.SubElement(postfiliale_detail, "cis:zip").text = str(pp.zip)
                    etree.SubElement(postfiliale_detail, "cis:city").text = str(pp.city)
                    postfiliale_origin = etree.SubElement(postfiliale_detail, "cis:Origin")
                    etree.SubElement(postfiliale_origin, "cis:country").text = ""
                    etree.SubElement(postfiliale_origin, "cis:countryISOCode").text = str((pp.country_id and pp.country_id.code) or "")
            
                if picking.batch_id.dhl_recipient_add_method=='dhl_parcelshop':
                    parcelshop_detail = etree.SubElement(receiver_info, "ParcelShop")
                    if self.shipping_instance_id.dhl_packstation_prefix in pp.street_no:
                        pack_no = pp.street_no
                        pack_no = pack_no.replace(self.shipping_instance_id.dhl_packstation_prefix, "")
                        pack_no = pack_no.replace(" ", "")
                        etree.SubElement(packstation_detail, "cis:parcelShopNumber").text = str(pack_no if pack_no else "")
                    else:
                        etree.SubElement(parcelshop_detail, "cis:parcelShopNumber").text = str(pp.street_no or "")
            
                    etree.SubElement(parcelshop_detail, "cis:zip").text = str(pp.zip)
                    etree.SubElement(parcelshop_detail, "cis:city").text = str(pp.city)
                    parcelshop_origin = etree.SubElement(parcelshop_detail, "cis:Origin")
                    etree.SubElement(parcelshop_origin, "cis:country").text = ""
                    etree.SubElement(parcelshop_origin, "cis:countryISOCode").text = str((pp.country_id and pp.country_id.code) or "")

        if self.shipment_is_out_of_country:
            matched_country_group = False
            for country_group in self.exclude_country_groups:
                if  to_address:
                    matched_country_group = res_country_group.search([('id', '=', country_group.id), (
                    'country_ids', 'in', (to_address.country_id and to_address.country_id.ids) or [])])
                else:
                    matched_country_group = res_country_group.search([('id', '=', country_group.id), (
                    'country_ids', 'in', (pp.country_id and pp.country_id.ids) or [])])
                    
                if matched_country_group:
                    break
            if not matched_country_group:
                export_document_detail = etree.SubElement(shipment, "ExportDocument")
                etree.SubElement(export_document_detail, "invoiceNumber").text = str(picking.name)
                etree.SubElement(export_document_detail, "exportType").text = str(self.export_type)
                if  to_address:
                    etree.SubElement(export_document_detail, "exportTypeDescription").text = str(
                    to_address.note if to_address.note else "")
                else:
                    etree.SubElement(export_document_detail, "exportTypeDescription").text =  ""
                    
                etree.SubElement(export_document_detail, "termsOfTrade").text = str(self.terms_of_trade)
                for line in picking.move_lines:
                    if pack == 1 or pack == line.move_line_ids.result_package_id:
                        product_weight=self.convert_weight(picking.weight_uom_id, self.weight_uom_id,line.product_id.weight)
                        export_doc_position = etree.SubElement(export_document_detail, "ExportDocPosition")
                        etree.SubElement(export_doc_position, "description").text = str(
                            line.product_id.name)
                        etree.SubElement(export_doc_position, "countryCodeOrigin").text = str(
                            picking_company_id.country_id and picking_company_id.country_id.code)
                        etree.SubElement(export_doc_position, "amount").text = str(int(line.product_qty))
                        etree.SubElement(export_doc_position, "netWeightInKG").text = str(
                            product_weight)
                        etree.SubElement(export_doc_position, "customsValue").text = str(line.product_id.lst_price if line.product_id.lst_price else 0.0)

        etree.SubElement(shipment_order, "labelResponseType").text = "B64"
        return etree.tostring(shipment_order)



    @api.model
    def dhl_de_ept_send_shipping(self, pickings):
        """ Generate the Lable of perticular shipping service for DHL
            @param :picking Detail
            @return: Lable(final data pass in to DHL).
            @author: Emipro Technologies Pvt Ltd
        """
        response = []
        res_country_group = self.env['res.country.group']
        context = self._context
        to_address = context.get('WizardSendToShip_id', False)
        for picking in pickings:
            self.check_instance_state()
            self.check_appropriate_data(picking)
            url = self.get_url()
            total_bulk_weight = self.convert_weight(picking.weight_uom_id, self.weight_uom_id,picking.weight_bulk)
            root_node = etree.Element("soapenv:Envelope")
            root_node.attrib['xmlns:soapenv'] = "http://schemas.xmlsoap.org/soap/envelope/"
            root_node.attrib['xmlns:cis'] = "http://dhl.de/webservice/cisbase"
            root_node.attrib['xmlns:bus'] = "http://dhl.de/webservices/businesscustomershipping"

            header_node = etree.SubElement(root_node, "soapenv:Header")
            authentification_node = etree.SubElement(header_node, "cis:Authentification")
            etree.SubElement(authentification_node, "cis:user").text = str(
                self.shipping_instance_id.userid)
            etree.SubElement(authentification_node, "cis:signature").text = str(
                self.shipping_instance_id.password)

            shipment_body_node = etree.SubElement(root_node, "soapenv:Body")
            shipment_order_node = etree.SubElement(shipment_body_node, "bus:CreateShipmentOrderRequest")
            version_node = etree.SubElement(shipment_order_node, "bus:Version")
            etree.SubElement(version_node, "majorRelease").text = ""
            etree.SubElement(version_node, "minorRelease").text = ""

            for package in picking.package_ids:
                product_weight = self.convert_weight(picking.weight_uom_id, self.weight_uom_id,package.shipping_weight)
                self.api_attribute_formater(picking,to_address,product_weight,package,shipment_order_node)

            if total_bulk_weight:
                self.api_attribute_formater(picking,to_address,total_bulk_weight,1,shipment_order_node)

            headers = {"Content-Type": "application/soap+xml;charset=UTF-8",
                       "SOAPAction": "urn:createShipmentOrder",
                       'Content-Length': str(len(etree.tostring(root_node))), }
            try:
                _logger.info("DHL Request URL : %s\n DHL Request Header: %s\n DHL Request Data : %s "%(url,headers,etree.tostring(root_node)))
                result = requests.post(url=url, data=etree.tostring(root_node), headers=headers,
                                       auth=HTTPBasicAuth(str(self.shipping_instance_id.http_userid),
                                                          str(self.shipping_instance_id.http_password)))
            except Exception as e:
                raise Warning(_(e))
            if result.status_code != 200:
                error = "Error Code : %s - %s" % (result.status_code, result.reason)
                raise Warning(_(error))
            # Todo : For Domestic shipment Multiple package is supported and For International shipment need to varify. - jigarv
            api = Response(result)
            result = api.dict()
            self.check_error_in_response(result)
            final_tracking_no = []
            label_data = result.get('Envelope', {}).get('Body', {}).get('CreateShipmentOrderResponse', {})
            if label_data:
                _logger.info("DHL Response Data : %s"%(result))
                if isinstance(label_data, dict):
                    label_data = [label_data]
                for detail in label_data:
                    creation_detail = detail.get('CreationState', {})
                    if isinstance(creation_detail, dict):
                        creation_detail = [creation_detail]
                    for cdetail in creation_detail:
                        tracking_no = cdetail.get('LabelData', {}).get('shipmentNumber')

                        binary_data = cdetail.get('LabelData', {}).get('labelData')

                        exportlabeldata = cdetail.get('LabelData', {}).get('exportLabelData')

                        label_binary_data = binascii.a2b_base64(str(binary_data))

                        message_ept = (
                                _("Shipment created!<br/> <b>Shipment Tracking Number : </b>%s") % (tracking_no))

                        if exportlabeldata:
                            exportbinarydata = binascii.a2b_base64(str(exportlabeldata))
                            picking.message_post(body=message_ept, attachments=[
                                ('DHL Label-%s.%s' % (tracking_no, "pdf"), label_binary_data),
                                ('DHL ExportLabel -%s.%s' % (tracking_no, "pdf"), exportbinarydata)])
                        else:
                            picking.message_post(body=message_ept, attachments=[
                                ('DHL Label-%s.%s' % (tracking_no, "pdf"), label_binary_data)])

                        final_tracking_no.append(tracking_no)

            shipping_data = {
                'exact_price': picking.sale_id and picking.sale_id.delivery_price or 0.0,
                'tracking_number':  ",".join(final_tracking_no)}
            response += [shipping_data]
        return response
     

    @api.multi
    def check_error_in_response(self, response):
        """ Genrate the dynamic error in DHL response when error response is occure.
            @param Reponse Detail
            @return: Dynamic Error when error want to genrate.
            @author: Jigar v Vagadiya on dated 14-July-2017.
        """
        fault_res = response.get('Envelope', {}).get('Body', {}).get('Fault', {})
        if fault_res:
            response_code = fault_res.get('faultcode')
            status_message = fault_res.get('faultstring')
            error = "Error Code : %s - %s" % (response_code, status_message)
            if response_code != "0":
                raise Warning(_(error))
        else:
            response_detail = response.get('Envelope', {}).get('Body', {}).get('CreateShipmentOrderResponse', {})
            response_code = response_detail.get('Status', {}).get('statusCode')
            status_message = response_detail.get('Status', {}).get('statusMessage')

            if isinstance(response_detail, dict):
                response_detail = [response_detail]
            for detail in response_detail:
                creation_detail = detail.get('CreationState', {})
                if creation_detail:
                    if isinstance(creation_detail, dict):
                        creation_detail = [creation_detail]
                    for cdetail in creation_detail:
                        custom_status_message = cdetail.get('LabelData', {}).get('Status', {}).get('statusMessage')
                        status_code = cdetail.get('LabelData', {}).get('Status', {}).get('statusCode')
                        error = "Error Code : %s - %s" % (status_code, custom_status_message)
                        if status_code != "0":
                            raise Warning(_(error))
            error = "Error Code : %s - %s" % (response_code, status_message)
            if response_code != "0":
                raise Warning(_(error))
        return True

    @api.multi
    def check_instance_state(self):
        '''Check the instance and method are active or not.
            @param :None
            @return:Generate the warning instance and method are active or not.
            @author:Jigar v Vagadiya on dated 17-July-2017.
        '''
        if self.shipping_instance_id.active != True:
            raise Warning(_("Shipping instance inactive !"))
        if self.active != True:
            raise Warning(_("Delivery method inactive !"))

    @api.multi
    def check_appropriate_data(self, picking):
        """ When data is incorrect genrate the error and check data is appropriate or not.
            @param : picking
            @return: Incorrect data than error want to genrate.
            @author: Jigar v Vagadiya on dated 17-July-2017.
        """
        for picking_id in picking.move_lines:
            if picking_id.product_id.weight == 0:
                error = "Enter the product weight : %s " % (picking_id.product_id.name)
                raise Warning(_(error))

        missing_value = self.validating_address(picking.partner_id)
        if missing_value:
            fields = ", ".join(missing_value)
            raise Warning(_("Missing the values of the Customer address. \n Missing field(s) : %s  ") % fields)

        #       validation shipper address
        missing_value = self.validating_address(picking.picking_type_id.warehouse_id.partner_id)
        if missing_value:
            fields = ", ".join(missing_value)
            raise Warning(_("Missing the values of the Warehouse address. \n Missing field(s) : %s  ") % fields)

        return True

    @api.multi
    def validating_address(self, partner, additional_fields=[]):
        """ Check the Address when validate the sale order
            @param : address information
            @return: Check the sale order address .
            @author: Jigar v Vagadiya
        """
        missing_value = []
        mandatory_fields = ['country_id', 'city', 'zip']
        mandatory_fields.extend(additional_fields)
        if not partner.street and not partner.street2:
            mandatory_fields.append('street')
        for field in mandatory_fields:
            if not getattr(partner, field):
                missing_value.append(field)
        return missing_value

    @api.multi
    def dhl_de_ept_get_tracking_link(self, pickings):
        """ Tracking the shipment from DHL
            @param:
            @return: Redirect from DHL site
            @author: Jigar v vagadiya
        """
        res = ""
        for picking in pickings:
            link = self.shipping_instance_id and self.shipping_instance_id.tracking_link or "https://nolp.dhl.de/nextt-online-public/en/search?piececode="
            tracking_no_lists = str(picking.carrier_tracking_ref)
            tracking = tracking_no_lists.replace(',', '%3B+')
            res = res + '%s %s' % (link, tracking)
        return res
        #https://nolp.dhl.de/nextt-online-public/en/search?piececode=222201010014766451+%3B+222201010014766468+%3B+222201010014766475

    @api.multi
    def dhl_de_ept_cancel_shipment(self, pickings):
        """ Cancel the shipment order when click on cancel button.
            @param 
            @return: Cancel the shipment request.
            @author: Jigar v Vagadiya on 21-july-2017.
        """
        for picking in pickings:
            url = self.get_url()
            root_node = etree.Element("soapenv:Envelope")
            root_node.attrib['xmlns:soapenv'] = "http://schemas.xmlsoap.org/soap/envelope/"
            root_node.attrib['xmlns:cis'] = "http://dhl.de/webservice/cisbase"
            root_node.attrib['xmlns:bus'] = "http://dhl.de/webservices/businesscustomershipping"

            header_node = etree.SubElement(root_node, "soapenv:Header")
            authentification_node = etree.SubElement(header_node, "cis:Authentification")
            etree.SubElement(authentification_node, "cis:user").text = str(self.shipping_instance_id.userid)
            etree.SubElement(authentification_node, "cis:signature").text = str(
                self.shipping_instance_id.password)

            shipment_body_node = etree.SubElement(root_node, "soapenv:Body")
            shipment_order_node = etree.SubElement(shipment_body_node, "bus:DeleteShipmentOrderRequest")
            version_node = etree.SubElement(shipment_order_node, "bus:Version")
            etree.SubElement(version_node, "majorRelease").text = ""
            etree.SubElement(version_node, "minorRelease").text = ""

            tracking_no_lists = str(picking.carrier_tracking_ref)

            tracking_nos = tracking_no_lists.split(',')
            for tracking_no in tracking_nos:
                if tracking_no:
                    etree.SubElement(shipment_order_node, "cis:shipmentNumber").text = str(tracking_no)

            headers = {"Content-Type": "application/soap+xml;charset=UTF-8", "SOAPAction": "urn:createShipmentOrder",
                       'Content-Length': str(len(etree.tostring(root_node))), }

            try:
                result = requests.post(url=url, data=etree.tostring(root_node), headers=headers,
                                       auth=HTTPBasicAuth(str(self.shipping_instance_id.http_userid),
                                                          str(self.shipping_instance_id.http_password)))
            except Exception as e:
                raise Warning(_(e))

            if result.status_code != 200:
                error = "Error Code : %s - %s" % (result.status_code, result.reason)
                raise Warning(_(error))
            api = Response(result)
            result = api.dict()

            fault_res = result.get('Envelope', {}).get('Body', {}).get('Fault', {})
            if fault_res:
                response_code = fault_res.get('faultcode')
                status_message = fault_res.get('faultstring')
                error = "Error Code : %s - %s" % (response_code, status_message)
                if response_code != "0":
                    raise Warning(_(error))

            check_data = result.get('Envelope', {}).get('Body', {}).get('DeleteShipmentOrderResponse', {})

            response_code = check_data.get('Status', {}).get('statusCode')
            status_message = check_data.get('Status', {}).get('statusMessage', {})
            error_msg = check_data.get('Status', {}).get('statusText')

            response_detail = result.get('Envelope', {}).get('Body', {}).get('DeleteShipmentOrderResponse', {})
            if isinstance(response_detail, dict):
                response_detail = [response_detail]
            for detail in response_detail:
                creation_detail = detail.get('DeletionState', {})
                if isinstance(creation_detail, dict):
                    creation_detail = [creation_detail]
                for cdetail in creation_detail:
                    status = cdetail.get('Status', {})
                    status_code = status.get('statusCode', {})
                    status_message = cdetail.get('shipmentNumber')
                    message = (_("Shipment cancelled : %s ") % (status_message))
                    msg = "Error : %s" % (result)
                    if status_code != "0":
                        raise Warning(_(msg))
                    picking.message_post(body=message)

            error = "Error Code : %s - %s - %s" % (response_code, status_message, error_msg)
            if response_code != "0":
                raise Warning(_(error))