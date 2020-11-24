# -*- coding: utf-8 -*-
from openerp import models,fields,api
import datetime
import pytz


class is_personnel_present(models.Model):
    _name='is.personnel.present'
    _order='name desc'

    name = fields.Date("Date", required=True, default=lambda *a: datetime.date.today().strftime('%Y-%m-%d'))
    site = fields.Selection([
            ('192.168.1.9'  , 'BSA'),
            ('192.168.20.10', 'Bressane'),
        ], u"Site", required=True)


    @api.multi
    def get_pointages(self):
        sites={
            '192.168.1.9'  : 'BSA',
            '192.168.20.10': 'Bressane',
        }
        cr = self._cr
        employes=[]
        for obj in self:
            SQL="""
                select id,name_related 
                from hr_employee
                order by name_related
            """
            cr.execute(SQL)
            res = cr.fetchall()
            for row in res:
                SQL="""
                    select 
                        create_date at time zone 'utc' at time zone 'europe/paris',
                        entree_sortie,
                        pointeuse
                    from is_pointage 
                    where 
                        employee="""+str(row[0])+""" and
                        pointeuse='"""+obj.site+"""' and
                        create_date>='"""+obj.name+""" 00:00:00' and
                        create_date<='"""+obj.name+""" 23:59:59' 
                    order by id desc limit 1
                """
                cr.execute(SQL)
                pointages = cr.fetchall()
                pointage=False
                for p in pointages:
                    if p[1]=='E':
                        pointage = p
                name = row[1]+' : '+str(pointage)
                if pointage:
                    create_date = pointage[0]
                    create_date = datetime.datetime.strptime(create_date, '%Y-%m-%d %H:%M:%S.%f')
                    create_date = create_date.strftime('%d/%m/%Y %H:%M')
                    employes.append({
                        'name'       : row[1],
                        'create_date': create_date,
                        'pointeuse'  : sites[pointage[2]],
                    })
        return employes


    @api.multi
    def get_db_name(self):
        db_name = self._cr.dbname
        return db_name


    @api.multi
    def get_connexions(self):
        cr = self._cr
        connexions=[]
        for obj in self:
            SQL="""
                select rp.name
                from res_users ru inner join  res_partner rp on ru.partner_id=rp.id
                where ru.login_date='"""+obj.name+"""'
                order by rp.name
            """
            cr.execute(SQL)
            rows = cr.fetchall()
            for row in rows:
                connexions.append(row[0])
        return connexions

##bsa-odoo=# select id,login,login_date,write_date from res_users order by login_date;


