# -*- coding: utf-8 -*-

from openerp import models,fields,api
from openerp.tools.translate import _


class purchase_order_line(models.Model):
    _inherit = "purchase.order.line"

    is_date_ar = fields.Date("Date AR")

