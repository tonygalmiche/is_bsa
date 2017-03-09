# -*- coding: utf-8 -*-

from openerp import models,fields,api,_
from openerp.exceptions import ValidationError

import pytz
from datetime import datetime, timedelta
from pytz import timezone

import os


# ** Convertir une date string utc en date string localisée ****************
def d(date):
    # Timezone en UTC
    utc = pytz.utc
    # DateTime à partir d'une string avec ajout de la timezone
    utc_dt  = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=utc)
    # Timezone Europe/Paris
    europe = timezone('Europe/Paris')
    # Convertion de la datetime utc en datetime localisée
    loc_dt = utc_dt.astimezone(europe)
    # Retour de la datetime localisée en string
    return loc_dt.strftime('%d/%m/%Y %H:%M')



def imprimer_etiquette(txt):
    path="/tmp/etiquette.txt"
    err=""
    try:
        fichier = open(path, "w")
    except IOError, e:
        err="Problème d'accès au fichier '"+path+"' => "+ str(e)
    if err=="":
        fichier.write(txt)
        fichier.close()
        cmd="lpr -h -PDatamax "+path
        os.system(cmd)






class is_etiquette_reception(models.TransientModel):
    _name = "is.etiquette.reception"

    @api.model
    def default_get(self, fields):
        context = self._context
        context = context or {} 
        res = super(is_etiquette_reception, self).default_get(fields)
        active_id = context.get('active_id')
        move_obj = self.env['stock.move']
        move_brw = move_obj.browse(active_id)
        res['stock_picking_id'] = move_brw.picking_id.id
        res['stock_move_id'] = move_brw.id
        res['quantite'] = move_brw.product_uom_qty
        return res

    stock_picking_id = fields.Many2one('stock.picking', string="Réception")
    stock_move_id = fields.Many2one('stock.move', string="Mouvement de stock")
    quantite = fields.Integer('Quantité')


    @api.one
    def check_wizard(self):
        wizard_brw = self[0]
        DateReception=str(wizard_brw.stock_picking_id.date)

        stock_move_id=str(wizard_brw.stock_move_id.id)

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
        txt=txt+"1E2206100060014B"+stock_move_id+chr(10)
        txt=txt+"102200002160010NUMERO FABRICATION : "+stock_move_id+chr(10)
        txt=txt+"102200001730009CLIENT : "+str(wizard_brw.stock_picking_id.partner_id.name)+chr(10)
        txt=txt+"103300001460084"+"#########################"+chr(10)
        txt=txt+"103300001180015"+str(wizard_brw.stock_move_id.product_id.name)+chr(10)
        txt=txt+"103300000910009NUMERO SERIE :"+stock_move_id+chr(10)
        txt=txt+"102200001950008COMMANDE : "+str(wizard_brw.stock_picking_id.origin)+chr(10)
        txt=txt+"^01"+chr(10)
        txt=txt+"Q0001"+chr(10)
        txt=txt+"E"+chr(10)


        i = 0
        etiquettes=""
        while i < wizard_brw.quantite:
            etiquettes=etiquettes+txt
            i += 1

        etiquettes=unicode(etiquettes,'utf-8')
        etiquettes=etiquettes.encode("windows-1252")

        #txt=txt+str(DateReception)+"\n"
        #txt=txt+ d(DateReception)+"\n"
        #txt=txt+ str(wizard_brw.stock_picking_id.partner_id.name)+"\n"
        #txt=txt+ str(wizard_brw.stock_move_id)+"\n"
        #txt=txt+ str(wizard_brw.stock_move_id.product_id.name)+"\n"
        #txt=txt+ str(wizard_brw.quantite)+"\n"
        imprimer_etiquette(etiquettes)

        return True


