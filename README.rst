===================================================
HitPay Payment Gateway for Odoo
===================================================

Official Odoo integration for `HitPay Payment Solutions <https://www.hitpayapp.com>`_, enabling merchants to accept 70+ payment methods including cards, digital wallets, and regional payment options.

Supported Odoo Versions
=======================

+-------------+------------------+------------------+
| Odoo Version| payment_hitpay   | pos_hitpay       |
+=============+==================+==================+
| 19.0        | No               | Yes              |
+-------------+------------------+------------------+
| 18.0        | Yes              | Yes              |
+-------------+------------------+------------------+
| 17.0        | Yes              | Yes              |
+-------------+------------------+------------------+
| 16.0        | Yes              | Yes              |
+-------------+------------------+------------------+
| 15.0        | Yes              | No               |
+-------------+------------------+------------------+

Installation
============

1. Clone the repository and checkout your Odoo version branch:

   .. code-block:: bash

      git clone https://github.com/hit-pay/odoo-extension.git
      cd odoo-extension
      git checkout 19.0  # Replace with your Odoo version (15.0, 16.0, 17.0, 18.0, 19.0)

2. Copy the module(s) to your Odoo addons directory:

   .. code-block:: bash

      cp -r payment_hitpay /path/to/odoo/addons/
      cp -r pos_hitpay /path/to/odoo/addons/  # If available for your version

3. Restart Odoo and update the apps list.

4. Install the module(s) from Apps menu.

Modules
=======

payment_hitpay - E-commerce Payment Gateway
-------------------------------------------

Integrates HitPay with Odoo's e-commerce checkout, allowing customers to pay using:

- Credit/Debit Cards (Visa, Mastercard, American Express)
- Digital Wallets (Apple Pay, Google Pay, GrabPay, WeChat Pay, Alipay)
- Regional Methods (PayNow QR, bank transfers)
- Buy Now Pay Later (Akulaku, Kredivo, Atome)

**Configuration:**

1. Go to *Invoicing/Accounting > Configuration > Payment Providers*
2. Select *HitPay* and click *Activate*
3. Enter your API Key and Salt from the `HitPay Dashboard <https://dashboard.hitpayapp.com>`_
4. Set the environment (Test/Production)
5. Save and publish the payment method

pos_hitpay - Point of Sale Payment Gateway
------------------------------------------

Integrates HitPay with Odoo POS for in-store payments.

**Configuration:**

1. Go to *Point of Sale > Configuration > Payment Methods*
2. Create a new payment method
3. Set *Use a Payment Terminal* to *HitPay Payment Gateway*
4. Enter your API Key, Salt, and Terminal ID
5. Add the payment method to your POS configuration

Requirements
============

- Odoo 15.0, 16.0, 17.0, 18.0 or 19.0
- HitPay merchant account (`Sign up here <https://www.hitpayapp.com>`_)
- API credentials from HitPay Dashboard

Support
=======

- **Documentation:** `HitPay Docs <https://docs.hitpayapp.com>`_
- **Issues:** `GitHub Issues <https://github.com/hit-pay/odoo-extension/issues>`_

License
=======

LGPL-3 (GNU Lesser General Public License v3.0)

Copyright (c) HitPay Payment Solutions Pte Ltd
