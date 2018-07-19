# -*- coding: utf-8 -*-

from openerp import models,fields,api

class product_template(models.Model):
    _inherit = 'product.template'
    
    is_ce_en1090                 = fields.Boolean(u'CE EN1090', help="Si cette case est cochée, le logo CE 1166 apparaîtra sur le BL")
    is_stock_prevu_valorise      = fields.Float('Stock prévu valorisé'     , store=False, compute='_compute')
    is_stock_disponible_valorise = fields.Float('Stock disponible valorisé', store=False, compute='_compute')
    is_recalcul_prix_revient     = fields.Boolean(u'Recalcul automatique du prix de revient', help="Si cette case est cochée, le prix de revient sera recalculé pendant la nuit")


    def _compute(self):
        for obj in self:
            is_stock_disponible_valorise = 0
            is_stock_prevu_valorise      = 0
            if obj.qty_available > 0:
                is_stock_disponible_valorise = obj.standard_price * obj.qty_available
            if obj.virtual_available > 0:
                is_stock_prevu_valorise = obj.standard_price * obj.virtual_available
            obj.is_stock_disponible_valorise = is_stock_disponible_valorise
            obj.is_stock_prevu_valorise      = is_stock_prevu_valorise


    @api.multi
    def copy(self,vals):
        for obj in self:
            res=super(product_template, self).copy(vals)
            for line in obj.seller_ids:
                v = {
                    'product_tmpl_id': res.id,
                    'name'      : line.name.id,
                }
                id = self.env['product.supplierinfo'].create(v)
            return res


    @api.multi
    def recalcul_prix_revient_action(self):
        cr , uid, context = self.env.args
        prod_obj = self.pool.get('product.template')
        for obj in self:
            if obj.cost_method=='standard' and obj.is_recalcul_prix_revient:
                res=prod_obj.compute_price(cr, uid, [], template_ids=[obj.id], real_time_accounting=False, recursive=True, test=False, context=context)


