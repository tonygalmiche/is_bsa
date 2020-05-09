# -*- coding: utf-8 -*-


from openerp import models,fields,api,tools, SUPERUSER_ID
from openerp.tools.translate import _
from datetime import datetime
from openerp.addons.product import _common



class is_gabarit(models.Model):
    _name='is.gabarit'
    _order='name'
    _sql_constraints = [('name_uniq','UNIQUE(name)', 'Ce gabarit existe déjà')] 

    name = fields.Char("Gabarit", required=True)



class mrp_production(models.Model):
    _inherit = "mrp.production"

    date_planned          = fields.Datetime('Date plannifiée', required=False, select=1, readonly=False, states={}, copy=False)
    is_date_prevue        = fields.Date('Date prévue', related='is_sale_order_line_id.is_date_prevue', readonly=True)
    is_date_planifiee     = fields.Date('Date planifiée')
    is_gabarit_id         = fields.Many2one('is.gabarit', u'Gabarit')
    is_sale_order_line_id = fields.Many2one('sale.order.line', u'Ligne de commande')
    is_sale_order_id      = fields.Many2one('sale.order', u'Commande', related='is_sale_order_line_id.order_id', readonly=True)






#    def _prepare_lines(self, cr, uid, production, properties=None, context=None):
#        # search BoM structure and route
#        bom_obj = self.pool.get('mrp.bom')
#        uom_obj = self.pool.get('product.uom')
#        bom_point = production.bom_id
#        bom_id = production.bom_id.id
#        if not bom_point:
#            bom_id = bom_obj._bom_find(cr, uid, product_id=production.product_id.id, properties=properties, context=context)
#            if bom_id:
#                bom_point = bom_obj.browse(cr, uid, bom_id)
#                routing_id = bom_point.routing_id.id or False
#                self.write(cr, uid, [production.id], {'bom_id': bom_id, 'routing_id': routing_id})

#        if not bom_id:
#            raise osv.except_osv(_('Error!'), _("Cannot find a bill of material for this product."))

#        # get components and workcenter_lines from BoM structure
#        factor = uom_obj._compute_qty(cr, uid, production.product_uom.id, production.product_qty, bom_point.product_uom.id)
#        print 'factor=',factor


#        # product_lines, workcenter_lines
#        return bom_obj._bom_explode(cr, uid, bom_point, production.product_id, factor / bom_point.product_qty, properties, routing_id=production.routing_id.id, context=context)



#    def _action_compute_lines(self, cr, uid, ids, properties=None, context=None):
#        """ Compute product_lines and workcenter_lines from BoM structure
#        @return: product_lines
#        """
#        if properties is None:
#            properties = []
#        results = []
#        prod_line_obj = self.pool.get('mrp.production.product.line')
#        workcenter_line_obj = self.pool.get('mrp.production.workcenter.line')
#        for production in self.browse(cr, uid, ids, context=context):
#            #unlink product_lines
#            prod_line_obj.unlink(cr, SUPERUSER_ID, [line.id for line in production.product_lines], context=context)
#            #unlink workcenter_lines
#            workcenter_line_obj.unlink(cr, SUPERUSER_ID, [line.id for line in production.workcenter_lines], context=context)

#            res = self._prepare_lines(cr, uid, production, properties=properties, context=context)
#            results = res[0] # product_lines
#            results2 = res[1] # workcenter_lines

#            # reset product_lines in production order
#            for line in results:
#                line['production_id'] = production.id
#                #line['is_offset']     = 
#                prod_line_obj.create(cr, uid, line)

#            #reset workcenter_lines in production order
#            for line in results2:
#                print line
#                line['production_id'] = production.id
#                workcenter_line_obj.create(cr, uid, line, context)
#        return results


class is_workcenter_line_temps_passe(models.Model):
    _name = "is.workcenter.line.temps.passe"


    @api.depends('heure_debut','heure_fin')
    def _compute_temps_passe(self):
        for obj in self:
            temps_passe = 0
            if obj.heure_debut and obj.heure_fin:
                nb = obj.nb or 1
                heure_debut = datetime.strptime(obj.heure_debut, '%Y-%m-%d %H:%M:%S')
                heure_fin   = datetime.strptime(obj.heure_fin, '%Y-%m-%d %H:%M:%S')
                temps_passe = nb*(heure_fin - heure_debut).total_seconds()/3600
            obj.temps_passe = temps_passe


    workcenter_line_id = fields.Many2one('mrp.production.workcenter.line', 'Ordre de travail', required=True, ondelete='cascade', readonly=True)
    employe_id  = fields.Many2one('hr.employee', u'Opérateur')
    nb          = fields.Integer(u'Nombre de personnes au poste',default=1)
    heure_debut = fields.Datetime(u'Heure de début')
    heure_fin   = fields.Datetime(u'Heure de fin')
    temps_passe = fields.Float(u'Temps passé', compute='_compute_temps_passe', readonly=True, store=True)


class mrp_production_workcenter_line(models.Model):
    _inherit = "mrp.production.workcenter.line"


    @api.depends('is_temps_passe_ids')
    def compute_temps_passe(self):
        for obj in self:
            temps_passe = 0
            ecart = 0
            for line in obj.is_temps_passe_ids:
                temps_passe+=line.temps_passe
            obj.is_temps_passe = temps_passe
            obj.is_ecart       = obj.hour - temps_passe


    is_commentaire     = fields.Text('Commentaire')
    is_temps_passe_ids = fields.One2many('is.workcenter.line.temps.passe'  , 'workcenter_line_id', u"Temps passé")
    is_temps_passe     = fields.Float('Temps passé', compute='compute_temps_passe', readonly=True, store=True)
    is_ecart           = fields.Float('Ecart', compute='compute_temps_passe', readonly=True, store=True)
    is_offset          = fields.Integer('Offset (jour)', help="Offset en jours par rapport à l'opération précédente pour le calcul du planning")


class mrp_bom(models.Model):
    _inherit  = 'mrp.bom'
    _order    = 'product_tmpl_id'
    _rec_name = 'product_tmpl_id'


    def _bom_explode(self, cr, uid, bom, product, factor, properties=None, level=0, routing_id=False, previous_products=None, master_bom=None, context=None):
        result, result2 = super(mrp_bom, self)._bom_explode(cr, uid, bom, product, factor, properties=properties, level=level, routing_id=routing_id, previous_products=previous_products, master_bom=master_bom, context=context)

        uom_obj = self.pool.get("product.uom")
        routing_obj = self.pool.get('mrp.routing')
        master_bom = master_bom or bom

        def _factor(factor, product_efficiency, product_rounding):
            factor = factor / (product_efficiency or 1.0)
            factor = _common.ceiling(factor, product_rounding)
            if factor < product_rounding:
                factor = product_rounding
            return factor

        factor = _factor(factor, bom.product_efficiency, bom.product_rounding)
        result2 = []
        routing = (routing_id and routing_obj.browse(cr, uid, routing_id)) or bom.routing_id or False
        if routing:
            for wc_use in routing.workcenter_lines:
                wc = wc_use.workcenter_id
                d, m = divmod(factor, wc_use.workcenter_id.capacity_per_cycle)
                m=round(m,6) #TODO : Pour corriger un bug
                mult = (d + (m and 1.0 or 0.0))
                cycle = mult * wc_use.cycle_nbr
                result2.append({
                    'name': tools.ustr(wc_use.name) + ' - ' + tools.ustr(bom.product_tmpl_id.name_get()[0][1]),
                    'workcenter_id': wc.id,
                    'sequence': level + (wc_use.sequence or 0),
                    'is_offset': wc_use.is_offset,
                    'cycle': cycle,
                    'hour': float(wc_use.hour_nbr * mult + ((wc.time_start or 0.0) + (wc.time_stop or 0.0) + cycle * (wc.time_cycle or 0.0)) * (wc.time_efficiency or 1.0)),
                })

        print 'result2=',result2
        return result, result2


class mrp_routing_workcenter(models.Model):
    _inherit  = 'mrp.routing.workcenter'

    is_offset = fields.Integer('Offset (jour)', help="Offset en jours par rapport à l'opération précédente pour le calcul du planning")



