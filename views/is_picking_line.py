# -*- coding: utf-8 -*-

from openerp import tools
from openerp import models,fields,api
from openerp.tools.translate import _


class is_picking_line(models.Model):
    _name='is.picking.line'
    _order='picking_id desc, id'
    _auto = False

    picking_id             = fields.Many2one('stock.picking', u'Bon de livraison / réception')
    reference              = fields.Char(u"Référence")
    is_date_bl             = fields.Date(u"Date du BL")
    date_done              = fields.Date(u"Date du transfert")
    partner_id             = fields.Many2one('res.partner', u'Client / Fournisseur')
    picking_type_id        = fields.Many2one('stock.picking.type', u'Picking Type')
    product_id             = fields.Many2one('product.product', u'Article')
    product_uom_qty        = fields.Float(u'Quantité'   , digits=(14,2))
    description            = fields.Char(u"Description")

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'is_picking_line')
        cr.execute("""
            CREATE OR REPLACE view is_picking_line AS (
                select 
                    sm.id,
                    sm.picking_id,
                    sp.name reference,
                    sp.is_date_bl,
                    sp.date_done::date,
                    sp.partner_id,
                    sp.picking_type_id,
                    sm.product_id,
                    sm.product_uom_qty,
                    sm.name description
                from stock_picking sp join stock_move sm on sp.id=sm.picking_id
                where sp.state='done' and sm.state='done'
            );
        """)

