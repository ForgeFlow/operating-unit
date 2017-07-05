# -*- coding: utf-8 -*-
# Copyright 2016-17 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# Copyright 2016-17 Serpent Consulting Services Pvt. Ltd.
#   (<http://www.serpentcs.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "Operating Unit in Purchase Requests",
    "version": "10.0.1.0.0",
    "author": "Eficent",
    "website": "http://www.eficent.com",
    "category": "Purchase Management",
    "depends": ["purchase_request",
                "purchase_operating_unit"],
    "description": """
Operating Unit in Purchase Requests
===================================
This module was written to extend the Purchase capabilities of Odoo.

This module introduces the operating unit to the purchase requests.

Security rules are defined to ensure that users can only display the
Purchase Requests in which they are allowed access to.

Installation
============

No additional installation instructions are required.


Configuration
=============

This module does not require any additional configuration.

Usage
=====

At the time when a user creates a new purchase request the system
proposes the user's default operating unit.

The operating unit is a required field.

Known issues / Roadmap
======================

No issue has been identified.

Credits
=======

Contributors
------------

* Eficent Business and IT Consulting Services S.L. <contact@eficent.com>
* Serpent Consulting Services Pvt. Ltd. <support@serpentcs.com>

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
    "data": [
        "security/purchase_security.xml",
        "view/purchase_request_view.xml",
    ],
    'installable': True,
}
