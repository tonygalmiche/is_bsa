# -*- coding: utf-8 -*-

from openerp import models,fields,api
from openerp.tools.translate import _


class purchase_order_line(models.Model):
    _inherit = "purchase.order.line"
    _order = "is_sequence,id"

    is_sequence = fields.Integer('Séquence')
    is_date_ar  = fields.Date("Date AR")


class purchase_order(models.Model):
    _inherit = "purchase.order"

    is_a_commander = fields.Boolean(u"A commander", default=False)
    is_arc         = fields.Boolean(u"ARC reçu"   , default=False)

    @api.multi
    def mouvement_stock_action(self):
        for obj in self:
            ids=[]
            for picking in obj.picking_ids:
                for line in picking.move_lines:
                    ids.append(line.id)
            if not ids:
                raise Warning(u'Aucune ligne de réception')
            else:
                return {
                    'name': u'Lignes de réception '+obj.name,
                    'view_mode': 'tree,form',
                    'view_type': 'form',
                    'res_model': 'stock.move',
                    'domain': [
                        ('id','in',ids),
                    ],
                    'type': 'ir.actions.act_window',
                }



    #TODO : J'ai surchargé cette fonction le 28/11/19, car le modèle de mail de la demande de prix a été supprimée
    def wkf_send_rfq(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        if not context:
            context= {}
        ir_model_data = self.pool.get('ir.model.data')
        try:
            if context.get('send_rfq', False):
                template_id = ir_model_data.get_object_reference(cr, uid, 'is_bsa', 'is_demande_de_prix_email_template')[1]
            else:
                template_id = ir_model_data.get_object_reference(cr, uid, 'purchase', 'email_template_edi_purchase_done')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False 
        ctx = dict(context)
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
