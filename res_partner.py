# -*- coding: utf-8 -*-

from openerp import models,fields,api


class res_partner(models.Model):
    _inherit = 'res.partner'

    is_code_client = fields.Char("Code comptable client")

