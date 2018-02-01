# -*- coding: utf-8 -*-

from openerp import models,fields,api


class is_categorie_client(models.Model):
    _name = "is.categorie.client"

    name = fields.Char(string='Catégorie', size=32)



class res_partner(models.Model):
    _inherit = 'res.partner'

    is_code_client         = fields.Char("Code comptable client")
    is_categorie_client_id = fields.Many2one('is.categorie.client', string='Catégorie de client')



