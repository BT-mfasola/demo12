# © 2014 - 2017 Sudokeys (Nicolas Potier <nicolas.potier@sudokeys.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    recurring_invoice_po = fields.Boolean('Purchase Subscription')
