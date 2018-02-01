# -*- coding: utf-8 -*-

from openerp import tools
from openerp import models,fields,api
from openerp.tools.translate import _


class is_sale_order_line(models.Model):
    _name='is.sale.order.line'
    _order='date_order desc'
    _auto = False

    order_id               = fields.Many2one('sale.order', 'Commande')
    date_order             = fields.Date("Date commande")
    client_order_ref       = fields.Char("Commande client")
    partner_id             = fields.Many2one('res.partner', 'Client')
    is_categorie_client_id = fields.Many2one('is.categorie.client', string='Catégorie de client')
    product_id             = fields.Many2one('product.product', 'Article')
    product_uom_qty        = fields.Float('Quantité'   , digits=(14,2))
    price_unit             = fields.Float('Prix'       , digits=(14,2))
    montant_ht             = fields.Float('Montant HT' , digits=(14,2))
    is_date_prevue         = fields.Date("Date prévue")
    is_date_demandee       = fields.Date("Date demandée")


    def init(self, cr):
        tools.drop_view_if_exists(cr, 'is_sale_order_line')
        cr.execute("""
            CREATE OR REPLACE view is_sale_order_line AS (
                select 
                    sol.id,
                    sol.order_id,
                    so.date_order,
                    so.client_order_ref,
                    so.partner_id,
                    rp.is_categorie_client_id,
                    sol.product_id,
                    sol.product_uom_qty,
                    sol.price_unit,
                    sol.product_uom_qty*sol.price_unit montant_ht,
                    sol.is_date_prevue,
                    sol.is_date_demandee
                from sale_order_line sol inner join sale_order so on sol.order_id=so.id
                                         inner join res_partner rp on so.partner_id=rp.id
                where 
                    sol.state<>'cancel' and 
                    so.state<>'cancel'
            );
        """)

