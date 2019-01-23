# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp
import datetime


class stock_transfer_details(models.TransientModel):
    _inherit = 'stock.transfer_details'
    _description = 'Picking wizard'


    #** Fonction reprise le 23/01/2019 pour pouvoir réceptionner plusieurs lignes du même article
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        picking_ids = context.get('active_ids', [])
        picking_id, = picking_ids
        picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
        res = super(stock_transfer_details, self).default_get(cr, uid, fields, context=context)
        picking_ids = context.get('active_ids', [])
        active_model = context.get('active_model')
        if not picking_ids or len(picking_ids) != 1:
            return res
        assert active_model in ('stock.picking'), 'Bad context propagation'
        picking_id, = picking_ids
        picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
        items = []
        packs = []
        if not picking.pack_operation_ids:
            picking.do_prepare_partial()
        for move in picking.move_lines:
            item = {
                #'packop_id': op.id,
                'product_id': move.product_id.id,
                'product_uom_id': move.product_uom.id,
                'quantity': move.product_qty,
                #'package_id': op.package_id.id,
                #'lot_id': op.lot_id.id,
                'sourceloc_id': move.location_id.id,
                'destinationloc_id': move.location_dest_id.id,
                #'result_package_id': op.result_package_id.id,
                'date': move.date, 
                #'owner_id': move.owner_id.id,
                'name':move.name,
            }
            if move.product_id:
                items.append(item)
        #***********************************************************************

#        for op in picking.pack_operation_ids:
#            print op
#            item = {
#                'packop_id': op.id,
#                'product_id': op.product_id.id,
#                'product_uom_id': op.product_uom_id.id,
#                'quantity': op.product_qty,
#                'package_id': op.package_id.id,
#                'lot_id': op.lot_id.id,
#                'sourceloc_id': op.location_id.id,
#                'destinationloc_id': op.location_dest_id.id,
#                'result_package_id': op.result_package_id.id,
#                'date': op.date, 
#                'owner_id': op.owner_id.id,
#                'name':'op.move_id.name',
#            }
#            if op.product_id:
#                items.append(item)
#            elif op.package_id:
#                packs.append(item)
        res.update(item_ids=items)
        res.update(packop_ids=packs)

        return res


class stock_transfer_details_items(models.TransientModel):
    _inherit = 'stock.transfer_details_items'

    name = fields.Char('Description')

