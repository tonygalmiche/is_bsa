# -*- coding: utf-8 -*-

from openerp import tools
from openerp import models,fields,api
from openerp.tools.translate import _


class is_liste_manquants(models.Model):
    _name='is.liste.manquants'
    _order='product_id,date'
    _auto = False

    product_id              = fields.Many2one('product.product', 'Article')
    type_val                = fields.Char('Type')
    picking_id              = fields.Many2one('stock.picking', 'Réception')
    purchase_line_id        = fields.Many2one('purchase.order.line', 'Ligne de commande')
    date                    = fields.Date("Date")
    uom_id                  = fields.Many2one('product.uom', 'Unité')
    qt                      = fields.Float('Quantité', digits=(14,2))
    cumul                   = fields.Float('Cumul'   , digits=(14,2))

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'is_liste_manquants')
        tools.drop_view_if_exists(cr, 'is_liste_manquants_tmp')
        cr.execute("""
            CREATE OR REPLACE view is_liste_manquants_tmp AS (
                select 
                    res.product_id, res.type_val, res.picking_id, res.purchase_line_id, res.date, res.uom_id, res.qt
                from (
                    select 
                        pp.id product_id,
                        'stock' type_val,
                        null as picking_id,
                        null as purchase_line_id,
                        '2000-01-01' date,
                        pt.uom_id,
                        (
                            select sum(sq.qty)
                            from stock_quant sq inner join stock_location sl on sq.location_id=sl.id
                            where sl.usage='internal' and sq.product_id=pp.id
                        ) qt
                    from product_product pp inner join product_template pt on pp.product_tmpl_id=pt.id
                    where pt.purchase_ok='t' 

                    union

                    select 
                        sm.product_id,
                        'cde' type_val,
                        sm.picking_id as picking_id,
                        sm.purchase_line_id as purchase_line_id,
                        COALESCE(pol.is_date_ar, sm.date_expected::date) date,
                        sm.product_uom uom_id,
                        sm.product_uom_qty qt
                    from stock_move sm inner join stock_picking sp on sm.picking_id=sp.id
                                             left outer join purchase_order_line pol on sm.purchase_line_id=pol.id
                    where sm.state not in ('cancel','done') and sp.picking_type_id=1   


                    union

                    select 
                        sm.product_id,
                        'prod' type_val,
                        sm.picking_id as picking_id,
                        null as purchase_line_id,
                        sm.date_expected::date date,
                        sm.product_uom uom_id,
                        -sum(sm.product_uom_qty) qt
                    from stock_move sm inner join mrp_production mp on sm.raw_material_production_id=mp.id
                    where sm.state not in ('cancel','done')    
                    group by sm.product_id, sm.date_expected::date, sm.product_uom, sm.picking_id
                ) res   inner join product_product pp on res.product_id=pp.id
                        inner join product_template pt on pp.product_tmpl_id=pt.id
                where pt.purchase_ok='t' 
                order by res.date
            );

            CREATE OR REPLACE view is_liste_manquants AS (
                select
                    row_number() over(order by tmp.product_id, tmp.date) as id,
                    tmp.product_id, 
                    tmp.type_val, 
                    tmp.picking_id, 
                    tmp.purchase_line_id,
                    tmp.date, 
                    tmp.uom_id, 
                    tmp.qt,
                    (
                        select sum(tmp2.qt) 
                        from is_liste_manquants_tmp tmp2
                        where tmp2.product_id=tmp.product_id and tmp2.date<=tmp.date
                    ) cumul
                from is_liste_manquants_tmp tmp
            );
        """)

