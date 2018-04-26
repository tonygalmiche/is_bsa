# -*- coding: utf-8 -*-

from openerp import models,fields,api
from openerp.tools.translate import _


class res_company(models.Model):
    _inherit = 'res.company'

    is_site = fields.Selection([
        ('bsa'     , 'BSA'),
        ('bressane'      , 'Bressane'),
    ], "Site", default='bsa', help="Champ utilisé pour diférencier les sites de production (ex : CGV)")


