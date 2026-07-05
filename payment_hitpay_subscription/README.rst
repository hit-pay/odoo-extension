.. image:: images/logo.png

=========================================================
HitPay Subscription Payment Provider for Odoo 19 Enterprise
=========================================================

HitPay Subscription Payment Provider integrates HitPay Recurring Billing with
Odoo Subscriptions, allowing merchants to securely collect recurring subscription
payments using saved customer payment methods.

Customers authorize their payment method during the initial subscription
checkout. Future subscription renewals are charged automatically using the
saved payment method without requiring additional customer interaction.

Features
========

* Secure payment method tokenization
* Automatic recurring subscription billing
* Automatic subscription renewals
* Online and offline token payments
* Automatic webhook lifecycle management
* Secure webhook signature verification
* Automatic payment method attachment
* Automatic payment method detachment
* Saved payment methods for future payments
* Intelligent provider visibility during checkout
* Configurable recurring payment methods
* Standalone payment provider for Odoo 19 Enterprise

Supported Recurring Payment Methods
===================================

Merchants can enable only the recurring payment methods supported by their
HitPay account. Enabled payment methods are displayed automatically during
checkout.

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

Update the Apps list and install:

**HitPay Subscription Payment Provider**

Configuration
=============

1. Navigate to:

   **Accounting → Configuration → Payment Providers**

2. Open **HitPay Subscription Payment Provider**.

3. Enter your HitPay API credentials.

4. Publish the payment provider.

5. Enable the recurring payment methods supported by your HitPay account.

6. Select an Accounting Journal.

The module automatically manages the webhook throughout the payment provider
lifecycle, including creation, updates, environment changes, and cleanup.

Checkout Flow
=============

Initial Subscription Payment
----------------------------

1. Customer selects **HitPay Subscription** during checkout.
2. Customer is redirected to the secure HitPay hosted payment page.
3. Customer authorizes a recurring payment method.
4. HitPay securely creates and authorizes the recurring payment method.
5. Odoo automatically stores the payment token.
6. Odoo performs the initial recurring subscription charge.
7. The subscription payment is completed and the subscription becomes active.

Recurring Renewals
------------------

When the subscription is renewed:

1. Odoo automatically generates the renewal invoice.
2. The saved payment method is charged automatically.
3. The payment transaction is processed immediately.
4. Payment is registered in Odoo.
5. The renewal invoice is paid automatically.

Webhook Processing
==================

The module automatically processes the following recurring billing webhook
events:

* Payment method attached
* Payment method detached

Recurring payment transactions are processed synchronously using the immediate
API response returned by HitPay. Because HitPay does not provide a merchant
reference when creating recurring charges, the ``charge.created`` webhook
cannot be reliably correlated with an Odoo transaction. It is acknowledged for
auditing purposes but is not used for transaction processing.

Payment Method Lifecycle
========================

When a customer authorizes a recurring payment method:

* A payment token is automatically created.
* The HitPay recurring billing identifier is securely stored.
* The initial recurring subscription payment is processed automatically.
* Future subscription renewals reuse the same saved payment token.

If the customer removes the payment method from HitPay:

* The corresponding Odoo payment token is automatically archived.
* Future recurring payments using that payment token are prevented.

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

====================================  ===========
Feature                               Support
====================================  ===========
Subscription Payments                 Yes
Payment Tokenization                  Yes
Saved Payment Methods                 Yes
Automatic Subscription Renewals       Yes
Online Token Payments                 Yes
Offline Token Payments                Yes
Automatic Webhook Lifecycle           Yes
Webhook Signature Verification        Yes
Payment Method Attachment             Yes
Payment Method Detachment             Yes
Refunds                               No
Express Checkout                      No
====================================  ===========

Architecture
============

The module consists of:

* Payment Provider
* Payment Transaction
* Payment Token
* Webhook Controller
* Automatic Webhook Lifecycle Management
* Odoo Subscription Integration

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
* Jul 03, 2026
* Initial release.
* Standalone HitPay Subscription payment provider.
* Secure recurring payment method tokenization.
* Automatic recurring subscription billing.
* Automatic subscription renewals.
* Online and offline token payments.
* Automatic webhook lifecycle management.
* Secure webhook signature verification.
* Automatic payment method lifecycle management.
* Configurable recurring payment methods.
* Intelligent provider visibility during checkout.
* Seamless integration with Odoo Subscriptions.