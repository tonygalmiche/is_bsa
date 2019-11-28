# -*- coding: utf-8 -*-


from openerp import models,fields,api
from openerp.tools.translate import _


class hr_employee(models.Model):
    _inherit = "hr.employee"

    is_workcenter_ids = fields.Many2many('mrp.workcenter', 'hr_employee_mrp_workcenter_rel', 'employe_id', 'workcenter_id', u'Postes de charges autorisés')


