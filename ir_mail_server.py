# -*- coding: utf-8 -*-
from openerp import api, fields, models


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"


    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None, smtp_debug=False):
        cc=''

        #print self, 'email_cc = ',message['email_cc']

        if message['From']:
            cc=message['From']
#        if not message['Cc']:
#            message['Cc'] = cc
#        else:
#            mem = message['Cc']
#            del message['Cc']
#            message['Cc'] = mem + "," + cc
        message['Cc'] = cc
        #message['Bcc'] = cc


        #for key in message:
        #    print 'IrMailServer : send_email',key
        #print 'IrMailServer : email_cc=',message['email_cc']


        res = super(IrMailServer, self).send_email(message, mail_server_id, smtp_server, smtp_port,
                   smtp_user, smtp_password, smtp_encryption, smtp_debug)


        #print '##copy : ',res,cc

        return res


