# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L.
# - Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Sales Order Report With Note Operating Unit',
    'version': '9.0.1.0.0',
    'category': 'Reports/Qweb',
    'license': 'AGPL-3',
    "author": "Eficent, "
              "Serpent CS,"
              "Odoo Community Association (OCA)",
    'website': "https://odoo-community.org/",
    'depends': ['sale_order_report_with_note',
                'sale_operating_unit'],
    'data': [
              'views/report_saleorder_qweb.xml',
              ],
    'installable': True,
}
