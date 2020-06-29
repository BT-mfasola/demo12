from . import models
from . import wizard
from odoo.api import Environment, SUPERUSER_ID
import logging

_logger=logging.getLogger(__name__)

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

def uninstall_hook_update_rule(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    for rule_xml_id,group_xml_id in multi_company_ir_rules.items() :
        rule = env.ref(rule_xml_id)
        group = env.ref(group_xml_id)
        if group in rule.groups :
            rule.write({'groups':[(3,group.id)]})
            
            
def post_init_update_rule(cr,registry): 
    env = Environment(cr, SUPERUSER_ID, {})
    for rule_xml_id,group_xml_id in multi_company_ir_rules.items() :
        rule = env.ref(rule_xml_id)
        group = env.ref(group_xml_id)
        if rule and group :
            if group not in rule.groups :
                rule.write({'groups':[(4,group.id)]})
