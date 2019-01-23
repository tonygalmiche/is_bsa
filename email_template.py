#-*- coding:utf-8 -*-

from openerp import models, fields, api, _
from openerp.tools import frozendict


class ir_attachment_selection(models.TransientModel):
    _name = 'ir.attachment.selection'
    
    directory_id       = fields.Many2one('document.directory','Répertoire')
    attachment_ids     = fields.Many2many('ir.attachment','attachment_selection_rel','selection_id','attachment_id',string='Document')
    compose_message_id = fields.Many2one('mail.compose.message','Message Id')
 
class mail_compose_message(models.TransientModel):
    _inherit = 'mail.compose.message'
     
    attachment_selection_ids = fields.One2many('ir.attachment.selection','compose_message_id','Document')

    @api.multi
    def send_mail(self):
        context=self._context
        attachment_ids = self.env['ir.attachment'].browse()
        for message in self:
            for selection in message.attachment_selection_ids:
                attachment_ids += selection.attachment_ids
            message.attachment_ids = message.attachment_ids | attachment_ids
        res=super(mail_compose_message, self).send_mail()

        #** Permet de supprimer les abonnés du document après l'envoi du mail **
        model=context.get('active_model')
        active_id=context.get('active_id')
        if model and active_id:
            obj = self.env[model].browse(active_id)
            if obj:
                obj.message_follower_ids=[(6,0,[])]
        #***********************************************************************

        return res
