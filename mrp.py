# -*- coding: utf-8 -*-


from openerp import models,fields,api
from openerp.tools.translate import _
from datetime import datetime


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



class is_workcenter_line_temps_passe(models.Model):
    _name = "is.workcenter.line.temps.passe"


    @api.depends('heure_debut','heure_fin')
    def _compute_temps_passe(self):
        for obj in self:
            temps_passe = 0
            if obj.heure_debut and obj.heure_fin:
                heure_debut = datetime.strptime(obj.heure_debut, '%Y-%m-%d %H:%M:%S')
                heure_fin   = datetime.strptime(obj.heure_fin, '%Y-%m-%d %H:%M:%S')
                temps_passe = (heure_fin - heure_debut).total_seconds()/3600
            obj.temps_passe = temps_passe


    workcenter_line_id = fields.Many2one('mrp.production.workcenter.line', 'Ordre de travail', required=True, ondelete='cascade', readonly=True)
    heure_debut        = fields.Datetime('Heure de début')
    heure_fin          = fields.Datetime('Heure de fin')
    temps_passe        = fields.Float('Temps passé', compute='_compute_temps_passe', readonly=True, store=True)


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


class mrp_bom(models.Model):
    _inherit  = 'mrp.bom'
    _order    = 'product_tmpl_id'
    _rec_name = 'product_tmpl_id'

