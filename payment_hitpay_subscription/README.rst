.. image:: images/logo.png

=========================================================
HitPay Subscription Payment Provider for Odoo 19 Enterprise
=========================================================

HitPay Subscription Payment Provider integrates HitPay Recurring Billing with
Odoo Subscriptions, allowing merchants to securely collect recurring payments
using saved customer payment methods.

Customers authorize their payment method during the initial subscription
checkout. Future subscription renewals are charged automatically using the
saved payment method without requiring additional customer interaction.

Features
========

* Secure payment method tokenization
* Automatic recurring subscription billing
* Online and offline token payments
* Automatic recurring payment renewals
* Automatic webhook registration and removal
* Secure webhook signature verification
* Automatic payment method attachment
* Automatic payment method detachment
* Intelligent provider visibility during checkout
* Configurable recurring payment methods
* Standalone payment provider for Odoo 19 Enterprise

Supported Recurring Payment Methods
===================================

The payment methods displayed during checkout can be configured directly from
Odoo based on the payment methods enabled in the merchant's HitPay account.

Supported payment methods include:

* Visa
* Mastercard
* American Express
* GrabPay
* ShopeePay
* Touch 'n Go

Requirements
============

* Odoo 19 Enterprise
* sale_subscription
* payment

Installation
============

Download the latest release from:

https://github.com/hit-pay/odoo-extension/releases

Copy the module into one of your Odoo addons directories.

Examples:

* ``[ODOO_ROOT]/server/odoo/addons/``
* ``/var/lib/odoo/addons/<version>/``
* Any directory configured in ``addons_path``

Then update the Apps list and install:

**HitPay Subscription Payment Provider**

Configuration
=============

1. Navigate to:

   **Accounting → Configuration → Payment Providers**

2. Open **HitPay Subscription Payment Provider**

3. Enter your HitPay API credentials.

4. Publish the payment provider.

5. Configure the recurring payment methods you wish to offer.

6. Select an Accounting Journal.

During installation the module automatically:

* Registers the webhook with HitPay
* Stores the webhook identifier
* Stores the webhook event salt used for signature verification

Checkout Flow
=============

Initial Subscription Payment
----------------------------

1. Customer selects **HitPay Subscription** during checkout.
2. Customer is redirected to the secure HitPay hosted payment page.
3. Customer authorizes a recurring payment method.
4. HitPay securely tokenizes the payment method.
5. Odoo stores the payment token.
6. The initial subscription payment is completed.
7. The subscription becomes active.

Recurring Renewals
------------------

When the subscription is renewed:

1. Odoo automatically creates the renewal invoice.
2. The saved payment method is charged automatically.
3. Payment is registered in Odoo.
4. The renewal invoice is paid automatically.

Webhook Processing
==================

The module automatically processes the following webhook events:

* Payment method attached
* Payment method detached

Recurring payment transactions are processed synchronously from the immediate
API response returned by HitPay. The ``charge.created`` webhook is acknowledged
for auditing purposes but is not used for transaction processing.

Payment Method Lifecycle
========================

When a customer authorizes a payment method:

* A payment token is automatically created.
* The HitPay recurring billing identifier is stored securely.
* Future recurring charges reuse the same payment token.

If the customer removes the payment method from HitPay:

* The corresponding Odoo payment token is automatically archived.
* Future recurring payments using that token are prevented.

Important Notes
===============

Subscription products intended for automatic recurring billing should use:

::

    Invoicing Policy = Ordered Quantities

Products configured with:

::

    Invoicing Policy = Delivered Quantities

cannot be automatically invoiced until they become invoiceable according to
Odoo's standard invoicing rules.

Supported Features
==================

===============================  ===========
Feature                          Support
===============================  ===========
Subscription Payments            Yes
Payment Tokenization             Yes
Saved Payment Methods            Yes
Automatic Renewals               Yes
Online Token Payments            Yes
Offline Token Payments           Yes
Webhook Registration             Yes
Webhook Signature Verification   Yes
Payment Method Attachment        Yes
Payment Method Detachment        Yes
Refunds                          No
Express Checkout                 No
===============================  ===========

Architecture
============

The module consists of:

* Payment Provider
* Payment Transaction
* Payment Token
* Webhook Controller
* Automatic Webhook Registration
* Automatic Webhook Cleanup

License
=======

LGPL-3

Author
======

HitPay Payment Solutions Pte Ltd

Website:

https://www.hitpayapp.com

Change Log
==========

19.0.0.1
---------

* Initial release.
* Standalone HitPay Subscription payment provider.
* Secure payment tokenization.
* Automatic recurring subscription billing.
* Automatic webhook registration and cleanup.
* Secure webhook signature verification.
* Automatic payment method lifecycle management.
* Configurable recurring payment methods.
* Intelligent provider visibility during checkout.