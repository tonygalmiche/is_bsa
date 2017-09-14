# -*- coding: utf-8 -*-
from openerp import models,fields,api
from openerp.tools.translate import _
from openerp.exceptions import Warning
import base64


def str2int(s):
    try:
        return int(s)
    except ValueError:
        return 0


class is_import_nomenclature(models.Model):
    _name='is.import.nomenclature'
    _order='name'
    _sql_constraints = [('name_uniq','UNIQUE(name)', 'Ce code existe déjà')]

    name     =  fields.Many2one('product.template', 'Article', domain="[('type', '!=', 'service')]", required=True)
    bom_id   =  fields.Many2one('mrp.bom', 'Nomenclature', readonly=True)
    resultat =  fields.Text("Résultat de l'importation", readonly=True)

    @api.multi
    def action_import_nomenclature(self):
        for obj in self:
            boms=self.env['mrp.bom'].search([('product_tmpl_id', '=', obj.name.id)])
            if len(boms)>0:
                raise Warning("Il existe déja une nomenclature par cet article")
            model='is.import.nomenclature'
            attachments = self.env['ir.attachment'].search([('res_model','=',model),('res_id','=',obj.id)])
            err=[]
            for attachment in attachments:
                vals = {
                    'product_tmpl_id': obj.name.id,
                    'name'           : obj.name.name,
                }
                bom_id = self.env['mrp.bom'].create(vals)
                csv=base64.decodestring(attachments.datas)
                rows=csv.split("\r\n")
                lig=0
                for row in rows:
                    if lig:
                        cols=row.split(",")
                        if len(cols)>2:
                            test=True
                            product_tmpl_id=str2int(cols[1])
                            if product_tmpl_id:
                                products = self.env['product.product'].search([('product_tmpl_id','=',product_tmpl_id)])
                                for product in products:
                                    test=False
                                    vals={
                                        'bom_id'     : bom_id.id,
                                        'sequence'   : cols[0],
                                        'product_id' : product.id,
                                        'product_qty': cols[2],
                                    }
                                    line_id = self.env['mrp.bom.line'].create(vals)
                                    err.append(u'OK : '+cols[2]+u' x '+product.name)
                            if test:
                                err.append(u'ERR : Composant '+cols[2]+u' (id='+(cols[1] or u'')+u') non trouvé ('+cols[3].decode('latin-1')+u')')
                    lig=lig+1
            obj.bom_id=bom_id.id
            obj.resultat='\n'.join(err)

