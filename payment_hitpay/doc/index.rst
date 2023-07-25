Installation & Upgrade
---------------------------

Download the latest module archive from https://github.com/hit-pay/odoo-extension/releases.

Now unzip the downloaded archive and copy the new payment_hitpay folder to Odoo addons directory. 

* [ODOO_ROOT_FOLDER]/server/odoo/addons/
* /var/lib/odoo/addons/[VERSION]/ (on Linux only)
* `addons_path` defined in odoo.conf

Then, youcan choose  one of these instructions:

* In your Odoo administrator interface, browse to "Configuration" tab. Here in, activate the developer mode.
* Or restart Odoo server with *sudo systemctl restart odoo* on Linux or by restarting Windows Odoo service.
  Odoo will update the applications list on startup.
*  Then browse to "Applications" tab and click on "Update applications list".

In your Odoo administrator interface, browse to "Applications" tab, delete "Applications" filter from
search field and search for "hitpay" keyword. Click "Install" (or "Upgrade") button of the "HitPay Payment Gateway Provider" module.

Configuration
---------------------------

* Go to "Website Admin" tab
* In "Configuration" section, expand "eCommerce" menu than click on "Payment Providers" entry
* Select HitPay Payment Gateway module
* You can now enter your HitPay Payment Gateway credentials

IMPORTANT
---------
* You should select a Payment Journal in the "Configuration" tab of the HitPay Payment Gateway
  to start using this payment method.

Change Log
---------------------------
1.0.
--------------------
* Initial release.
