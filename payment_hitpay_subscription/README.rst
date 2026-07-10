.. image:: images/logo.png

HitPay Subscription Payment Provider for Odoo 19 Enterprise
===========================================================

HitPay Subscription Payment Provider integrates HitPay Recurring Billing
with Odoo Subscriptions, allowing merchants to securely collect
recurring subscription payments using saved customer payment methods.

Customers authorize their payment method during the initial subscription
checkout. Future subscription renewals are charged automatically using
the saved payment method without requiring additional customer
interaction.

Features
--------

-  Secure payment method tokenization
-  Automatic recurring subscription billing
-  Automatic subscription renewals
-  Online and offline token payments
-  Automatic webhook lifecycle management
-  Secure webhook signature verification
-  Automatic payment method attachment
-  Automatic payment method detachment
-  Saved payment methods for future payments
-  Intelligent provider visibility during checkout
-  Configurable recurring payment methods
-  Standalone payment provider for Odoo 19 Enterprise

Supported Recurring Payment Methods
-----------------------------------

Merchants can enable only the recurring payment methods supported by
their HitPay account. Enabled payment methods are displayed
automatically during checkout.

Supported payment methods include:

-  Visa
-  Mastercard
-  American Express
-  GrabPay
-  ShopeePay
-  Touch 'n Go

Requirements
------------

-  Odoo 19 Enterprise
-  sale_subscription
-  payment

Installation
------------

The HitPay Subscription Payment Provider can be installed from the Odoo
Apps Store, deployed through Odoo.sh, or installed manually from a
release package.

Install from Odoo Apps
~~~~~~~~~~~~~~~~~~~~~~

1. Purchase or download **HitPay Subscription Payment Provider** from
   the Odoo Apps Store.

2. Download the module source code from your Odoo Apps account.

3. Extract the downloaded archive if necessary.

4. Copy the ``payment_hitpay_subscription`` module directory into a
   custom addons directory configured in the Odoo ``addons_path``.

   Examples:

   .. code:: text

   [ODOO_ROOT]/custom_addons/ /var/lib/odoo/addons/<version>/
   /opt/odoo/custom_addons/

5. Restart the Odoo server.

6. Enable Developer Mode.

7. Go to **Apps** and select **Update Apps List**.

8. Search for **HitPay Subscription Payment Provider**.

9. Click **Install**.

Deploy on Odoo.sh
~~~~~~~~~~~~~~~~~

1. Download the module source code from the Odoo Apps Store or the
   appropriate release package.

2. Extract the ``payment_hitpay_subscription`` module into the Git
   repository connected to your Odoo.sh project.

   Example repository structure:

   .. code:: text

   your-odoo-project/
   ├── custom_addons/
   │   └── payment_hitpay_subscription/
   ├── README.md
   └── requirements.txt

3. Commit the module and push the changes to the appropriate Odoo.sh
   branch.

   .. code:: bash

   git add custom_addons/payment_hitpay_subscription
   git commit -m "Add HitPay Subscription Payment Provider"
   git push

4. Wait for the Odoo.sh build to complete successfully.

5. Open the Odoo database associated with the deployed branch.

6. Enable Developer Mode.

7. Go to **Apps** and select **Update Apps List**.

8. Search for **HitPay Subscription Payment Provider**.

9. Click **Install**.

Install from a Release Package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Download the latest compatible release package from the HitPay Odoo
   Extension releases page.

2. Extract the release archive.

3. Copy the ``payment_hitpay_subscription`` module directory into a
   custom addons directory configured in the Odoo ``addons_path``.

   Examples:

   .. code:: text

   [ODOO_ROOT]/custom_addons/ /var/lib/odoo/addons/<version>/
   /opt/odoo/custom_addons/

4. Restart the Odoo server.

5. Enable Developer Mode.

6. Go to **Apps** and select **Update Apps List**.

7. Search for **HitPay Subscription Payment Provider**.

8. Click **Install**.

Upgrade
-------

Before upgrading the module, back up the Odoo database and filestore.

Upgrade from Odoo Apps
~~~~~~~~~~~~~~~~~~~~~~

1. Download the latest compatible module version from your Odoo Apps
   account.
2. Replace the existing ``payment_hitpay_subscription`` module source
   code with the new version.
3. Restart the Odoo server.
4. Enable Developer Mode.
5. Go to **Apps** and select **Update Apps List**.
6. Locate **HitPay Subscription Payment Provider**.
7. Click **Upgrade**.

Upgrade on Odoo.sh
~~~~~~~~~~~~~~~~~~

1. Replace the existing module source code in the Git repository
   connected to the Odoo.sh project.

2. Commit the updated module files.

   .. code:: bash

   git add custom_addons/payment_hitpay_subscription
	 git commit -m "Upgrade HitPay Subscription Payment Provider"
	 git push

3. Wait for the Odoo.sh build to complete successfully.

4. Open the database associated with the deployed branch.

5. Go to **Apps**.

6. Locate **HitPay Subscription Payment Provider**.

7. Click **Upgrade**.

If the release includes database schema changes, new fields, XML data
changes, access-control changes, or other module metadata updates,
upgrading the module is required after deployment.

Upgrade from a Release Package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Download the latest compatible release package.

2. Back up the existing module source code if required.

3. Replace the existing ``payment_hitpay_subscription`` module directory
   with the new release.

   Do not merge old and new module directories because removed or
   renamed files from previous releases may remain on the server.

4. Restart the Odoo server.

5. Enable Developer Mode.

6. Go to **Apps** and select **Update Apps List**.

7. Locate **HitPay Subscription Payment Provider**.

8. Click **Upgrade**.

Command-Line Upgrade
~~~~~~~~~~~~~~~~~~~~

For command-line deployments, the module can be upgraded with:

.. code:: bash

   ./odoo-bin \
       -d <database_name> \
       -u payment_hitpay_subscription \
       --stop-after-init

Ensure that the Odoo configuration used by the command includes the
custom addons directory containing ``payment_hitpay_subscription``.

After upgrading, verify that the HitPay payment provider configuration
is valid and save the provider configuration if webhook synchronization
needs to be triggered.

The module automatically manages webhook registration, synchronization,
recovery, and cleanup. Manual recreation of HitPay webhooks is normally
not required.

Configuration
-------------

1. Navigate to:

   **Website → Configuration → Payment Providers**

2. Open **HitPay Subscription Payment Provider**.

3. Enter your HitPay API credentials.

4. Publish the payment provider.

5. Enable the recurring payment methods supported by your HitPay
   account.

6. Select an Accounting Journal.

The module automatically manages the webhook throughout the payment
provider lifecycle, including creation, updates, environment changes,
and cleanup.

Checkout Flow
-------------

Initial Subscription Payment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Customer selects **HitPay Subscription** during checkout.
2. Customer is redirected to the secure HitPay hosted payment page.
3. Customer authorizes a recurring payment method.
4. HitPay securely creates and authorizes the recurring payment method.
5. Odoo automatically stores the payment token.
6. Odoo performs the initial recurring subscription charge.
7. The subscription payment is completed and the subscription becomes
   active.

Recurring Renewals
~~~~~~~~~~~~~~~~~~

When the subscription is renewed:

1. Odoo automatically generates the renewal invoice.
2. The saved payment method is charged automatically.
3. The payment transaction is processed immediately.
4. Payment is registered in Odoo.
5. The renewal invoice is paid automatically.

Webhook Processing
------------------

The module automatically processes the following recurring billing
webhook events:

-  Payment method attached
-  Payment method detached

Recurring payment transactions are processed synchronously using the
immediate API response returned by HitPay. Because HitPay does not
provide a merchant reference when creating recurring charges, the
``charge.created`` webhook cannot be reliably correlated with an Odoo
transaction. It is acknowledged for auditing purposes but is not used
for transaction processing.

Payment Method Lifecycle
------------------------

When a customer authorizes a recurring payment method:

-  A payment token is automatically created.
-  The HitPay recurring billing identifier is securely stored.
-  The initial recurring subscription payment is processed
   automatically.
-  Future subscription renewals reuse the same saved payment token.

If the customer removes the payment method from HitPay:

-  The corresponding Odoo payment token is automatically archived.
-  Future recurring payments using that payment token are prevented.

Important Notes
---------------

Subscription products intended for automatic invoicing should use:

::

   Invoicing Policy = Ordered Quantities

Products configured with:

::

   Invoicing Policy = Delivered Quantities

cannot be automatically invoiced until they become invoiceable according
to Odoo's standard invoicing rules.

Supported Features
------------------

=============================== =======
Feature                         Support
=============================== =======
Subscription Payments           Yes
Payment Tokenization            Yes
Saved Payment Methods           Yes
Automatic Subscription Renewals Yes
Online Token Payments           Yes
Offline Token Payments          Yes
Automatic Webhook Lifecycle     Yes
Webhook Signature Verification  Yes
Payment Method Attachment       Yes
Payment Method Detachment       Yes
Refunds                         No
Express Checkout                No
=============================== =======

Architecture
------------

The module consists of:

-  Payment Provider
-  Payment Transaction
-  Payment Token
-  Webhook Controller
-  Automatic Webhook Lifecycle Management
-  Odoo Subscription Integration

License
-------

LGPL-3

Author
------

HitPay Payment Solutions Pte Ltd

Website:

`HitPay <https://www.hitpayapp.com>`__

Change Log
----------

19.0.0.2
~~~~~~~~

-  Jul 10, 2026
-  Fixed webhook lifecycle synchronization, cleanup, and automatic
   recovery.
-  Fixed webhook salt preservation and recovery when local webhook data
   is incomplete.
-  Fixed webhook cleanup when provider credentials, environment, or
   state changes.
-  Fixed module upgrades failing while updating payment method records.
-  Fixed API errors displaying as generic Odoo server errors during
   provider configuration and payment processing.
-  Fixed validation of malformed or incomplete HitPay API responses.
-  Improved webhook API error handling with HTTP status-aware recovery.
-  Improved stale and duplicate webhook cleanup.
-  Improved sanitized API request and response logging.
-  Improved recurring billing error handling and transaction response
   validation.

.. _section-1:

19.0.0.1
~~~~~~~~

-  Jul 03, 2026
-  Initial release.
-  Standalone HitPay Subscription payment provider.
-  Automatic recurring subscription billing.
-  Secure recurring payment method tokenization.
-  Online and offline token payments.
-  Automatic webhook lifecycle management.
-  Secure webhook signature verification.
-  Automatic payment method lifecycle management.
-  Configurable recurring payment methods.
-  Intelligent provider visibility during checkout.
-  Seamless integration with Odoo Subscriptions.

