# -*- coding: utf-8 -*-

from openerp import tools
from openerp import models,fields,api
from openerp.tools.translate import _


class is_derniere_commande_achat(models.Model):
    _name='is.derniere.commande.achat'
    _order='name'
    _auto = False


    product_id             = fields.Many2one('product.product', 'Variante')
    product_tmpl_id        = fields.Many2one('product.product', 'Article')
    name                   = fields.Char(u"Désignation")
    default_code           = fields.Char(u"Référence interne")
    sale_ok                = fields.Char(u"Peut être vendu")
    purchase_ok            = fields.Char(u"Peut être acheté")
    price_unit             = fields.Float('Prix unitaire', digits=(14,4))
    product_uom            = fields.Many2one('product.uom', u'Unité')
    date_planned           = fields.Date(u"Date prévue")
    order_id               = fields.Many2one('purchase.order', 'Commande')
    line_id                = fields.Many2one('purchase.order.line', 'Ligne de commande commande')


    def init(self, cr):
        tools.drop_view_if_exists(cr, 'is_derniere_commande_achat')
        cr.execute("""
            CREATE OR REPLACE view is_derniere_commande_achat AS (
                select
                    pp.id,
                    pp.id product_id,
                    pp.product_tmpl_id,
                    pt.name,
                    pp.default_code,
                    pt.sale_ok,
                    pt.purchase_ok,
                    (select pol.price_unit   from purchase_order_line pol where pol.product_id=pp.id order by pol.id desc limit 1) price_unit,
                    (select pol.product_uom  from purchase_order_line pol where pol.product_id=pp.id order by pol.id desc limit 1) product_uom,
                    (select pol.date_planned from purchase_order_line pol where pol.product_id=pp.id order by pol.id desc limit 1) date_planned,
                    (select pol.order_id     from purchase_order_line pol where pol.product_id=pp.id order by pol.id desc limit 1) order_id,
                    (select pol.id           from purchase_order_line pol where pol.product_id=pp.id order by pol.id desc limit 1) line_id
                from product_product pp inner join product_template pt on pp.product_tmpl_id=pt.id
            );
        """)

