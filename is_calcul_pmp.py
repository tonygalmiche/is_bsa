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
    def get_products(self):
        for obj in self:
            filtre=[('purchase_ok', '=', True)]
            if obj.stock_category_id:
                filtre.append(('is_stock_category_id', '=', obj.stock_category_id.id))
            if obj.product_id:
               filtre.append(('id', '=', obj.product_id.id))
            products=self.env['product.product'].search(filtre)
        return products


    @api.multi
    def extraire_mouvement_action(self):
        cr=self._cr
        for obj in self:
            obj.move_ids.unlink()
            obj.product_ids.unlink()
            products = obj.get_products()
            nb=len(products)
            ct=1
            for product in products:
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
                        (location_id=%s or location_dest_id=%s) and
                        date>='2021-01-01'
                    ORDER BY date desc, id desc
                """
                cr.execute(SQL,[product.id, obj.location_id.id, obj.location_id.id])
                for row in cr.fetchall():
                    qt           = row[2]
                    price_unit   = row[6] or 0.0
                    picking_id   = row[8]
                    if row[3]==obj.location_id.id:
                        qt=-qt

                    if not picking_id:
                        price_unit=0


                    vals = {
                        'calcul_id'       : obj.id,
                        'product_id'      : product.id,
                        'date'            : row[1],
                        'product_uom_qty' : qt,
                        'location_id'     : row[3],
                        'location_dest_id': row[4],
                        'product_uom'     : row[5],
                        'price_unit'      : price_unit,
                        'origin'          : row[7],
                        'picking_id'      : picking_id,
                        'move_id'         : row[9],
                    }
                    id = self.env['is.calcul.pmp.move'].create(vals)
                _logger.info(u"%s/%s extraire_mouvement_action : %s (id=%s))", ct,nb, product.name, product.id)
                ct+=1


    @api.multi
    def calcul_stock_date_action(self):
        for obj in self:
            products = obj.get_products()
            nb=len(products)
            ct=1
            for product in products:
                stock_actuel = product.qty_available
                stock_date   = stock_actuel
                stock_date_limite = 0
                periode_pmp=False
                stock0=False
                filtre=[
                    ('calcul_id', '=', obj.id),
                    ('product_id', '=', product.id),
                ]
                moves=self.env['is.calcul.pmp.move'].search(filtre, order="date desc, id desc")
                for move in moves:
                    qt = move.product_uom_qty
                    if (stock_date)<0.01:
                        stock0=True
                    if move.date<obj.date_limite:
                        periode_pmp=True
                    if stock0:
                        periode_pmp=False
                    vals = {
                        'stock_date' : stock_date,
                        'periode_pmp': periode_pmp,
                     }
                    move.write(vals)
                    stock_date-=qt
                _logger.info(u"%s/%s calcul_stock_date_action : %s (id=%s))", ct,nb, product.name, product.id)
                ct+=1


    @api.multi
    def calcul_pmp_action(self):
        for obj in self:
            obj.product_ids.unlink()
            products = obj.get_products()
            nb=len(products)
            ct=1
            for product in products:
                stock_actuel = product.qty_available
                stock_date_limite = pmp = price_unit = last = mini = maxi = nb_rcp = total_qt = total_montant = 0
                prix_moyen = 0
                filtre=[
                    ('calcul_id'  , '=', obj.id),
                    ('product_id' , '=', product.id),
                    ('periode_pmp', '=', True),
                ]
                moves=self.env['is.calcul.pmp.move'].search(filtre, order="date, id")
                for move in moves:
                    qt = move.product_uom_qty
                    qt_rcp=montant_rcp=montant_pmp=0
                    if move.picking_id:
                        price_unit  = move.price_unit
                        if price_unit>0 and move.stock_date>0:
                            if pmp==0:
                                pmp = price_unit
                            else:
                                pmp = ((move.stock_date - qt)*pmp + qt*price_unit)/move.stock_date
                            last_pmp=pmp
                        nb_rcp+=1
                        total_qt+=qt
                        last = price_unit
                        if price_unit>0 and (price_unit<mini or mini==0):
                            mini = price_unit
                        if price_unit>maxi:
                            maxi=price_unit
                        qt_rcp      = move.product_uom_qty
                        montant_rcp = qt_rcp * price_unit
                        total_montant+=montant_rcp
                    montant_pmp = pmp*move.stock_date
                    vals = {
                        'pmp'        : pmp,
                        'montant_pmp': montant_pmp,
                        'qt_rcp'     : qt_rcp,
                        'montant_rcp': montant_rcp,
                     }
                    move.write(vals)
                    stock_date_limite = move.stock_date

                if total_qt>0:
                    prix_moyen = total_montant/total_qt
                stock_valorise_pmp = stock_date_limite*pmp
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
                    'prix_moyen'        : prix_moyen,
                    'stock_date_limite' : stock_date_limite,
                    'stock_actuel'      : stock_actuel,
                    'stock_valorise_last' : stock_date_limite*last,
                    'stock_valorise_moyen': stock_date_limite*prix_moyen,
                    'stock_valorise_pmp'  : stock_date_limite*pmp,
                }
                id = self.env['is.calcul.pmp.product'].create(vals)
                _logger.info(u"%s/%s calcul_pmp_action : %s (id=%s)(pmp=%s))", ct,nb, product.name, product.id,pmp)
                ct+=1


    # @api.multi
    # def calcul_pmp_action(self):
    #     cr=self._cr
    #     for obj in self:
    #         obj.move_ids.unlink()
    #         obj.product_ids.unlink()
    #         filtre=[('purchase_ok', '=', True)]
    #         if obj.stock_category_id:
    #             filtre.append(('is_stock_category_id', '=', obj.stock_category_id.id))
    #         if obj.product_id:
    #            filtre.append(('id', '=', obj.product_id.id))
    #         products=self.env['product.product'].search(filtre)
    #         nb=len(products)
    #         ct=1
    #         for product in products:
    #             mini=maxi=last=nb_rcp=total_qt=total_montant=0
    #             stock_actuel = product.qty_available
    #             stock_date   = stock_actuel
    #             stock_date_limite = 0
    #             SQL="""
    #                 SELECT 
    #                     product_id,
    #                     date,
    #                     product_uom_qty,
    #                     location_id,
    #                     location_dest_id,
    #                     product_uom,
    #                     price_unit,
    #                     origin,
    #                     picking_id,
    #                     id
    #                 FROM stock_move
    #                 WHERE 
    #                     product_id=%s and 
    #                     state='done' and
    #                     (location_id=%s or location_dest_id=%s) and
    #                     date>='2021-01-01'
    #                 ORDER BY date desc, id desc
    #             """
    #             cr.execute(SQL,[product.id, obj.location_id.id, obj.location_id.id])
    #             periode_pmp=False
    #             stock0=False
    #             for row in cr.fetchall():
    #                 qt         = row[2]
    #                 picking_id = row[8]
    #                 if row[3]==obj.location_id.id:
    #                     qt=-qt
    #                 if (stock_date)<0.01:
    #                     stock0=True
    #                 if row[1]<obj.date_limite:
    #                     periode_pmp=True
    #                 if stock0:
    #                     periode_pmp=False
    #                 if row[1]<=obj.date_limite and stock_date_limite==0:
    #                     stock_date_limite=stock_date
    #                 price_unit = row[6]
    #                 if picking_id and periode_pmp and price_unit>0:
    #                     nb_rcp+=1
    #                     if last==0 and price_unit>0:
    #                         last=price_unit
    #                     total_qt+=qt
    #                     total_montant+=qt*price_unit
    #                     if mini>price_unit or mini==0:
    #                         mini=price_unit
    #                     if price_unit>maxi:
    #                         maxi=price_unit
    #                 if not picking_id:
    #                     price_unit=0
    #                 qt_rcp=montant_rcp=0
    #                 if periode_pmp:
    #                     if picking_id:
    #                         qt_rcp=qt
    #                         montant_rcp = qt_rcp*price_unit
    #                 vals = {
    #                     'calcul_id'       : obj.id,
    #                     'product_id'      : product.id,
    #                     'date'            : row[1],
    #                     'product_uom_qty' : qt,
    #                     'location_id'     : row[3],
    #                     'location_dest_id': row[4],
    #                     'stock_date'      : stock_date,
    #                     'product_uom'     : row[5],
    #                     'qt_rcp'          : qt_rcp,
    #                     'montant_rcp'     : montant_rcp,
    #                     'price_unit'      : price_unit,
    #                     'periode_pmp'     : periode_pmp,
    #                     'origin'          : row[7],
    #                     'picking_id'      : picking_id,
    #                     'move_id'         : row[9],
    #                 }
    #                 id = self.env['is.calcul.pmp.move'].create(vals)
    #                 stock_date-=qt
    #             pmp=0
    #             if total_qt>0:
    #                 pmp=total_montant/total_qt
    #             vals = {
    #                 'calcul_id'    : obj.id,
    #                 'product_id'   : product.id,
    #                 'last'         : last,
    #                 'mini'         : mini,
    #                 'maxi'         : maxi,
    #                 'nb_rcp'       : nb_rcp,
    #                 'total_qt'     : total_qt,
    #                 'total_montant': total_montant,
    #                 'pmp'          : pmp,
    #                 'stock_date_limite': stock_date_limite,
    #                 'stock_actuel'     : stock_actuel,
    #             }
    #             id = self.env['is.calcul.pmp.product'].create(vals)
    #             _logger.info(u"%s/%s : pmp=%s : %s (id=%s))", ct,nb,round(pmp,2), product.name, product.id)
    #             ct+=1




class is_calcul_pmp_product(models.Model):
    _name = 'is.calcul.pmp.product'
    _description = u"Articles calcul PMP"
    _order='product_id'

    calcul_id     = fields.Many2one('is.calcul.pmp', u'Calcul PMP', required=True, select=True)
    product_id    = fields.Many2one('product.product', u'Article', required=True, select=True)
    stock_category_id = fields.Many2one('is.stock.category', string='Catégorie de stock', related='product_id.is_stock_category_id' )
    last          = fields.Float(u"Dernier prix")
    mini          = fields.Float(u"Prix mini")
    maxi          = fields.Float(u"Prix maxi")
    nb_rcp        = fields.Float(u"Nb rcp")
    total_qt      = fields.Float(u"Quantité rcp")
    total_montant = fields.Float(u"Montant rcp")
    pmp                = fields.Float(u"PMP")
    prix_moyen         = fields.Float(u"Prix moyen")
    stock_actuel       = fields.Float(u"Stock actuel")
    stock_date_limite  = fields.Float(u"Stock date limite")

    stock_valorise_last  = fields.Float(u"Stock valorisé au dernier prix")
    stock_valorise_moyen = fields.Float(u"Stock valorisé au prix moyen")
    stock_valorise_pmp   = fields.Float(u"Stock valorisé au PMP")


    @api.multi
    def liste_mouvements_action(self):
        for obj in self: 
            return {
                "name": "Mouvements "+obj.product_id.name,
                "view_mode": "tree,form",
                "res_model": "is.calcul.pmp.move",
                "domain": [
                    ("calcul_id" ,"=",obj.calcul_id.id),
                    ("product_id","=",obj.product_id.id),
                ],
                "type": "ir.actions.act_window",
            }





class is_calcul_pmp_move(models.Model):
    _name = 'is.calcul.pmp.move'
    _description = u"Mouvements calcul PMP"
    _order='product_id,date,id'

    calcul_id        = fields.Many2one('is.calcul.pmp', u'Calcul PMP', required=True, select=True)
    product_id       = fields.Many2one('product.product', u'Article', required=True, select=True)
    date             = fields.Datetime(u"Date", select=True)
    product_uom_qty  = fields.Float(u"Quantité")
    location_id      = fields.Many2one('stock.location', u'Emplacement source')
    location_dest_id = fields.Many2one('stock.location', u'Emplacement destination')
    stock_date       = fields.Float(u"Stock à date")

    product_uom      = fields.Many2one('product.uom', u'Unité')
    price_unit       = fields.Float(u"Prix")

    qt_rcp           = fields.Float("Qt Rcp")
    montant_rcp      = fields.Float("Montant Rcp")
    pmp              = fields.Float("PMP")
    montant_pmp      = fields.Float("Montant PMP à date")
    periode_pmp      = fields.Boolean("Période PMP", select=True, help="Ce mouvement est compris dans le caclul du PMP")

    origin           = fields.Char(u"Origine")
    picking_id       = fields.Many2one('stock.picking', u'Picking')
    move_id          = fields.Many2one('stock.move', u'Mouvement')



