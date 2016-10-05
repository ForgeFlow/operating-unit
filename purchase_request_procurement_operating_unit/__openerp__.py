# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. -
# Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "Purchase Request Procurement with Operating Units",
    "version": "9.0.1.0.0",
    "author": "Eficent",
    "website": "www.eficent.com",
    "category": "Purchase Management",
    "depends": ["purchase_request_procurement",
                "purchase_request_operating_unit",
                'procurement_operating_unit'],
    "description": """
Purchase Request Procurement with Operating Unit
================================================
This module passes the Operating Unit from the Procurement to the Purchase
Request.


Credits
=======

Contributors
------------

* Jordi Ballester <jordi.ballester@eficent.com>


Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
    """,
    'installable': True,
}
