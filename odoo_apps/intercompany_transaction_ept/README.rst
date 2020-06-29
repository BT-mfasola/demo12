=============================================
Inter Company Transfer and Warehouse Transfer
=============================================
Module to manage Inter Company Transfer and Inter Warehouse Transfer along with all required documents with easiest way by just simple configurations.

========
Features
========
* **Common Features**
* An easy interface to transfer products from one warehouse to another warehouse.
* System will decide what kind of documents needs to be created based on companies of source warehouse and destination warehouses.
* All documents created by just one click based on the configuration of the system.

* **Inter Warehouse Transfer (Intra company transfer)**
* Creates Delivery Order in source warehouse & Receipts in Destination warehouse.
* Smart buttons to view created Delivery Order & Receipt.
* Allows users to do reverse transfer from the same screen. It will reverse the delivery order & receipt.

* **Inter Company Transfer**
* Creates Sales Order from source warehouse & Purchase Order in destination warehouse if warehouses belongs to different companies.
* Control over Invoice numbering / Refund numbering by specifying separate journals company wise.
* System will allow you to control pricing from the same screen. Same price will apply on sales order of source company and purchase order of destination company.
* An option to reverse entire / partial transactions with all effects. In case of Reverse intercompany transactions system will create reverse of delivery order, reverse of incoming shipment (only if they are done), debit note and credit note.
* Control over all documents process like automatic workflow of all documents, whether need to create or not, auto confirm or not, auto validate or not. Like one can control Auto confirm Sales Orders/ Purchase Order or Generate & Validate Invoice and Cancel: create credit note and reconcile.
* In multi company environment it’s not easy to create documents of multi companies without login to that company, with this app user can create all records related to intercompany transactions by just one click without login to that company, for that just need to set intercompany user company wise. So you can be sure that taxes applied on SO & PO are accurate according to the companies.

====================================
Recommended ICT Configurations
====================================

* **COMMON CONFIGURATIONS**
* Company Specific
	Set Inter Company user
	Inter company users must have rights same as an admin (to avoid access rights issue during process) but can have an access to only single company in which you set it.
	Set customer invoice and vendor bill journal (Optional)

* Warehouses Specific
	Set resupply warehouses in warehouse to generate automatic routes for internal transfers
* Product Specific
	If products are common for all companies then remove / do not set company in products (if products needs to be shared by all companies).
 	Vendor price configurations.
	Set routes in product

* Partners Specific
	Set customer location & Vendor location in partner
	Access Right: Inter company users must have an access of following areas.
	Sales Manager
	Purchase Manager
	Inventory Manager
	Accounting Manager
	Multi Warehouses
	ICT Manager

* ICT Configurations (Automatic workflow)
	Auto confirm sale / purchase order
	Auto create invoice
	Auto validate invoice
* Reverse ICT
	Create a draft credit note
	Cancel: create credit note and reconcile

* **COMPANY WISE CONFIGURATIONS**
(Company wise configurations means user need to login to each company and need to do configurations. Value of the fields might different company by company, field is unique but value might different for each company.)

* Product
	Customer taxes and vendor taxes
* Partners
	Set customer price list for partner for each companies
	Set fiscal position for partner for each companies
============
Similar Apps
============
Inter Company Transfer
ICT
Internal Transfer
Warehouse transfer
warehouse to warehouse transfer
Intercompany transfer
company to company transfer
transfer between warehouses
transfer between companies
the inter company transfer with odoo
odoo intercompany
inter company transaction in odoo
warehouse transfer odoo
odoo inter warehouse transfer
odoo internal company transfer
odoo inter company transfer
odoo intra company transfer
