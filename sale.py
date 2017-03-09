# -*- coding: utf-8 -*-

from openerp import models,fields,api
from openerp.tools.translate import _
from openerp import workflow
from openerp.exceptions import Warning
import datetime


class sale_order_line(models.Model):
    _name = "sale.order.line"
    _inherit = "sale.order.line"



    is_date_demandee      = fields.Date('Date demandée')
    is_date_prevue        = fields.Date('Date prévue')
    is_fabrication_prevue = fields.Float('Fabrication prévue'           , compute='_compute_fab', readonly=True, store=False, digits=(14,0))
    is_reste              = fields.Float('Reste à lancer en fabrication', compute='_compute_fab', readonly=True, store=False, digits=(14,0))
    is_client_order_ref   = fields.Char('Référence Client', store=True, compute='_compute')


    @api.depends('order_id','order_id.client_order_ref')
    def _compute(self):
        for obj in self:
            if obj.order_id:
                obj.is_client_order_ref = obj.order_id.client_order_ref


    def _compute_fab(self):
        cr = self._cr
        for obj in self:
            sql="""
                select sum(product_qty)
                from mrp_production
                where is_sale_order_line_id="""+str(obj.id)+"""
            """
            cr.execute(sql)
            fabrication_prevue=0
            for row in cr.fetchall():
                fabrication_prevue=row[0] or 0
            obj.is_fabrication_prevue=fabrication_prevue
            obj.is_reste=obj.product_uom_qty-fabrication_prevue


    @api.multi
    def action_creer_of(self):
        for obj in self:
            print obj

            mrp_production_obj = self.env['mrp.production']
            bom_obj = self.env['mrp.bom']


            bom_id = bom_obj._bom_find(product_id=obj.product_id.id, properties=[])
            routing_id = False
            if bom_id:
                bom_point = bom_obj.browse(bom_id)
                routing_id = bom_point.routing_id.id or False
            mrp_id = mrp_production_obj.create({
                'product_id'           : obj.product_id.id,
                'product_uom'          : obj.product_id.uom_id.id,
                'product_qty'          : obj.is_reste,
                'bom_id'               : bom_id,
                'routing_id'           : routing_id,
                'origin'               : obj.order_id.name,
                'is_date_planifiee'    : datetime.date.today().strftime('%Y-%m-%d'),
                'is_sale_order_line_id': obj.id
            })
            try:
                workflow.trg_validate(self._uid, 'mrp.production', mrp_id.id, 'button_confirm', self._cr)
            except Exception as inst:
                msg="Impossible de convertir la "+obj.name+'\n('+str(inst)+')'
                raise Warning(msg)
            if mrp_id:
                return {
                    'name': "Ordre de fabrication",
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'mrp.production',
                    'type': 'ir.actions.act_window',
                    'res_id': mrp_id.id,
                    'domain': '[]',
                }


    def name_get(self, cr, uid, ids, context=None):
        res = []
        for obj in self.browse(cr, uid, ids, context=context):
            name=obj.order_id.name+u' '+obj.name
            if obj.is_date_prevue:
                name=name+u' '+str(obj.is_date_prevue)
            res.append((obj.id,name))
        return res


    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            ids = self.search(cr, user, ['|',('name','ilike', name),('order_id.name','ilike', name)], limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result








