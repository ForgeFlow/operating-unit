# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L.
# - Jordi Ballester Alomar
# © 2015 Ecosoft Co. Ltd. - Kitti Upariphutthiphong
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Budget with Operating Units',
    'version': '9.0.1.0.0',
    'category': 'Accounting & Finance',
    "author": "Eficent Business and IT Consulting Services S.L., "
              "Ecosoft Co. Ltd.,"
              "Serpent CS,"
              "Odoo Community Association (OCA)",
    'website': 'http://www.eficent.com',
    "license": "LGPL-3",
    'depends': ['account_budget', 'operating_unit'],
    'data': [
        'views/account_budget_view.xml',
        'security/account_budget_security.xml'
    ],
    'installable': True,
}
