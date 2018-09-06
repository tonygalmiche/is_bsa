# -*- coding: utf-8 -*-

from openerp import models,fields,api
from openerp.tools.translate import _



class is_mode_reglement(models.Model):
    _name = "is.mode.reglement"
    name = fields.Char(string='Mode de règlement')


class account_invoice(models.Model):
    _inherit = "account.invoice"

    is_acompte               = fields.Float("Acompte")
    is_imputation_partenaire = fields.Char("Imputation partenaire")
    is_contact_id            = fields.Many2one('res.partner', string='Contact')
    is_mode_reglement_id     = fields.Many2one('is.mode.reglement', string='Mode de règlement')


class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"
    _order='is_stock_move_id,sequence,id'

    is_stock_move_id = fields.Many2one('stock.move', string='Stock Move')
