# -*- coding: utf-8 -*-
from functools import total_ordering
from itertools import product
from openerp import models,fields,api
import datetime
import logging
_logger = logging.getLogger(__name__)



class is_calcul_pmp(models.Model):
    _name='is.calcul.pmp'
    _description = u"Calcul PMP"
    _order='date_creation desc'
    _rec_name = 'date_creation'


#    date = fields.Datetime('Date du stock', default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'), required=True)


    location_id       = fields.Many2one('stock.location', 'Emplacement', required=True)
    date_limite       = fields.Date("Date limite"                      , required=True)
    stock_category_id = fields.Many2one('is.stock.category', u'Catégorie de stock')
    product_id        = fields.Many2one('product.product', u'Article')
    date_creation     = fields.Date("Date de création"                 , required=True)
    createur_id       = fields.Many2one('res.users', 'Créateur'        , required=True)
    move_ids          = fields.One2many('is.calcul.pmp.move'   , 'calcul_id', u'Mouvements de stocks')
    product_ids       = fields.One2many('is.calcul.pmp.product', 'calcul_id', u'Articles')

    _defaults = {
        'date_limite'  : datetime.date.today(),
        'date_creation': datetime.date.today(),
        'createur_id'  : lambda obj, cr, uid, context: uid,
    }


    @api.multi
    def calcul_pmp_action(self):
        cr=self._cr
        for obj in self:
            obj.move_ids.unlink()
            obj.product_ids.unlink()

            filtre=[('purchase_ok', '=', True)]
    

            if obj.stock_category_id:
                filtre.append(('is_stock_category_id', '=', obj.stock_category_id.id))
            if obj.product_id:
               filtre.append(('id', '=', obj.product_id.id))

            print(filtre)


            products=self.env['product.product'].search(filtre)

            nb=len(products)
            ct=1

            for product in products:

                mini=maxi=last=nb_rcp=total_qt=total_montant=0
                stock_actuel = product.qty_available
                stock_date   = stock_actuel
                stock_date_limite = 0
                SQL="""
                    SELECT 
                        product_id,
                        date,
                        product_uom_qty,
                        location_id,
                        location_dest_id,
                        product_uom,
                        price_unit,
                        origin,
                        picking_id,
                        id
                    FROM stock_move
                    WHERE 
                        product_id=%s and 
                        state='done' and
                        (location_id=%s or location_dest_id=%s)
                    ORDER BY date desc
                """
                cr.execute(SQL,[product.id, obj.location_id.id, obj.location_id.id])
                for row in cr.fetchall():



                    if row[1]<=obj.date_limite and stock_date_limite==0:
                        stock_date_limite=stock_date


                    qt = row[2]
                    if row[3]==obj.location_id.id:
                        qt=-qt
                    price_unit = row[6]
                    if row[8] and row[1]<=obj.date_limite and price_unit>0:
                        nb_rcp+=1
                        if last==0 and price_unit>0:
                            last=price_unit
                        total_qt+=qt
                        total_montant+=qt*price_unit
                        if mini>price_unit or mini==0:
                            mini=price_unit
                        if price_unit>maxi:
                            maxi=price_unit
                    vals = {
                        'calcul_id'       : obj.id,
                        'product_id'      : product.id,
                        'date'            : row[1],
                        'product_uom_qty' : qt,
                        'location_id'     : row[3],
                        'location_dest_id': row[4],
                        'stock_date'      : stock_date,
                        'product_uom'     : row[5],
                        'price_unit'      : row[6],
                        'origin'          : row[7],
                        'picking_id'      : row[8],
                        'move_id'         : row[9],
                    }
                    id = self.env['is.calcul.pmp.move'].create(vals)
                    stock_date-=qt

                    if stock_date<0.01:
                       break
                pmp=0
                if total_qt>0:
                    pmp=total_montant/total_qt


                vals = {
                    'calcul_id'    : obj.id,
                    'product_id'   : product.id,
                    'last'         : last,
                    'mini'         : mini,
                    'maxi'         : maxi,
                    'nb_rcp'       : nb_rcp,
                    'total_qt'     : total_qt,
                    'total_montant': total_montant,
                    'pmp'          : pmp,
                    'stock_date_limite': stock_date_limite,
                    'stock_actuel'     : stock_actuel,
                }
                id = self.env['is.calcul.pmp.product'].create(vals)


                #print(ct,nb, product.id, product.name, id)

                _logger.info(u"%s/%s : pmp=%s : %s (id=%s))", ct,nb,round(pmp,2), product.name, product.id)




                ct+=1




class is_calcul_pmp_product(models.Model):
    _name = 'is.calcul.pmp.product'
    _description = u"Articles calcul PMP"
    _order='product_id'

    calcul_id     = fields.Many2one('is.calcul.pmp', u'Calcul PMP', required=True, select=True)
    product_id    = fields.Many2one('product.product', u'Article', required=True, select=True)
    last          = fields.Float(u"Dernier prix")
    mini          = fields.Float(u"Prix mini")
    maxi          = fields.Float(u"Prix maxi")
    nb_rcp        = fields.Float(u"Nb réceptions")
    total_qt      = fields.Float(u"Quantité réceptionnée")
    total_montant = fields.Float(u"Montant")
    pmp           = fields.Float(u"PMP")
    stock_date_limite = fields.Float(u"Stock date limite")
    stock_actuel      = fields.Float(u"Stock actuel")


class is_calcul_pmp_move(models.Model):
    _name = 'is.calcul.pmp.move'
    _description = u"Mouvements calcul PMP"
    _order='product_id,date desc'

    calcul_id        = fields.Many2one('is.calcul.pmp', u'Calcul PMP', required=True, select=True)
    product_id       = fields.Many2one('product.product', u'Article', required=True, select=True)
    date             = fields.Datetime(u"Date", select=True)
    product_uom_qty  = fields.Float(u"Quantité")
    location_id      = fields.Many2one('stock.location', u'Emplacement source')
    location_dest_id = fields.Many2one('stock.location', u'Emplacement destination')
    stock_date       = fields.Float(u"Stock à date")

    product_uom      = fields.Many2one('product.uom', u'Unité')
    price_unit       = fields.Float(u"Prix")
    origin           = fields.Char(u"Origine")
    picking_id       = fields.Many2one('stock.picking', u'Picking')
    move_id          = fields.Many2one('stock.move', u'Mouvement')



