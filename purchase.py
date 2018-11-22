# -*- coding: utf-8 -*-

from openerp import models,fields,api
from openerp.tools.translate import _


class purchase_order_line(models.Model):
    _inherit = "purchase.order.line"

    is_date_ar = fields.Date("Date AR")



class purchase_order(models.Model):
    _inherit = "purchase.order"


    @api.multi
    def mouvement_stock_action(self):
        for obj in self:
            ids=[]
            for picking in obj.picking_ids:
                for line in picking.move_lines:
                    ids.append(line.id)
            if not ids:
                raise Warning(u'Aucune ligne de réception')
            else:
                return {
                    'name': u'Lignes de réception '+obj.name,
                    'view_mode': 'tree,form',
                    'view_type': 'form',
                    'res_model': 'stock.move',
                    'domain': [
                        ('id','in',ids),
                    ],
                    'type': 'ir.actions.act_window',
                }

