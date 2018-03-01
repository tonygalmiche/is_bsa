# -*- coding: utf-8 -*-



{
  "name" : "InfoSaône - Module Odoo pour BSA",
  "version" : "0.1",
  "author" : "InfoSaône / Tony Galmiche",
  "category" : "InfoSaône\BSA",


  'description': """
InfoSaône - Module Odoo pour BSA
===================================================

InfoSaône - Module Odoo pour BSA

""",

  'maintainer': 'InfoSaône',
  'website': 'http://www.infosaone.com',

  "depends" : [
    "base",
    "mail",
    "crm",                    # CRM
    #"account_voucher",        # eFacturation & Règlements
    #"account_accountant",     # Comptabilité et finance
    "sale",                   # Gestion des ventes
    "stock",                  # Stock
    "mrp",                    # MRP
    "mrp_operations",         # Gammes
    "purchase",               # Gestion des achats
    "hr",                     # Ressources humaines
    #"report_webkit",          # Rapports Webkit
    "sale_order_dates"        # Ajout de champs dates dans les commandes clients (date demandée)
  ], # Liste des dépendances (autres modules nececessaire au fonctionnement de celui-ci)
     # -> Il peut être interessant de créer un module dont la seule fonction est d'installer une liste d'autres modules
     # Remarque : La desinstallation du module n'entrainera pas la desinstallation de ses dépendances (ex : mail)

  "init_xml" : [],
  "demo_xml" : [],
  "data" : [
    "assets.xml",
    "sale_view.xml",
    "pricelist_view.xml",
    "mrp_view.xml",
    "product_view.xml",
    "bsa_stock_a_date_view.xml",
    "report/report_qweb_mrp.xml",
    "report/report_mrporder.xml",
    "report/report_purchaseorder.xml",
    "report/report_stockpicking.xml",
    "report/report_expense.xml",
    "report/report_expense_list.xml",
    "report/report_fiche_travail.xml",
    "report/conditions_generales_de_vente_templates.xml",
    "report/report_saleorder.xml",
    "report/report_invoice.xml",
    "report/report.xml", 
    "is_fiche_travail.xml",
    "wizard/is_etiquette_reception_view.xml",
    "stock_view.xml",
    "purchase_view.xml",
    "email_template_view.xml",
    "res_partner_view.xml",
    "bsa_fnc_view.xml",
    "is_export_compta.xml",
    "is_import_nomenclature.xml",
    "account_invoice_view.xml",
    "views/is_liste_manquants.xml",
    "views/is_sale_order_line.xml",
    "menu.xml",
    "security/ir.model.access.csv",
  ],
  "installable": True,
  "active": False,
  "application": True
}




