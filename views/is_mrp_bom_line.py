# -*- coding: utf-8 -*-

from openerp import tools
from openerp import models,fields,api
from openerp.tools.translate import _


class is_mrp_bom_line(models.Model):
    _name='is.mrp.bom.line'
    _order='compose_id'
    _auto = False


    bom_id         = fields.Many2one('mrp.bom', 'Nomenclature')
    compose_id     = fields.Many2one('product.template', 'Composé')
    composant_id   = fields.Many2one('product.template', 'Composant')
    product_qty    = fields.Float('Quantité nomenclature', digits=(14,2))
    product_uom    = fields.Many2one('product.uom', 'Unité')
    standard_price = fields.Float('Prix de revient', digits=(14,2))


    def init(self, cr):
        tools.drop_view_if_exists(cr, 'is_mrp_bom_line')
        cr.execute("""

            CREATE OR REPLACE FUNCTION get_standard_price(product_id integer) RETURNS float AS $$
            BEGIN
                RETURN (
                    select value_float
                    from ir_property ip 
                    where ip.name='standard_price' and res_id=concat('product.template,',product_id)
                    limit 1
                );
            END;
            $$ LANGUAGE plpgsql;


            CREATE OR REPLACE view is_mrp_bom_line AS (
                select
                    mbl.id,
                    mbl.bom_id,
                    pt.id compose_id,
                    pt2.id composant_id,
                    mbl.product_qty,
                    mbl.product_uom,
                    coalesce(get_standard_price(pt2.id),0) standard_price
                from mrp_bom_line mbl inner join mrp_bom          mb  on mbl.bom_id=mb.id
                                      inner join product_template pt  on mb.product_tmpl_id=pt.id
                                      inner join product_product  pp  on mbl.product_id=pp.id 
                                      inner join product_template pt2 on pp.product_tmpl_id=pt2.id
            );

        """)

