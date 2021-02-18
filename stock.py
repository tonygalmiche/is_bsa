# -*- coding: utf-8 -*-

from openerp import models,fields,api


class is_affecter_etiquette_livraison(models.Model):
    _name = "is.affecter.etiquette.livraison"

    operateur_livraison_id = fields.Many2one('hr.employee', 'Opérateur de la livraison', required=True)
    move_id                = fields.Many2one('stock.move', 'Ligne de la livraison'   , required=True)
    product_id             = fields.Many2one('product.template', 'Article', related='move_id.product_id.product_tmpl_id', readonly=True)
    etiquette_ids          = fields.Many2many('is.tracabilite.livraison', 'is_affecter_etiquette_livraison_rel', 'affecter_id', 'etiquette_id')


    @api.multi
    def ok_action(self):
        context=self._context
        ids=[]
        for obj in self:
            if 'picking_id' in context:
                picking_id=context['picking_id']
                picking = self.env['stock.picking'].browse(picking_id)
                if picking:
                    for etiquette in obj.etiquette_ids:
                        vals={
                            'sale_id': picking.document_id.id,
                            'move_id': obj.move_id.id,
                            'picking_id': picking.id,
                            'quantity': 1,
                            'livraison': picking.date_done,
                            'operateur_livraison_ids': [(6,0,[obj.operateur_livraison_id.id])]
                        }
                        etiquette.write(vals)
                        ids.append(etiquette.id)
            return {
                'name': 'Etiquettes de livraison',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'is.tracabilite.livraison',
                'domain': [('id','in',ids)],
            }


class stock_picking(models.Model):
    _inherit = "stock.picking"

    @api.depends('move_lines')
    def compute_montant_total(self):
        for obj in self:
            montant = 0
            for line in obj.move_lines:
                price_unit = line.procurement_id.sale_line_id.price_unit
                if price_unit:
                    montant+=price_unit*line.product_uom_qty
            obj.is_montant_total = montant


    @api.depends('move_lines')
    def compute_trace_reception(self):
        for obj in self:
            trace = False
            if obj.picking_type_code=='incoming':
                for line in obj.move_lines:
                    if line.product_id.is_trace_reception:
                        trace = True
            obj.is_trace_reception = trace


    is_commentaire     = fields.Text(string='Commentaire pour le client')
    is_date_bl         = fields.Date('Date BL')
    is_montant_total   = fields.Float('Montant Total HT'           , compute='compute_montant_total'  , readonly=True, store=False)
    is_trace_reception = fields.Boolean(u'Traçabilité en réception', compute='compute_trace_reception', readonly=True, store=False)


    # @api.multi
    # def imprimer_bon_atelier_action(self):
    #     for obj in self:
    #         print obj
    #         return self.env['report'].with_context({'titre': 'Bon atelier'}).get_action(self, 'is_bsa.report_picking')

    #         #report = self.env.ref('is_bsa.report_picking')
    #         #return report.with_context({'key': 'value', 'key': 'value'}).render_qweb_pdf([obj.id])



    @api.multi
    def write(self, vals):
        res=super(stock_picking, self).write(vals)
        if self.date_done and not self.is_date_bl:
            self.is_date_bl=self.date_done
        return res


    def f(self,x):
        return x.replace('\n','<br />')


class stock_move(models.Model):
    _inherit = "stock.move"

 
    is_date_ar      = fields.Date(related='purchase_line_id.is_date_ar'  , string='Date AR')
    is_date_planned = fields.Date(related='purchase_line_id.date_planned', string='Date prévue')


    def _create_invoice_line_from_vals(self, cr, uid, move, invoice_line_vals, context=None):
        invoice_line_vals['is_stock_move_id']=move.id
        res = super(stock_move, self)._create_invoice_line_from_vals(cr, uid, move, invoice_line_vals, context)
        return res


    @api.multi
    def etiquette_livraison_action(self):
        for obj in self:
            context={
                'default_move_id': obj.id,
                'picking_id':obj.picking_id.id,
            }
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'is.affecter.etiquette.livraison',
                'target': 'new',
                'context': context,
            }


    @api.multi
    def fiche_article_action(self):
        #dummy, view_id = self.env['ir.model.data'].get_object_reference('is_pg_product', 'is_product_template_only_form_view')
        for obj in self:
            return {
                'name': "Article",
                'view_mode': 'form',
                #'view_id': view_id,
                'view_type': 'form',
                'res_model': 'product.template',
                'type': 'ir.actions.act_window',
                'res_id': obj.product_id.product_tmpl_id.id,
                'domain': '[]',
            }


class is_stock_category(models.Model):
    _name = "is.stock.category"
    name = fields.Char(string='Code', size=32)


class product_template(models.Model):
    _inherit = "product.template"
     
    is_stock_category_id = fields.Many2one('is.stock.category', string='Catégorie de stock')


class stock_quant(models.Model):
    _inherit = "stock.quant"
     
    product_stock_category_id = fields.Many2one(related='product_id.is_stock_category_id', string='Catégorie de stock')


class stock_inventory(models.Model):
    _inherit = "stock.inventory"
    _order='date desc'
     
    product_stock_category_id = fields.Many2one('is.stock.category', string='Catégorie de stock')
    is_date_forcee            = fields.Datetime("Date forcée pour l'inventaire")


    @api.multi
    def action_force_date_inventaire(self):
        cr = self._cr
        for obj in self:
            if obj.is_date_forcee:
                SQL="""
                    UPDATE stock_move set date='"""+str(obj.is_date_forcee)+"""'
                    WHERE inventory_id="""+str(obj.id)+"""
                """
                res=cr.execute(SQL)


    def _get_inventory_lines(self, cr, uid, inventory, context=None):
        location_obj = self.pool.get('stock.location')
        product_obj = self.pool.get('product.product')
        location_ids = location_obj.search(cr, uid, [('id', 'child_of', [inventory.location_id.id])], context=context)
        domain = ' location_id in %s'
        args = (tuple(location_ids),)
        if inventory.partner_id:
            domain += ' and owner_id = %s'
            args += (inventory.partner_id.id,)
        if inventory.lot_id:
            domain += ' and lot_id = %s'
            args += (inventory.lot_id.id,)
        if inventory.product_id:
            domain += ' and product_id = %s'
            args += (inventory.product_id.id,)
        if inventory.package_id:
            domain += ' and package_id = %s'
            args += (inventory.package_id.id,)
        
        cr.execute('''
           SELECT product_id, sum(qty) as product_qty, location_id, lot_id as prod_lot_id, package_id, owner_id as partner_id
           FROM stock_quant WHERE''' + domain + '''
           GROUP BY product_id, location_id, lot_id, package_id, partner_id
        ''', args)
        vals = []
        for product_line in cr.dictfetchall():
            for key, value in product_line.items():
                if not value:
                    product_line[key] = False
            product_line['inventory_id'] = inventory.id
            product_line['theoretical_qty'] = product_line['product_qty']
            if product_line['product_id']:
                product = product_obj.browse(cr, uid, product_line['product_id'], context=context)
                product_line['product_uom_id'] = product.uom_id.id
            if inventory.product_stock_category_id:
                if product_obj.search(cr, uid, [('id', '=', product_line['product_id']),('is_stock_category_id','=',inventory.product_stock_category_id.id)], count=True):
                    vals.append(product_line)
            else:
                vals.append(product_line)
        return vals
