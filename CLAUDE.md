# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository overview

This repo contains two Odoo addons that integrate the HitPay payment gateway:

- `payment_hitpay/` — e-commerce payment provider (extends `payment.provider` / `payment.transaction`).
- `pos_hitpay/` — Point of Sale terminal integration (extends `pos.payment.method` / `pos.payment` / `pos.order` plus OWL/JS frontend).

There is no build, lint, or test tooling in the repo — these are pure Odoo modules. "Running" them means copying each module dir into an Odoo `addons/` path, restarting Odoo, and installing/upgrading the module from the Apps menu. Debug logging can be enabled via Odoo CLI: `--log-level=debug --log-handler=odoo.addons.payment_hitpay:DEBUG`.

## Branch model — important

This repo uses **per-Odoo-version branches** (`15.0`, `16.0`, `17.0`, `18.0`, `19.0`) that are intentionally **independent**. `main` tracks the latest active version (currently 19.0).

- Never merge version branches into each other. They diverge because of Odoo API breaks between versions.
- When fixing a bug that affects multiple versions, land it on the latest affected version branch first, then cherry-pick down. Some fixes can't be backported due to API differences — don't force it.
- When making a release, bump the `version` field in the module's `__manifest__.py` (format: `<odoo-version>.0.0.<patch>`, e.g. `19.0.0.1`) and update `CHANGELOG.md` in that branch.
- PRs target the version branch, not `main`.

The current branch is `main` (Odoo 19.0). API patterns below describe the 19.0 surface — older branches use older Odoo APIs (e.g. pre-19 payment provider hooks, different POS asset bundles, different OWL component conventions).

## Architecture: `payment_hitpay` (e-commerce)

Standard Odoo payment-provider extension pattern. Flow:

1. `models/payment_provider.py` — adds `hitpay` to the `payment.provider.code` selection, stores `hitpay_api_key` / `hitpay_api_salt`, and exposes `_hitpay_make_request()` (HTTP to `https://api.hit-pay.com/v1` or sandbox) and `_hitpay_calculate_signature()` (HMAC-SHA256 over alphabetically-sorted, concatenated `key+value` pairs, excluding `hmac` itself — used to verify webhooks).
2. `models/payment_transaction.py::_get_specific_rendering_values` is the entry point on checkout: calls `POST /payment-requests`, stores `hitpay_payment_request_id`, returns `api_url` for the redirect form.
3. `views/payment_hitpay_templates.xml` defines the `redirect_form` template — a bare `<form>` whose action is HitPay's hosted checkout URL. Odoo auto-submits it.
4. `controllers/main.py::HitpayController` exposes:
   - `/payment/hitpay/return` — browser redirect after checkout. Routes the user to `/payment/status` or back to `/shop/payment` on cancel.
   - `/payment/hitpay/webhook` — server-to-server notification. Verifies signature via `_verify_notification_signature`, then calls `tx_sudo._process('hitpay', data)` which dispatches to `_apply_updates`.
5. `_apply_updates` maps HitPay statuses (`pending` / `completed` / `canceled` / `failed` / `null`) to Odoo transaction states via `const.TRANSACTION_STATUS_MAPPING`.
6. Refunds go through `_send_refund_request` → `POST /refund` with a negative amount. Refund metadata is mirrored onto `account.payment` (see `models/account_payment.py::action_post`) and, if the source is a POS order, onto the matching `account.payment` row keyed by `pos_order_id`.

`post_init_hook` / `uninstall_hook` in `__init__.py` call `setup_provider` / `reset_payment_provider` from `odoo.addons.payment` so the provider is properly registered/unregistered.

## Architecture: `pos_hitpay` (POS terminal)

Adds `pos_hitpay` as a `use_payment_terminal` option on `pos.payment.method`. The frontend (OWL/JS) drives the flow; the Python side acts as a CORS-free proxy to HitPay's API.

Backend (Python):
- `models/pos_payment_method.py` — adds the `pos_hitpay` selection, fields (`pos_hitpay_api_key`, `pos_hitpay_api_salt`, `pos_hitpay_test_mode`, `pos_hitpay_terminal_identifier`, `pos_hitpay_latest_response`), and three RPC methods called from JS: `request_payment`, `get_latest_pos_hitpay_status`, `delete_payment`. These are `@api.model` deliberately — see the docstring on `request_payment`: it avoids row-level locking on `pos.payment.method` so HitPay's webhook-driven write to `pos_hitpay_latest_response` doesn't deadlock against an in-flight payment request.
- `models/hitpaypos_client.py` — thin requests-based client: `createPaymentRequest`, `getPaymentStatus`, `deletePaymentRequest`, `refundPayment`. Note: this class is used in an unusual style — `self.hitpayPosClient = hitpaypos_client.HitpayPosClient` (the class, not an instance) and calls pass `self.hitpayPosClient` as the first arg manually (e.g. `self.hitpayPosClient.createPaymentRequest(self.hitpayPosClient, payment_method, data)`). When editing methods on this class, preserve that calling convention or change all call sites.
- `models/pos_order.py::refund_payment` — looks up the original `pos.payment.hitpay_paymentId` for the refunded order line, then calls `refundPayment`.
- `controllers/main.py::PosHitpayController` — single endpoint `/pos/hitpay/webhook` (jsonrpc, `auth='none'`). It just buffers the latest HitPay payload onto `pos_hitpay_latest_response`; the frontend polling loop is the source of truth, not the webhook.

Frontend (OWL, in `static/src/js/`):
- `models.js` — registers `PaymentPosHitpay` via `register_payment_method("pos_hitpay", ...)` and patches `PosPayment` to add `hitpayInvoiceId` get/set helpers.
- `payment_hitpay_pos.js` — `PaymentPosHitpay extends PaymentInterface`. Implements:
  - `sendPaymentRequest` → branches on `order.isRefund`. For refunds calls `pos.order.refund_payment`; for sales calls `pos.payment.method.request_payment`, then enters a 5.5-second polling loop (`start_get_status_polling` → `_poll_for_response` → `get_latest_pos_hitpay_status`) until status flips to `completed` / `failed` / `canceled`.
  - `sendPaymentCancel` → calls `pos.payment.method.delete_payment` to delete the pending HitPay payment request.
- `PaymentScreen.js` — likely overrides POS payment screen behavior (refund handling); read it before changing refund UX.

Asset registration is in `__manifest__.py` under `assets['point_of_sale._assets_pos']` — any new JS/XML must be added there to be loaded by the POS bundle. The `pos.payment.method` writeable-field allowlist in `_is_write_forbidden` permits `pos_hitpay_latest_response` so the webhook can update it after a session has started.

## Conventions and gotchas worth knowing

- API base URLs are picked from `state == 'test'` (e-commerce) or `pos_hitpay_test_mode` (POS): sandbox is `api.sandbox.hit-pay.com/v1`, production is `api.hit-pay.com/v1`.
- The HMAC signing scheme used by `_hitpay_calculate_signature` is custom: alphabetical sort of keys, concatenate `key + value` (no separators), HMAC-SHA256 with the salt. Don't change it without coordinating with HitPay's webhook senders.
- The `payment_hitpay/data/neutralize.sql` file is what Odoo runs when neutralizing a DB clone — keep field names in sync with `payment_provider.py` (a past bug shipped with `hitpay_api_salty` instead of `hitpay_api_salt`; see CHANGELOG).
- `getCustomerName` / `getCustomerEmail` deliberately substitute `'NA'` / `'na@notapplicable.com'` when blank — HitPay's API rejects empty values for these fields.
- Refund amounts are passed as negative numbers (`-self.amount`, `data['amount'] * -1`). Don't "fix" this by taking `abs()`.
- `pos.order.refund_payment` returns `{'status': 'success'|'error', ...}` — the JS layer branches on `result.status` and shows an `AlertDialog` on error. Preserve that envelope.

## Reference files

- `CONTRIBUTING.md` — branch workflow, release/tagging steps, PR target rules.
- `CHANGELOG.md` — per-version, per-module release notes; update when shipping a release.
- `README.rst` — user-facing setup/install instructions.
