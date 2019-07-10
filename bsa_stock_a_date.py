# -*- coding: utf-8 -*-
from openerp import models,fields,api
import time


class bsa_stock_a_date(models.Model):
    _name='bsa.stock.a.date'
    _order='name'

    name              = fields.Many2one('product.product','Article', required=True)
    default_code      = fields.Char("Référence interne")
    stock_category_id = fields.Many2one('is.stock.category', string='Catégorie de stock')
    uom_id            = fields.Many2one('product.uom','Unité')
    list_price        = fields.Float("Prix de vente")
    standard_price    = fields.Float("Prix de revient")
    stock             = fields.Float("Stock à date")
    stock_valorise    = fields.Float("Stock valorisé au prix de revient")
    date_stock        = fields.Datetime('Date stock')


class bsa_stock_a_date_wizard(models.TransientModel):
    _name = "bsa.stock.a.date.wizard"

    date = fields.Datetime('Date du stock', default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'), required=True)


    @api.multi
    def calul_stock_action(self):
        cr=self._cr
        for obj in self:
            sql="delete from bsa_stock_a_date"
            cr.execute(sql)
            sql="""
                select 
                        sm2.product_id, 
                        sum(sm.qty)
                from (

                    select 
                        sm.id,
                        sum(sq.qty)         as qty,
                        sl1.name            as src,
                        sl2.name            as dest
                    from stock_move sm inner join stock_location        sl1 on sm.location_id=sl1.id
                                       inner join stock_location        sl2 on sm.location_dest_id=sl2.id
                                       left outer join stock_quant_move_rel sqmr on sm.id=sqmr.move_id
                                       left outer join stock_quant            sq on sqmr.quant_id=sq.id
                    where sm.state='done' and sl2.usage='internal' 
                    group by 
                        sm.id,
                        sm.product_uom,
                        sl1.name,
                        sl2.name

                    union

                    select 
                        sm.id,
                        -sum(sq.qty)        as qty,
                        sl1.name            as dest,
                        sl2.name            as src
                    from stock_move sm inner join stock_location        sl1 on sm.location_dest_id=sl1.id
                                       inner join stock_location        sl2 on sm.location_id=sl2.id
                                       left outer join stock_quant_move_rel sqmr on sm.id=sqmr.move_id
                                       left outer join stock_quant            sq on sqmr.quant_id=sq.id
                    where sm.state='done' and sl2.usage='internal' 
                    group by 
                        sm.id,
                        sm.product_uom,
                        sl1.name,
                        sl2.name


                ) sm    inner join stock_move                sm2 on sm.id=sm2.id           
                        inner join product_product            pp on sm2.product_id=pp.id
                        inner join product_template           pt on pp.product_tmpl_id=pt.id
                        left outer join stock_picking_type   spt on sm2.picking_type_id=spt.id
                        left outer join stock_picking         sp on sm2.picking_id=sp.id

                where sm2.date<='"""+str(obj.date)+"""'
                group by sm2.product_id
                having sum(sm.qty)<>0
                order by sm2.product_id
            """

            cr.execute(sql)
            for row in cr.fetchall():
                product_id=row[0]
                product=self.env['product.product'].browse(product_id)
                if product:
                    stock=row[1]
                    stock_valorise=stock*product.standard_price
                    vals = {
                        'name'             : product_id,
                        'default_code'     : product.default_code,
                        'stock_category_id': product.is_stock_category_id.id,
                        'stock'            : stock,
                        'uom_id'           : product.uom_id.id,
                        'list_price'       : product.list_price,
                        'standard_price'   : product.standard_price,
                        'stock_valorise'   : stock_valorise,
                        'date_stock'       : obj.date
                    }
                    res=self.env['bsa.stock.a.date'].create(vals)
                    print row,res,product


            return {
                'name': u'Stock au '+str(obj.date),
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'bsa.stock.a.date',
                'type': 'ir.actions.act_window',
            }








