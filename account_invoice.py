# -*- coding: utf-8 -*-

from openerp import models,fields,api
from openerp.tools.translate import _



class is_mode_reglement(models.Model):
    _name = "is.mode.reglement"
    name = fields.Char(string='Mode de règlement')


class account_invoice(models.Model):
    _inherit = "account.invoice"
    _order = "create_date desc"

    def _alerte_acompte(self):
        for obj in self:

            ids=[]
            for line in obj.invoice_line:
                id=line.is_stock_move_id.picking_id.sale_id.id
                if id and id not in ids:
                    ids.append(id)
            print ids

            invoices=self.env['account.invoice'].search([
                ('is_sale_order_id', 'in' , ids),
                ('is_account_invoice_id', '=', False),
                ('state','not in', ['draft','cancel']),
            ])
            print ids,invoices
            alerte = False
            if invoices:
                alerte = u"ATTENTION : L'acompte "+str(invoices[0].number)+u" sur la commande "+str(invoices[0].is_sale_order_id.name)+u" n'a pas été traité"




            obj.is_alerte_acompte = alerte


    is_acompte               = fields.Float("Acompte")
    is_imputation_partenaire = fields.Char("Imputation partenaire")
    is_contact_id            = fields.Many2one('res.partner', string='Contact')
    is_mode_reglement_id     = fields.Many2one('is.mode.reglement', string='Mode de règlement')
    is_sale_order_id         = fields.Many2one('sale.order', string=u"Facture d'acompte sur la commande")
    is_account_invoice_id    = fields.Many2one('account.invoice', string=u"Acompte traité sur la facture")
    is_alerte_acompte        = fields.Char("Alerte acompte", store=False, compute='_alerte_acompte')


    @api.multi
    def name_get(self):
        res=[]
        for obj in self:
            name=obj.number or ''
            res.append((obj.id, name))
        return res


    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            filtre=['|',('name','ilike', name),('internal_number','ilike', name)]
            ids = self.search(cr, user, filtre, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result


class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"
    _order='is_stock_move_id,sequence,id'

    is_stock_move_id = fields.Many2one('stock.move', string='Stock Move')
