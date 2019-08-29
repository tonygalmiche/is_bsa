# -*- coding: utf-8 -*-

from openerp import models,fields,api
from openerp.tools.translate import _


class ProjectTask(models.Model):
    _inherit = "project.task"


    @api.depends('is_description')
    def _compute_is_description_html(self):
        for obj in self:
            if obj.is_description:
                obj.is_description_html = obj.is_description.replace('\n','<br />')


    is_description      = fields.Text(u'Description')
    is_description_html = fields.Text('Description HTML', compute='_compute_is_description_html', readonly=True, store=False)
    is_appro_specifique = fields.Boolean(u"Appro spécifique")
    is_appro_standard   = fields.Boolean(u"Appro standard")




