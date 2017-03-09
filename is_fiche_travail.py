# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp.tools.translate import _

class is_fiche_travail(osv.osv):
    _name='is.fiche.travail'
    _order='name'    #Ordre de tri par defaut des listes
    #_sql_constraints = [('name_uniq','UNIQUE(name)', 'Ce code existe déjà')] 

    _columns={
        'name':fields.date("Date",required=True),
        'ordre_fabrication': fields.many2one('mrp.production', 'Ordre de fabrication', required=True, ondelete='set null'),
        'quantite': fields.integer('Quantité', required=True),
        'commentaire': fields.text('Commentaire'),
    }

is_fiche_travail()



