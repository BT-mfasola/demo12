from . import models
from . import wizard
from . import report
from odoo.api import Environment, SUPERUSER_ID
import logging

_logger=logging.getLogger(__name__)



multi_company_ir_rules = {'stock.stock_warehouse_comp_rule':'stock.group_stock_user',
                          'stock.stock_location_comp_rule':'stock.group_stock_user',
                          'stock.stock_picking_type_rule':'stock.group_stock_user'}
                        
                               

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