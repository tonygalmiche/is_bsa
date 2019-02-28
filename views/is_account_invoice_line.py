# -*- coding: utf-8 -*-

from openerp import tools
from openerp import models,fields,api
from openerp.tools.translate import _


class is_account_invoice_line(models.Model):
    _name='is.account.invoice.line'
    _order='invoice_id desc, id'
    _auto = False


    invoice_id             = fields.Many2one('account.invoice', 'Facture')
    internal_number        = fields.Char("N°Facture")
    date_invoice           = fields.Date("Date Facture")
    order_id               = fields.Many2one('sale.order', 'Commande')
    product_id             = fields.Many2one('product.product', 'Article')
    description            = fields.Text("Description")
    quantity               = fields.Float('Quantité'   , digits=(14,2))
    price_unit             = fields.Float('Prix unitaire', digits=(14,4))
    price_subtotal         = fields.Float('Montant HT'   , digits=(14,4))
    partner_id             = fields.Many2one('res.partner', u'Client/Fournisseur Facturé')
    move_id                = fields.Many2one('stock.move', 'Mouvement')
    type                   = fields.Char("Type Facture")
    state                  = fields.Char("Etat Facture")


    def init(self, cr):
        tools.drop_view_if_exists(cr, 'is_account_invoice_line')
        cr.execute("""
            CREATE OR REPLACE view is_account_invoice_line AS (
                select
                    ail.id,
                    ail.invoice_id,
                    ai.internal_number,
                    ai.date_invoice,
                    sol.order_id,
                    ail.product_id,
                    ail.name description,
                    ail.quantity,
                    ail.price_unit,
                    ail.price_subtotal,
                    ail.is_stock_move_id move_id,
                    ai.partner_id,
                    ai.type,
                    ai.state
                from account_invoice_line ail inner join account_invoice ai on ail.invoice_id=ai.id
                                              left outer join stock_move sm on ail.is_stock_move_id=sm.id
                                              left outer join procurement_order po on sm.procurement_id=po.id
                                              left outer join sale_order_line sol on po.sale_line_id=sol.id
                                              left outer join sale_order so on sol.order_id=so.id
            );
        """)

