# -*- coding: utf-8 -*-

from openerp.osv import fields, osv

class product_product(osv.osv):
    _inherit = 'product.template'
    
    _columns = {
        'is_ce_en1090': fields.boolean(u'CE EN1090', help="Si cette case est cochée, le logo CE 1166 apparaîtra sur le BL"),
    }
