# -*- coding: utf-8 -*-
from openerp import models,fields,api
from openerp.tools.translate import _
import datetime
from openerp.exceptions import Warning
import unicodedata


def s(txt,lg):
    if type(txt)!=unicode:
        txt = unicode(txt,'utf-8')
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore')
    txt = (txt+u'                                                             ')[:lg]
    return txt


class is_export_compta(models.Model):
    _name='is.export.compta'
    _order='name desc'

    name               = fields.Char("N°Folio"      , readonly=True)
    type_interface     = fields.Selection([('ventes', u'Ventes'),('achats', u'Achats')], "Interface"    , required=True)
    format_export      = fields.Selection([('cegid' , u'CEGID'),('ledonia', u'Cabinet LEDONIA EXPERTISE')], "Format export", required=True)
    date_debut         = fields.Date("Date de début")
    date_fin           = fields.Date("Date de fin")
    num_debut          = fields.Char("N° facture début")
    num_fin            = fields.Char("N° facture fin")
    ligne_ids          = fields.One2many('is.export.compta.ligne', 'export_compta_id', u'Lignes')

    _defaults = {
        'type_interface':  'ventes',
        'format_export' :  'ledonia',
    }


    @api.model
    def create(self, vals):
        data_obj = self.env['ir.model.data']
        sequence_ids = data_obj.search([('name','=','is_export_compta_seq')])
        if sequence_ids:
            sequence_id = data_obj.browse(sequence_ids[0].id).res_id
            vals['name'] = self.env['ir.sequence'].get_id(sequence_id, 'id')
        res = super(is_export_compta, self).create(vals)
        return res


    @api.multi
    def action_export_compta(self):
        cr=self._cr
        for obj in self:
            obj.ligne_ids.unlink()
            if obj.type_interface=='ventes':
                type_facture=['out_invoice', 'out_refund']
                journal='VE'
            else:
                type_facture=['in_invoice', 'in_refund']
                journal='AC'
            filter=[
                ('state'       , 'in' , ['open','paid']),
                ('type'        , 'in' , type_facture)
            ]
            if obj.date_debut:
                filter.append(('date_invoice', '>=', obj.date_debut))
            if obj.date_fin:
                filter.append(('date_invoice', '<=', obj.date_fin))
            if obj.num_debut:
                filter.append(('number', '>=', obj.num_debut))
            if obj.num_fin:
                filter.append(('number', '<=', obj.num_fin))
            invoices = self.env['account.invoice'].search(filter, order="date_invoice,id")
            if len(invoices)==0:
                raise Warning('Aucune facture à traiter')
            for invoice in invoices:
                sql="""
                    SELECT  
                        ai.date_invoice,
                        aa.code, 
                        ai.number, 
                        rp.name, 
                        ai.type, 
                        rp.is_code_client,
                        sum(aml.debit), 
                        sum(aml.credit),
                        rp.id partner_id 
                    FROM account_move_line aml inner join account_invoice ai             on aml.move_id=ai.move_id
                                               inner join account_account aa             on aml.account_id=aa.id
                                               inner join res_partner rp                 on ai.partner_id=rp.id
                    WHERE ai.id="""+str(invoice.id)+"""
                    GROUP BY ai.date_invoice, ai.number, rp.id, rp.name, aa.code, ai.type, rp.is_code_client, ai.date_due, rp.supplier
                    ORDER BY ai.date_invoice, ai.number, rp.id, rp.name, aa.code, ai.type, rp.is_code_client, ai.date_due, rp.supplier
                """
                cr.execute(sql)
                for row in cr.fetchall():
                    compte=str(row[1])
                    if obj.type_interface=='ventes' and compte=='411100':
                        compte=str(row[5])
                    vals={
                        'export_compta_id'  : obj.id,
                        'date_facture'      : row[0],
                        'journal'           : journal,
                        'compte'            : compte,
                        'libelle'           : row[3],
                        'debit'             : row[6],
                        'credit'            : row[7],
                        'devise'            : 'E',
                        'piece'             : row[2],
                        'commentaire'       : False,
                        'partner_id'        : row[8],

                    }
                    self.env['is.export.compta.ligne'].create(vals)
            if obj.format_export=='cegid':
                self.generer_fichier_cegid()
            else:
                self.generer_fichier_ledonia()


    def generer_fichier_cegid(self):
        for obj in self:
            model='is.export.compta'
            attachments = self.env['ir.attachment'].search([('res_model','=',model),('res_id','=',obj.id)])
            attachments.unlink()
            name='export-compta.txt'
            dest     = '/tmp/'+name
            f = open(dest,'wb')
            for row in obj.ligne_ids:
                compte=str(row.compte)
                if compte=='None':
                    compte=''
                debit=row.debit
                credit=row.credit
                montant=credit-debit
                if montant>0.0:
                    sens='C'
                else:
                    montant=-montant
                    sens='D'
                montant=(u'000000000000'+str(int(round(100*montant))))[-12:]
                date_facture=row.date_facture
                date_facture=datetime.datetime.strptime(date_facture, '%Y-%m-%d')
                date_facture=date_facture.strftime('%d%m%y')
                libelle=s(row.libelle,20)
                piece=(row.piece[-8:]+u'        ')[0:8]
                f.write('M')
                f.write((compte+u'00000000')[0:8])
                f.write(row.journal)
                f.write('000')
                f.write(date_facture)
                f.write('F')
                f.write(libelle)
                f.write(sens)
                f.write('+')
                f.write(montant)
                f.write('        ')
                f.write('000000')
                f.write('     ')
                f.write(piece)
                f.write('                 ')
                f.write(piece)
                f.write('EURVE    ')
                f.write(libelle)
                f.write('\r\n')
            f.close()
            r = open(dest,'rb').read().encode('base64')
            vals = {
                'name':        name,
                'datas_fname': name,
                'type':        'binary',
                'res_model':   model,
                'res_id':      obj.id,
                'datas':       r,
            }
            id = self.env['ir.attachment'].create(vals)


    def generer_fichier_ledonia(self):
        for obj in self:
            name='export-compta.csv'
            model='is.export.compta'
            attachments = self.env['ir.attachment'].search([('res_model','=',model),('res_id','=',obj.id),('name','=',name)])
            attachments.unlink()
            dest     = '/tmp/'+name
            f = open(dest,'wb')

            f.write("ligne\tjournal_code\tecriture_num\tecriture_date\tcompte_num\tcomp_aux_num\tpiece_ref\tpiece_date\tecriture_lib\tdebit\tcredit\r\n")
            ligne=1
            for row in obj.ligne_ids:
                date_facture = row.date_facture
                date_facture = datetime.datetime.strptime(date_facture, '%Y-%m-%d')
                date_facture=date_facture.strftime('%Y%m%d')
                f.write(str(ligne)+'\t')
                f.write(row.journal+'\t')
                f.write(row.piece+'\t')
                f.write(date_facture+'\t')
                f.write(row.compte+'\t')
                f.write((row.partner_id.is_code_client or '')+'\t')
                f.write(row.piece+'\t')
                f.write(date_facture+'\t')
                f.write(row.libelle+'\t')
                f.write(str(row.debit).replace('.','.')+'\t')
                f.write(str(row.credit).replace('.','.')+'\t')
                f.write('\r\n')
                ligne+=1
            f.close()
            r = open(dest,'rb').read().encode('base64')
            vals = {
                'name':        name,
                'datas_fname': name,
                'type':        'binary',
                'res_model':   model,
                'res_id':      obj.id,
                'datas':       r,
            }
            attachment = self.env['ir.attachment'].create(vals)
            obj.file_ids=[(6,0,[attachment.id])]


class is_export_compta_ligne(models.Model):
    _name = 'is.export.compta.ligne'
    _description = u"Lignes d'export en compta"
    _order='date_facture'

    export_compta_id = fields.Many2one('is.export.compta', 'Export Compta', required=True)
    date_facture     = fields.Date("Date")
    journal          = fields.Char("Journal")
    compte           = fields.Char("N°Compte")
    piece            = fields.Char("Pièce")
    libelle          = fields.Char("Libellé")
    debit            = fields.Float("Débit")
    credit           = fields.Float("Crédit")
    devise           = fields.Char("Devise")
    commentaire      = fields.Char("Commentaire")
    partner_id       = fields.Many2one('res.partner', u'Partenaire')

    _defaults = {
        'journal': 'VTE',
        'devise' : 'E',
    }







