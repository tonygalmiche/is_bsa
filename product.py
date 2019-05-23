# -*- coding: utf-8 -*-

from openerp import models,fields,api
from lxml import etree
import xml.etree.ElementTree as ET
import uuid
import base64
import codecs
import unicodedata


class is_position_dans_produit(models.Model):
    _name = "is.position.dans.produit"
    name = fields.Char(string='Position dans produit', size=32)


class product_template(models.Model):
    _inherit = 'product.template'
    
    is_ce_en1090                 = fields.Boolean(u'CE EN1090', help="Si cette case est cochée, le logo CE 1166 apparaîtra sur le BL")
    is_stock_prevu_valorise      = fields.Float('Stock prévu valorisé'     , store=False, compute='_compute')
    is_stock_disponible_valorise = fields.Float('Stock disponible valorisé', store=False, compute='_compute')
    is_recalcul_prix_revient     = fields.Boolean(u'Recalcul automatique du prix de revient', help="Si cette case est cochée, le prix de revient sera recalculé pendant la nuit")
    is_position_dans_produit_ids = fields.Many2many('is.position.dans.produit','is_position_dans_produit_product_rel','product_id','position_id', string="Position dans produit")
    is_doublon                   = fields.Char('Doublon', store=False, compute='_compute_doublon')
    is_import_par_mail           = fields.Boolean(u'Article importé par mail')


    def message_new(self, cr, uid, msg_dict, custom_values=None, context=None):
        """Méthode provenant par surcharge de mail.tread permettant de personnaliser la création de l'article lors de la réception d'un mail avec le serveur de courrier entrant créé"""
        if context is None:
            context = {}
        data = {}
        if isinstance(custom_values, dict):
            data = custom_values.copy()
        model = context.get('thread_model') or self._name
        model_pool = self.pool[model]
        fields = model_pool.fields_get(cr, uid, context=context)
        if 'name' in fields and not data.get('name'):
            data['name'] = msg_dict.get('subject', '')

        if msg_dict.get('body'):

            #print msg_dict



            filename = '/tmp/product.template-%s.xml' % uuid.uuid4()
            temp = open(filename, 'w+b')
            description = msg_dict.get('body')


            #print description

            #print description.decode('utf-8')
            #print description.decode('iso-8859-1')

            #.decode('iso-8859-1').encode('utf8')


            #description = unicodedata.normalize('NFKD', description).encode('ascii', 'ignore')
            #description = description.decode('cp1252').encode('utf-8')
            #description = description.decode('cp1252')
            #description = description.decode('ascii')
            #description = description.decode('iso8859_15')
            #description = description.decode('utf-8')
            #print type(description)
            #description = description.decode('iso-8859-1').encode('utf8')

            description = description.encode('utf-8')
            temp.write(description)
            temp.close()
            tree = ET.parse(filename)
            root = tree.getroot()
            for n1 in root:
                if n1.tag in fields:
                    #print n1.tag,' : ',n1.text.strip()
                    data[n1.tag] = n1.text.strip()

            data['is_import_par_mail'] = True


        res_id = model_pool.create(cr, uid, data, context=context)
        return res_id


    def _compute_doublon(self):
        for obj in self:
            doublon=False
            products=self.env['product.template'].search([
                ('name', '=' , obj.name),
                ('id'  , '!=', obj.id),
            ])
            ids=[]
            if len(products)>0:
                for product in products:
                    ids.append(str(product.id))
                doublon=u'Doublon Nom : '+', '.join(ids)
            products=self.env['product.template'].search([
                ('default_code', '=' , obj.default_code),
                ('default_code', '!=' , False),
                ('id'  , '!=', obj.id),
            ])
            ids=[]
            if len(products)>0:
                for product in products:
                    ids.append(str(product.id))
                doublon=u'Doublon Référence : '+', '.join(ids)
            p={}
            for line in obj.seller_ids:
                products=self.env['product.supplierinfo'].search([
                    ('product_code'   , '=' , line.product_code),
                    ('product_code'   , '!=', False),
                    ('id'             , '!=', line.id),
                ])
                if len(products)>0:
                    for product in products:
                        if product.product_tmpl_id.active:
                            id=product.product_tmpl_id.id
                            p[id]=id
            ids=[]
            if len(p)>0:
                for id in p:
                    ids.append(str(id))
                doublon=u'Doublon Référence fournisseur : '+', '.join(ids)
            obj.is_doublon=doublon


    def _compute(self):
        for obj in self:
            is_stock_disponible_valorise = 0
            is_stock_prevu_valorise      = 0
            if obj.qty_available > 0:
                is_stock_disponible_valorise = obj.standard_price * obj.qty_available
            if obj.virtual_available > 0:
                is_stock_prevu_valorise = obj.standard_price * obj.virtual_available
            obj.is_stock_disponible_valorise = is_stock_disponible_valorise
            obj.is_stock_prevu_valorise      = is_stock_prevu_valorise


    @api.multi
    def write(self, vals):
        vals = vals or {}
        res=super(product_template, self).write(vals)
        if 'stop_write_recursion' not in self.env.context:
            champs=['name','description','description_purchase','description_sale']
            for champ in champs:
                if vals.get(champ):
                    translatons = self.env["ir.translation"].search([('name','=','product.template,'+champ),('res_id','=',self.id)])
                    for t in translatons:
                        t.with_context(stop_write_recursion=1).write({'source':t.value})
        return res


    @api.multi
    def copy(self,vals):
        for obj in self:
            res=super(product_template, self).copy(vals)
            for line in obj.seller_ids:
                v = {
                    'product_tmpl_id': res.id,
                    'name'      : line.name.id,
                }
                id = self.env['product.supplierinfo'].create(v)
            return res


    @api.multi
    def recalcul_prix_revient_action(self):
        cr , uid, context = self.env.args
        prod_obj = self.pool.get('product.template')
        for obj in self:
            if obj.cost_method=='standard' and obj.is_recalcul_prix_revient:
                res=prod_obj.compute_price(cr, uid, [], template_ids=[obj.id], real_time_accounting=False, recursive=True, test=False, context=context)


