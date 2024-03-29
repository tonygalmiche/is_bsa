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
    "sale_order_dates",       # Ajout de champs dates dans les commandes clients (date demandée)
    "project",
    "warning",                # Module permettant d'ajouter des blocages sur les articles et commandes
    "is_pointeuse",
  ], # Liste des dépendances (autres modules nececessaire au fonctionnement de celui-ci)
     # -> Il peut être interessant de créer un module dont la seule fonction est d'installer une liste d'autres modules
     # Remarque : La desinstallation du module n'entrainera pas la desinstallation de ses dépendances (ex : mail)

  "init_xml" : [],
  "demo_xml" : [],
  "data" : [
    "security/res.groups.xml",
    "security/ir.model.access.csv",
    "assets.xml",
    "account_move_line_view.xml",
    "wizard/is_mrp_workcenter_temps_ouverture_wiz.xml",
    "res_company_view.xml",
    "sale_view.xml",
    "pricelist_view.xml",
    "mrp_view.xml",
    "product_view.xml",
    "bsa_stock_a_date_view.xml",
    "is_accident_travail_view.xml",
    "is_fiche_controle.xml",
    "hr_view.xml",
    "is_personnel_present.xml",
    "project_view.xml",
    "report/report_qweb_mrp.xml",
    "report/report_mrporder.xml",
    "report/report_purchaseorder.xml",
    "report/report_stockpicking.xml",
    "report/report_expense.xml",
    "report/report_expense_list.xml",
    "report/report_fiche_travail.xml",
    "report/conditions_generales_de_vente_bressane_templates.xml",
    "report/conditions_generales_de_vente_bsa_templates.xml",
    "report/report_saleorder.xml",
    "report/report_invoice.xml",
    "report/report_personnel_present.xml",
    "report/report_bon_atelier.xml",
    "report/report_fiche_controle.xml",
    "report/layouts.xml",
    "report/report.xml", 
    "is_fiche_travail.xml",
    "wizard/is_etiquette_reception_view.xml",
    "wizard/stock_transfer_details.xml",
    "stock_view.xml",
    "purchase_view.xml",
    "email_template_view.xml",
    "res_partner_view.xml",
    "bsa_fnc_view.xml",
    "is_export_compta.xml",
    "is_balance_agee.xml",
    "is_import_nomenclature.xml",
    "is_calcul_pmp.xml",
    "account_invoice_view.xml",
    "views/is_liste_manquants.xml",
    "views/is_sale_order_line.xml",
    "views/is_mrp_bom_line.xml",
    "views/is_account_invoice_line.xml",
    "views/is_derniere_commande_achat.xml",
    "views/is_picking_line.xml",
    "menu.xml",
  ],
  "installable": True,
  "active": False,
  "application": True
}




