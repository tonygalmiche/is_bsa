# -*- coding: utf-8 -*-

from openerp import models,fields,api


class account_move_line(models.Model):
    _inherit = "account.move.line"

    @api.depends('debit','credit')
    def _compute_is_solde(self):
        for obj in self:
            obj.is_solde = obj.credit - obj.debit

    is_solde = fields.Float("Solde", store=True, readonly=True, compute='_compute_is_solde')
