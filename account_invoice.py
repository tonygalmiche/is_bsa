# -*- coding: utf-8 -*-

from openerp import models,fields,api
from openerp.tools.translate import _



class account_invoice(models.Model):
    _inherit = "account.invoice"

    is_acompte = fields.Float("Acompte")


class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"
    _order='is_stock_move_id,sequence,id'

    is_stock_move_id = fields.Many2one('stock.move', string='Stock Move')
