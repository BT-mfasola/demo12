# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name' : "Merge Delivery Orders/Incoming Shipments in odoo",
    'version' : "12.0.0.2",
    'author' : "BrowseInfo",
    'description' : '''
            This modules gives facility to merge the picking(delivery orders / receipts).
			Merge Picking list, Merge Delivery Orders, Merge Incoming shipments, Merge Receipts. Merge orders , Merge Delivery Orders/Incoming Shipments in odoo , 
			merge transfer, merge shipment, delivery merger, shipment merger, picking merger, merge operations, merge internal transfer in odoo
			merge DO, receipt merger, merge multiple picking, merge multiple delivery, merge multiple shipment, merge warhouse picking, merge stock picking, merge stock movement
			
Fusionner la liste de prélèvement, fusionner les commandes de livraison, fusionner les envois entrants, fusionner les reçus. Fusionner les commandesfusionner le transfert, fusionner l'expédition, fusionner les livraisons, fusionner les expéditions, choisir la fusion, fusionner les opérations, fusionner le transfert internefusionner DO, réception fusion, fusionner plusieurs picking, fusionner plusieurs livraisons, fusionner plusieurs envois, fusionner picking warhouse, fusionner picking stock, fusionner stock mouvement

Combinar lista de picking, fusionar pedidos de entrega, combinar envíos entrantes, combinar recibos. Fusionar pedidos
fusión de transferencia, combinación de envío, fusión de entrega, fusión de envío, fusión de picking, fusión de operaciones, combinación de transferencia interna
fusionar DO, fusionar recibos, fusionar selección múltiple, fusionar entregas múltiples, fusionar envíos múltiples, fusionar picking de warhouse, combinar stock picking, fusionar stock de movimientos
    ''',
    'category' : "Warehouse",
    'price': 19,
    'currency': "EUR",
    'summary': 'Merge Pickings(Delivery Orders/Incoming Shipments)',
    'data': [
             'wizard/merge_picking_view.xml',
             ],
    'website': 'http://www.browseinfo.in',
    'depends' : ['sale_management','stock', 'product','sale_stock','purchase'],
    'live_test_url':'https://www.youtube.com/watch?v=psFkkkBi1ZU&feature=youtu.be',
    'installable': True,
    'auto_install': False,
	"images":['static/description/Banner.png'],
}
