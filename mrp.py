# -*- coding: utf-8 -*-
from openerp import models,fields,api,tools, SUPERUSER_ID
from openerp.tools.translate import _
from datetime import datetime, date, timedelta
from openerp.addons.product import _common
from openerp.exceptions import Warning


class is_gabarit(models.Model):
    _name='is.gabarit'
    _order='name'
    _sql_constraints = [('name_uniq','UNIQUE(name)', 'Ce gabarit existe déjà')] 

    name = fields.Char("Gabarit", required=True)


class mrp_production(models.Model):
    _inherit = "mrp.production"
    _order = "id desc"

    date_planned          = fields.Datetime('Date plannifiée', required=False, select=1, readonly=False, states={}, copy=False)
    is_date_prevue        = fields.Date(u'Date prévue commande client', related='is_sale_order_line_id.is_date_prevue', readonly=True, help='Date de prévue sur la ligne de commande client')
    is_date_planifiee     = fields.Date(u'Date planifiée début')
    is_date_planifiee_fin = fields.Date(u'Date planifiée fin', readonly=True)
    is_ecart_date         = fields.Integer(u'Ecart date', readonly=True)
    is_gabarit_id         = fields.Many2one('is.gabarit', u'Gabarit')
    is_sale_order_line_id = fields.Many2one('sale.order.line', u'Ligne de commande')
    is_sale_order_id      = fields.Many2one('sale.order', u'Commande', related='is_sale_order_line_id.order_id', readonly=True)


    @api.multi
    def planifier_operation_action(self):
        for obj in self:
            if obj.state in ['confirmed','ready','in_production']:
                ops = self.env["mrp.production.workcenter.line"].search([('production_id','=',obj.id),('state','in',['draft','pause','startworking'])],order='production_id,sequence')
                if ops:
                    ops[0].is_date_debut = obj.is_date_planifiee
                    ops[0].planifier_operation_action()



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
    _order = "id desc"

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
    is_date_debut      = fields.Date(u'Date de début', index=True)
    is_date_fin        = fields.Date(u'Date de fin')


    @api.multi
    def write(self, vals):
        if 'date_start' in vals and 'is_date_debut' not in vals:
            vals['is_date_debut'] = vals['date_start']
        if 'date_finished' in vals and 'is_date_fin' not in vals:
            vals['is_date_fin'] = vals['date_finished']
        res=super(mrp_production_workcenter_line, self).write(vals)
        return res


#    @api.multi
#    def write(self, vals):
#        if 'is_date_debut' in vals:
#            vals['date_start']     = str(vals['is_date_debut'])+' 07:00:00'
#            vals['date_finished']  = str(vals['is_date_debut'])+' 16:00:00'
#            vals['is_date_fin']    = vals['is_date_debut']
#        else:
#            if 'date_start' in vals:
#                vals['is_date_debut'] = vals['date_start']
#            if 'date_finished' in vals:
#                vals['is_date_fin'] = vals['date_finished']
#        res=super(mrp_production_workcenter_line, self).write(vals)
#        #** Mise à jour de la date de début des opérations suivantes ***********
#        if 'is_date_debut' in vals:
#            ops = self.env["mrp.production.workcenter.line"].search([('production_id','=',self.production_id.id),('sequence','>',self.sequence)],order='sequence')
#            d = datetime.strptime(self.is_date_debut, '%Y-%m-%d')
#            for op in ops:
#                offset = op.is_offset
#                d = d + timedelta(days=offset)
#                op.is_date_debut = d
#        #***********************************************************************
#        return res


    @api.multi
    def planifier_operation_action(self):
        for obj in self:
            date_debut = False
            if obj.is_date_debut:
                ops = self.env["mrp.production.workcenter.line"].search([('production_id','=',obj.production_id.id),('sequence','>=',obj.sequence)],order='sequence')
                d = datetime.strptime(obj.is_date_debut, '%Y-%m-%d')

                if str(d)[:10]<str(date.today()):
                    d = datetime.now()

                for op in ops:
                    offset = op.is_offset
                    d = d + timedelta(days=offset)
                    dates=[]
                    for line in op.workcenter_id.is_temps_ouverture_ids:
                        dates.append(str(line.date_ouverture))
                    date_debut=False
                    d2=d
                    for x in range(50):
                        if str(d2)[:10] in dates:
                            date_debut = str(d2)[:10]
                            break
                        else:
                            d2 = d2 + timedelta(days=1)
                    if not date_debut:
                        raise Warning(u"Aucune date d'ouverture disponible pour le poste de charge '"+op.workcenter_id.name+u"' et pour le "+d.strftime('%d/%m/%Y'))


                    #date_debut = datetime.strptime(d, '%Y-%m-%d')
                    #date_debut = str(d)[:10]
                    vals={
                        'is_date_debut': date_debut,
                        'is_date_fin'  : date_debut,
                        'date_planned' : str(date_debut) + ' 07:00:00',
                        'date_start'   : str(date_debut) + ' 07:00:00',
                        'date_finished': str(date_debut) + ' 16:00:00',
                    }
                    op.write(vals)
            if date_debut:
                print obj,date_debut
                obj.production_id.is_date_planifiee_fin = date_debut
                if date_debut and obj.production_id.is_date_prevue:
                    print date_debut,obj.production_id.is_date_prevue
                    d1 = datetime.strptime(date_debut, '%Y-%m-%d')
                    d2 = datetime.strptime(obj.production_id.is_date_prevue, '%Y-%m-%d')
                    ecart = (d2-d1).days
                    obj.production_id.is_ecart_date = ecart


class mrp_bom(models.Model):
    """Méthode surchargée pour ajouter le champ is_offset"""
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
        return result, result2


class mrp_routing_workcenter(models.Model):
    _inherit  = 'mrp.routing.workcenter'

    is_offset = fields.Integer('Offset (jour)', help="Offset en jours par rapport à l'opération précédente pour le calcul du planning")


class mrp_workcenter(models.Model):
    _inherit  = 'mrp.workcenter'

    is_temps_ouverture_ids = fields.One2many('is.mrp.workcenter.temps.ouverture', 'workcenter_id', u"Temps d'ouverture")


    @api.multi
    def calculer_charge_action(self):
        cr=self._cr
        for obj in self:
            for line in obj.is_temps_ouverture_ids:
                SQL="""
                    SELECT sum(hour)
                    FROM mrp_production_workcenter_line
                    WHERE workcenter_id="""+str(obj.id)+""" and is_date_debut='"""+str(line.date_ouverture)+"""'
                """
                cr.execute(SQL)
                temps_planifie = 0.0
                for row in cr.fetchall():
                    temps_planifie = row[0] or 0.0
                ecart = line.temps_ouverture - temps_planifie
                charge = 100
                if line.temps_ouverture>0:
                    charge = 100*(temps_planifie / line.temps_ouverture)
                line.temps_planifie = temps_planifie
                line.ecart          = ecart
                line.charge         = charge




#    @api.multi
#    def calcul_charge_action(self):
#        for obj in self:
#            print obj
#            ops = self.env["mrp.production.workcenter.line"].search([('workcenter_id','=',obj.id),('state','in',['draft','pause','startworking'])],order='production_id,sequence')
#            now = str(date.today())
#            print now,type(now)
#            for op in ops:
#                print op.production_id.name,op.sequence,op.is_date_debut,op.is_offset
#                date_debut = False
#                if not op.is_date_debut:
#                    date_debut = now
#                else:
#                    d = datetime.strptime(op.is_date_debut, '%Y-%m-%d')
#                    d = str(d)[:10]
#                    if d<now:
#                        date_debut = now
#                if date_debut:
#                    vals={
#                        'is_date_debut': date_debut,
#                        'is_date_fin'  : date_debut,
#                        'date_planned' : str(date_debut) + ' 07:00:00',
#                        'date_start'   : str(date_debut) + ' 07:00:00',
#                        'date_finished': str(date_debut) + ' 16:00:00',
#                    }
#                    op.write(vals)

#            for i in range(21):
#                vals={
#                    'workcenter_id'  : obj.id,
#                    'date_ouverture' : date_ouverture,
#                    'temps_ouverture': temps_ouverture,
#                }
#                self.env["is.mrp.workcenter.temps.ouverture"].create(vals)
#                date_ouverture = date_ouverture + timedelta(days=1)






class is_mrp_workcenter_temps_ouverture(models.Model):
    _name = "is.mrp.workcenter.temps.ouverture"
    _order = 'workcenter_id,date_ouverture'

    @api.depends('date_ouverture')
    def _compute_date_ouverture(self):
        for obj in self:
            if obj.date_ouverture:
                date_ouverture = datetime.strptime(obj.date_ouverture, '%Y-%m-%d')
                obj.semaine_ouverture = date_ouverture.strftime('%Y')+u'-S'+date_ouverture.strftime('%V')
                obj.mois_ouverture    = date_ouverture.strftime('%Y-%m')


    workcenter_id     = fields.Many2one('mrp.workcenter', 'Poste de charge', required=True, ondelete='cascade', readonly=True)
    date_ouverture    = fields.Date(u"Date d'ouverture"      , required=True, index=True)
    semaine_ouverture = fields.Char(u"Semaine d'ouverture", compute='_compute_date_ouverture', readonly=True, store=True)
    mois_ouverture    = fields.Char(u"Mois d'ouverture"   , compute='_compute_date_ouverture', readonly=True, store=True)
    temps_ouverture   = fields.Float(u"Temps d'ouverture (H)", required=True)
    temps_planifie    = fields.Float(u"Temps planifié (H)", readonly=True)
    ecart             = fields.Float(u"Ecart (H)"         , readonly=True)
    charge            = fields.Float(u"Charge (%)"        , readonly=True)
    operateur_ids     = fields.Many2many('hr.employee', 'is_mrp_workcenter_temps_ouverture_operateur_rel', 'date_id', 'employe_id', u"Opérateurs")






