# -*- coding: utf-8 -*-


from openerp import models,fields,api
from openerp.tools.translate import _


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


class mrp_production_workcenter_line(models.Model):
    _inherit = "mrp.production.workcenter.line"

    is_commentaire = fields.Text('Commentaire')


class mrp_bom(models.Model):
    _inherit  = 'mrp.bom'
    _order    = 'product_tmpl_id'
    _rec_name = 'product_tmpl_id'

