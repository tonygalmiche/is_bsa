# -*- coding: utf-8 -*-
from openerp import models,fields,api
import datetime


class is_fiche_controle(models.Model):
    _name='is.fiche.controle'
    _description = u"Fiche contrôle"
    _order='name desc'

    name               = fields.Char("Fiche", readonly=True)
    type_fiche         = fields.Selection([('interne', u'Interne'),('cient', u'Client')], "Type de fiche", required=True)
    product_id         = fields.Many2one('product.product', 'Article', required=True)
    date_creation      = fields.Date("Date de création"              , required=True)
    createur_id        = fields.Many2one('res.users', 'Créateur'     , required=True)
    ligne_ids          = fields.One2many('is.fiche.controle.ligne', 'fiche_id', u'Lignes')


    _defaults = {
        'date_creation':  datetime.date.today(),
        'createur_id': lambda obj, cr, uid, context: uid,
    }


    @api.model
    def create(self, vals):
        data_obj = self.env['ir.model.data']
        sequence_ids = data_obj.search([('name','=','is_fiche_controle_seq')])
        if sequence_ids:
            sequence_id = data_obj.browse(sequence_ids[0].id).res_id
            vals['name'] = self.env['ir.sequence'].get_id(sequence_id, 'id')
        res = super(is_fiche_controle, self).create(vals)
        return res


    @api.onchange('type_fiche')
    def _onchange_type_fiche(self):
        if self.type_fiche:
            lignes = []
            points = self.env['is.fiche.controle.point'].search([])
            for point in points:
                lignes.append((0, 0, {
                    'point': point.name,
                }))
            self.ligne_ids = lignes





class is_fiche_controle_ligne(models.Model):
    _name = 'is.fiche.controle.ligne'
    _description = u"Lignes fiche contrôle"

    fiche_id = fields.Many2one('is.fiche.controle', 'Fiche', required=True, ondelete='cascade')
    point          = fields.Char("Point à contrôler")
    conforme       = fields.Selection([('oui', u'Oui'),('non', u'Non')], "Conforme", required=True)
    action_corrective = fields.Text("Si non, action corrective")


class is_fiche_controle_point(models.Model):
    _name = 'is.fiche.controle.point'
    _description = u"Points à contrôler"
    _order='ordre'

    name  = fields.Char("Point à contrôler", required=True)
    ordre = fields.Integer("Ordre")







