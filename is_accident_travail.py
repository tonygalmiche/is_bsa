# -*- coding: utf-8 -*-

from openerp import models,fields,api
from openerp.tools.translate import _
from openerp.exceptions import Warning
import datetime


class is_accident_travail(models.Model):
    _name='is.accident.travail'
    _inherit = ['mail.thread']
    _order='name desc'

    name            = fields.Char("N°", readonly=True)
    createur_id     = fields.Many2one('res.users', 'Créateur', required=True)
    date_creation   = fields.Date("Date de création", required=True)
    type_accident   = fields.Selection([
                        ('sans_visite_medecin', 'Sans visite de médecin et sans arrêt'),
                        ('sans_visite_medecin', 'Visite de médecin et sans arrêt'),
                        ('avec_arret_travail' , 'Avec arrêt de travail'),
                        ('amelioration'       , 'Amélioration'),
                    ], "Type", required=True)
    employe_id          = fields.Many2one('hr.employee', 'Employé')
    description         = fields.Text("Description du problème")
    individu            = fields.Text("L'individu")
    tache               = fields.Text("La tache")
    materiel            = fields.Text("Le matériel")
    milieu              = fields.Text("Le milieu")
    resolution          = fields.Text("Résolution")
    evaluation          = fields.Text("Évaluation")
    date_evaluation     = fields.Date("Date évaluation")
    evaluateur_id       = fields.Many2one('res.users', 'Evaluateur')
    attachment_ids      = fields.Many2many('ir.attachment', 'bsa_fnc_attachment_rel', 'bsa_fnc_id', 'attachment_id', u'Pièces jointes')
    state               = fields.Selection([
                        ('ouverte', 'Ouverte'),
                        ('encours', 'En cours'),
                        ('fermee' , 'Fermée'),
                    ], "État")


    def _date_creation():
        now = datetime.date.today()     # Date du jour
        return now.strftime('%Y-%m-%d') # Formatage

    _defaults = {
        'state'        : 'ouverte',
        'date_creation':  _date_creation(),
        'createur_id'  : lambda obj, cr, uid, ctx=None: uid,
    }


    @api.model
    def create(self, vals):

        #** Numérotation *******************************************************
        data_obj = self.env['ir.model.data']
        sequence_ids = data_obj.search([('name','=','is_accident_travail_seq')])
        if sequence_ids:
            sequence_id = sequence_ids[0].res_id
            vals['name'] = self.env['ir.sequence'].get_id(sequence_id, 'id')
        obj = super(is_accident_travail, self).create(vals)
        #***********************************************************************
        return obj


