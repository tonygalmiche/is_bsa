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
    def action_creer_etiquette_mrp(self):
        for obj in self:
            tracab_obj = self.env['is.tracabilite.livraison']
            res = []
            etiquettes=""
            if obj.product_qty:
                qty = obj.product_qty
                lot=1
                if obj.product_id.is_gestion_lot:
                    lot=qty
                while ( qty >= 1):
                    vals = {
                        'production_id': obj.id,
                        'quantity': 1.0,
                        'lot_fabrication': lot,
                    }
                    new_id = tracab_obj.create(vals)
                    qty = qty - lot
                obj.generer_etiquette=True


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
    #_order = "production_id desc, sequence"

    @api.depends('is_temps_passe_ids')
    def compute_temps_passe(self):
        for obj in self:
            temps_passe = 0
            ecart = 0
            for line in obj.is_temps_passe_ids:
                temps_passe+=line.temps_passe
            obj.is_temps_passe = temps_passe
            obj.is_ecart       = obj.hour - temps_passe


    @api.depends('is_date_debut')
    def compute_charge(self):
        for obj in self:
            lines = self.env["is.mrp.workcenter.temps.ouverture"].search([('workcenter_id','=',obj.workcenter_id.id),('date_ouverture','=',obj.is_date_debut)])
            charge = 0
            for line in lines:
                charge = line.charge
            obj.is_charge = charge


    @api.depends('production_id')
    def compute_product_id(self):
        for obj in self:
            obj.is_product_id = obj.production_id.product_id.id


    is_product_id      = fields.Many2one('product.product', u'Article', compute='compute_product_id', readonly=True, store=True)
    is_commentaire     = fields.Text('Commentaire')
    is_temps_passe_ids = fields.One2many('is.workcenter.line.temps.passe'  , 'workcenter_line_id', u"Temps passé")
    is_temps_passe     = fields.Float('Temps passé', compute='compute_temps_passe', readonly=True, store=True)
    is_ecart           = fields.Float('Ecart', compute='compute_temps_passe', readonly=True, store=True)
    is_offset          = fields.Integer('Offset (jour)', help="Offset en jours par rapport à l'opération précédente pour le calcul du planning")
    is_date_debut      = fields.Date(u'Date de début opération', index=True)
    is_date_fin        = fields.Date(u'Date de fin opération')

    is_date_prevue_cde    = fields.Date(u'Date prévue commande client', related='production_id.is_date_prevue'    , readonly=True)
    is_date_planifiee_fin = fields.Date(u'Date planifiée fin'         , related='production_id.is_date_planifiee_fin', readonly=True)
    is_ecart_date         = fields.Integer(u'Ecart date'              , related='production_id.is_ecart_date'        , readonly=True)
    is_charge             = fields.Float(u"Charge (%)"         , compute='compute_charge', readonly=True, store=False, help="Charge pour la date de début de l'opération")


#    @api.multi
#    def write(self, vals):
#        if 'date_start' in vals and 'is_date_debut' not in vals:
#            vals['is_date_debut'] = vals['date_start']
#        if 'date_finished' in vals and 'is_date_fin' not in vals:
#            vals['is_date_fin'] = vals['date_finished']

#        print vals
#        if 'is_date_debut' in vals:
#            print 'TEST'

#        res=super(mrp_production_workcenter_line, self).write(vals)
#        return res


    @api.multi
    def write(self, vals, update=True):
        if len(vals)==2 and 'date_finished' in vals and 'date_start' in vals:
            d = datetime.strptime(vals['date_start'], '%Y-%m-%d %H:%M:%S')
            vals['is_date_debut'] =  str(d)[:10]
            #offset = op.is_offset
            #d = d + timedelta(days=offset)
            if self.is_offset:
                offset = self.is_offset
                d = d + timedelta(days=offset)
            vals['is_date_fin'] =  str(d)[:10]




        res=super(mrp_production_workcenter_line, self).write(vals, update=update)


        if 'is_date_debut' in vals:
            #print 'TEST',res,self
            #self.planifier_operation_action()
            self.workcenter_id.calculer_charge_action()
            #ops = self.env["mrp.production.workcenter.line"].search([('production_id','=',obj.production_id.id),('state','in',['draft','pause','startworking'])],order='production_id,sequence')
            #    if ops:
            #        ops[0].is_date_debut = obj.is_date_planifiee
            #        ops[0].planifier_operation_action()



        return res



#    def write(self, cr, uid, ids, vals, context=None, update=True):
#        direction = {}
#        if vals.get('date_start', False):
#            for po in self.browse(cr, uid, ids, context=context):
#                direction[po.id] = cmp(po.date_start, vals.get('date_start', False))

#        #print vals

#        result = super(mrp_production, self).write(cr, uid, ids, vals, context=context)
#        if (vals.get('workcenter_lines', False) or vals.get('date_start', False) or vals.get('date_planned', False)) and update:
#            self._compute_planned_workcenter(cr, uid, ids, context=context, mini=mini)
#        for d in direction:
#            if direction[d] == 1:
#                # the production order has been moved to the passed
#                self._move_pass(cr, uid, [d], context=context)
#                pass
#            elif direction[d] == -1:
#                self._move_futur(cr, uid, [d], context=context)
#                # the production order has been moved to the future
#                pass
#        return result



#{'date_finished': '2020-09-05 16:00:00', 'date_start': '2020-09-05 07:00:00'}



    @api.multi
    def planifier_operation_action(self):
        for obj in self:
            date_debut = False
            date_fin=False
            if obj.is_date_debut:
                filtre=[
                    ('production_id','=',obj.production_id.id),
                    ('sequence','>',obj.sequence),
                    ('id','!=',obj.id),
                ]
                ops = self.env["mrp.production.workcenter.line"].search(filtre,order='sequence')
                d = datetime.strptime(obj.is_date_debut, '%Y-%m-%d')
                if str(d)[:10]<str(date.today()):
                    d = datetime.now()
                for op in ops:
                    date_debut = str(d)[:10]
                    offset = op.is_offset
                    d = d + timedelta(days=offset)
                    dates=[]
                    for line in op.workcenter_id.is_temps_ouverture_ids:
                        dates.append(str(line.date_ouverture))
                    date_fin=False
                    d2=d
                    for x in range(50):
                        if str(d2)[:10] in dates:
                            date_fin = str(d2)[:10]
                            break
                        else:
                            d2 = d2 + timedelta(days=1)
                    if not date_fin:
                        raise Warning(u"Aucune date d'ouverture disponible pour le poste de charge '"+op.workcenter_id.name+u"' et pour le "+d.strftime('%d/%m/%Y'))
                    d=d2
                    vals={
                        'is_date_debut': date_debut,
                        'is_date_fin'  : date_fin,
                        #'date_planned' : str(date_debut) + ' 07:00:00', #TODO : La mise à jour de ce champ est trép long
                        'date_start'   : str(date_debut) + ' 07:00:00',
                        'date_finished': str(date_debut) + ' 16:00:00',
                    }
                    op.write(vals)


            if date_fin:
                obj.production_id.is_date_planifiee_fin = date_fin
                if date_fin and obj.production_id.is_date_prevue:
                    d1 = datetime.strptime(date_fin, '%Y-%m-%d')
                    d2 = datetime.strptime(obj.production_id.is_date_prevue, '%Y-%m-%d')
                    ecart = (d2-d1).days
                    obj.production_id.is_ecart_date = ecart


class mrp_bom(models.Model):
    """Méthode surchargée pour ajouter le champ is_offset"""
    _inherit  = 'mrp.bom'
    _order    = 'product_tmpl_id'
    #_rec_name = 'product_tmpl_id'
    _rec_name = 'name'

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
                    WHERE 
                        workcenter_id="""+str(obj.id)+""" and 
                        is_date_debut='"""+str(line.date_ouverture)+"""' and
                        state not in ('cancel','done')
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



    @api.multi
    def acceder_ordres_travaux(self):
        for obj in self:
            return {
                'name': u'travaux '+obj.workcenter_id.name+u' '+str(obj.date_ouverture),
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'mrp.production.workcenter.line',
                'domain': [
                    ('workcenter_id','=',obj.workcenter_id.id),
                    ('is_date_debut','=',obj.date_ouverture),
                    ('state','not in', ['cancel','done']),
                ],
                'type': 'ir.actions.act_window',
            }








