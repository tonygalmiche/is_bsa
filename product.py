# -*- coding: utf-8 -*-

from openerp import models,fields,api
from lxml import etree
import xml.etree.ElementTree as ET
import uuid
import base64
import codecs
import unicodedata
import os
import time



class is_position_dans_produit(models.Model):
    _name = "is.position.dans.produit"
    name = fields.Char(string='Position dans produit', size=32)


class product_template(models.Model):
    _inherit = 'product.template'
    
    is_ce_en1090                 = fields.Boolean(u'CE EN1090', help="Si cette case est cochée, le logo CE 1166 apparaîtra sur le BL")
    is_numero_certificat         = fields.Char(u'Numéro du certificat',help=u"Numéro du certificat associé au logo CE 1166",default="1166-CPR-0258")
    is_stock_prevu_valorise      = fields.Float('Stock prévu valorisé'     , store=False, compute='_compute')
    is_stock_disponible_valorise = fields.Float('Stock disponible valorisé', store=False, compute='_compute')
    is_recalcul_prix_revient     = fields.Boolean(u'Recalcul automatique du prix de revient', help="Si cette case est cochée, le prix de revient sera recalculé pendant la nuit")
    is_position_dans_produit_ids = fields.Many2many('is.position.dans.produit','is_position_dans_produit_product_rel','product_id','position_id', string="Position dans produit")
    is_doublon                   = fields.Char('Doublon', store=False, compute='_compute_doublon')
    is_import_par_mail           = fields.Boolean(u'Article importé par mail')
    is_masse_tole                = fields.Float(u'Masse tôle')




    # x : Position x à partir de la gauche
    # y : Position y à partir du bas (entre 0 et 200)
    # sizex : Taille X des caractères (1 à 9)
    # sizey : Taille Y des caractères (1 à 9)
    def datamax(self,sizex, sizey, y, x, txt):
        sizex="0"+str(sizex)
        sizex=sizex[-1:]

        sizey="0"+str(sizey)
        sizey=sizey[-1:]

        x="0000"+str(x)
        x=x[-4:]

        y="0000"+str(y)
        y=y[-4:]

        r="10"+sizex+sizey+"000"+y+x+txt+chr(10)
        return r






    @api.multi
    def generer_etiquette(self):
        for obj in self:
            txt=""
            txt=txt+chr(2)+"qC"+chr(10)
            txt=txt+chr(2)+"qC"+chr(10)
            txt=txt+chr(2)+"n"+chr(10)
            txt=txt+chr(2)+"e"+chr(10)
            txt=txt+chr(2)+"c0000"+chr(10)
            txt=txt+chr(2)+"Kf0000"+chr(10)
            txt=txt+chr(2)+"V0"+chr(10)
            txt=txt+chr(2)+"M0591"+chr(10)
            txt=txt+chr(2)+"L"+chr(10)
            txt=txt+"A2"+chr(10)
            txt=txt+"D11"+chr(10)
            txt=txt+"z"+chr(10)
            txt=txt+"PG"+chr(10)
            txt=txt+"SG"+chr(10)
            txt=txt+"pC"+chr(10)
            txt=txt+"H20"+chr(10)


            name1=""
            name2=""
            name3=""
            name1=obj.name[0:30]
            if len(obj.name)>30:
                name2=obj.name[30:60]
            if len(obj.name)>60:
                name3=obj.name[60:]

            txt=txt+self.datamax(x=15,y=200,sizex=2,sizey=2,txt="ARTICLE:")
            txt=txt+self.datamax(x=15,y=180,sizex=3,sizey=4,txt=name1.encode("utf-8"))
            txt=txt+self.datamax(x=15,y=155,sizex=3,sizey=4,txt=name2.encode("utf-8"))
            txt=txt+self.datamax(x=15,y=130,sizex=3,sizey=4,txt=name3.encode("utf-8"))



            txt=txt+self.datamax(x=15,y=110,sizex=2,sizey=2,txt="FOURNISSEUR:")
            for line in obj.seller_ids:
                fournisseur=line.name.name
                txt=txt+self.datamax(x=15,y=90,sizex=4,sizey=4,txt=fournisseur.encode("utf-8"))
                break

            now=time.strftime('%Y-%m-%d',time.gmtime())
            txt=txt+self.datamax(x=15,y=70,sizex=2,sizey=2,txt="DATE:")
            txt=txt+self.datamax(x=15,y=50,sizex=4,sizey=4,txt=now)

            txt=txt+self.datamax(x=250,y=70,sizex=2,sizey=2,txt="ID:")
            txt=txt+self.datamax(x=250,y=50,sizex=4,sizey=4,txt=str(obj.id))

            txt=txt+self.datamax(x=15,y=30,sizex=2,sizey=2,txt="REFERENCE:")
            txt=txt+self.datamax(x=15,y=10 ,sizex=4,sizey=4,txt=obj.default_code.encode("utf-8"))

            txt=txt+"^01"+chr(10)
            txt=txt+"Q0001"+chr(10)
            txt=txt+"E"+chr(10)
            return txt


    @api.multi
    def imprimer_etiquette_direct(self):
        for obj in self:
            etiquettes=self.generer_etiquette()
            etiquettes=unicode(etiquettes,'utf-8')
            etiquettes=etiquettes.encode("windows-1252")
            path="/tmp/etiquette.txt"
            err=""
            try:
                fichier = open(path, "w")
            except IOError, e:
                err="Problème d'accès au fichier '"+path+"' => "+ str(e)
            if err=="":
                fichier.write(etiquettes)
                fichier.close()
                user  = self.env['res.users'].browse(self._uid)
                imprimante = user.company_id.is_nom_imprimante or 'Datamax'
                cmd="lpr -h -P"+imprimante+" "+path
                os.system(cmd)


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
            filename = '/tmp/product.template-%s.xml' % uuid.uuid4()
            temp = open(filename, 'w+b')
            description = msg_dict.get('body')
            description = description.encode('utf-8')
            temp.write(description)
            temp.close()
            tree = ET.parse(filename)
            root = tree.getroot()
            for n1 in root:
                if n1.tag in fields:
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
            vals['purchase_line_warn'] = u'warning'
            vals['purchase_line_warn_msg'] = u'Article non validé'
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
                res=prod_obj.compute_price(cr, uid, [obj.id], template_ids=[obj.id], real_time_accounting=False, recursive=True, test=False, context=context)
            if obj.cost_method=='real' and obj.is_recalcul_prix_revient:
                SQL="""
                    SELECT pol.price_unit
                    FROM purchase_order po join purchase_order_line pol on po.id=pol.order_id
                                           join product_product pp on pol.product_id=pp.id
                                           join product_template pt on pt.id=pp.product_tmpl_id
                    WHERE pol.price_unit>0 and pt.id=%s and po.state in ('approved','done')
                    ORDER BY pol.id desc 
                    limit 1
                """
                cr.execute(SQL,[obj.id])
                for row in cr.fetchall():
                    obj.standard_price=row[0]


    @api.multi
    def recalcul_all_prix_revient(self):
        products=self.env['product.template'].search([])
        for product in products:
            product.recalcul_prix_revient_action()


    def recalcul_prix_revient_scheduler_action(self, cr, uid, use_new_cursor=False, company_id = False, context=None):
        self.recalcul_all_prix_revient(cr, uid, context)





