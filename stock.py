# -*- coding: utf-8 -*-

from openerp import models,fields,api




class stock_picking(models.Model):
    _inherit = "stock.picking"

    is_commentaire = fields.Text(string='Commentaire pour le client')


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
