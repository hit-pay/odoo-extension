# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hmac
import logging
import pprint
import hashlib

from werkzeug.exceptions import Forbidden

from odoo import _, http
from odoo.http import request

from odoo.addons.payment_hitpay_subscription import const


_logger = logging.getLogger(__name__)


class HitpaySubscriptionController(http.Controller):
    _return_url = '/payment/hitpay/subscription/return'
    _webhook_url = '/payment/hitpay/subscription/webhook'

    @http.route(_return_url, type='http', methods=['GET'], auth='public')
    def hitpay_subscription_return_from_checkout(self, **data):
        """ Process the notification data sent by Hitpay after redirection from checkout.

        :param dict data: The notification data.
        """
        # Handle the notification data.
        _logger.info("Handling redirection from Hitpay Subscription with data:\n%s", pprint.pformat(data))
     
        if data.get('status') != 'canceled':
            return request.redirect('/payment/status')
        else:
            return request.redirect('/shop/payment')

    @http.route(_webhook_url, type='http', auth='public', methods=['POST'], csrf=False)
    def hitpay_subscription_webhook(self, **kwargs):

        raw_body = request.httprequest.get_data()

        headers = request.httprequest.headers

        signature = headers.get("Hitpay-Signature")
        event_type = headers.get("Hitpay-Event-Type")
        event_object = headers.get("Hitpay-Event-Object")

        payload = request.get_json_data()

        providers = request.env["payment.provider"].sudo().search([
            ("code", "=", const.PROVIDER_CODE),
            ("state", "!=", "disabled"),
        ])

        if not providers:
            _logger.error("HitPay Subscription provider not found.")
            return "OK"

        provider = None
        for candidate in providers:
            try:
                self._verify_signature(
                    candidate.hitpay_webhook_event_salt,
                    raw_body,
                    signature,
                )
                provider = candidate
                break
            except Forbidden:
                continue

        if not provider:
            _logger.error("No provider with valid webhook signature found.")
            raise Forbidden("Invalid webhook signature")

        if event_object == "recurring_billing":
            if event_type == "method_attached":
                return self._handle_method_attached(provider, payload)

            elif event_type == "method_detached":
                return self._handle_method_detached(provider, payload)

        elif event_object == "charge":
            if event_type == "created":
                return self._handle_charge_created(provider, payload)

        return "OK"
        
    @staticmethod
    def _verify_signature(salt, raw_body, received_signature):
        if not received_signature:
            raise Forbidden("Missing webhook signature")

        if not salt:
            raise Forbidden("Missing webhook salt")

        received_signature = received_signature.strip()

        expected_signature = hmac.new(
            str(salt).encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest().strip()

        if not hmac.compare_digest(expected_signature, received_signature):
            _logger.warning(
                "Invalid webhook signature.\nExpected: %r\nReceived: %r",
                expected_signature,
                received_signature,
            )
            raise Forbidden("Invalid webhook signature")
           
    def _handle_method_attached(self, provider, payload):
        try:
            recurring_id = payload["recurring_billing"]["id"]
            payment_method = payload["recurring_billing"]["payment_method"]
        except KeyError as e:
            _logger.error(
                "Malformed method_attached webhook payload, missing key: %s\n%s",
                e,
                pprint.pformat(payload),
            )
            return "OK"

        card_data = payment_method.get("card")

        if card_data:
            brand = card_data.get("brand", "Card")
            last4 = card_data.get("last4", "****")
            payment_details = f"{brand.upper()} ****{last4}"
        else:
            method_type = payment_method.get("type", "Payment Method")
            payment_details = method_type.title()
        
        tx = request.env["payment.transaction"].sudo().search([
            ("hitpay_recurring_billing_id", "=", recurring_id),
            ("provider_id", "=", provider.id),
        ], limit=1)
        
        if not tx:
            _logger.warning(
                "No transaction found for recurring billing id %s",
                recurring_id,
            )
            return "OK"
        
        existing = request.env["payment.token"].sudo().search([
                ("provider_id", "=", tx.provider_id.id),
                ("provider_ref", "=", recurring_id),
            ], limit=1)
            
        token = existing

        if not token:
            token = request.env["payment.token"].sudo().create({
                "provider_id": tx.provider_id.id,
                "partner_id": tx.partner_id.id,
                "payment_method_id": tx.payment_method_id.id,
                "provider_ref": recurring_id,
                "payment_details": payment_details,
                "hitpay_recurring_billing_id":recurring_id,
            })
            
            _logger.info(
                "Created payment token for recurring billing %s",
                recurring_id,
            )
        else:
            _logger.info(
                "Reusing existing payment token for recurring billing %s",
                recurring_id,
            )
        
        tx.token_id = token

        tx._charge_recurring_billing(recurring_id)

        return "OK"
        
    def _handle_charge_created(self, provider, payload):
        """Handle recurring charge notifications.

        Recurring charges are processed synchronously from the response of
        /charge/recurring-billing/{id} in `_send_payment_request()` and
        `_handle_method_attached()`.

        HitPay does not allow passing a merchant reference when creating a
        recurring charge, therefore the `charge.created` webhook cannot be
        reliably correlated with an Odoo transaction and is acknowledged only.
        """
        try:
            payment_id = payload["id"]
        except KeyError as e:
            _logger.error(
                "Malformed charge_created webhook payload, missing key: %s\n%s",
                e,
                pprint.pformat(payload),
            )
            return "OK"

        _logger.info(
            "Ignoring recurring charge webhook for payment %s. "
            "Recurring charge already processed synchronously.",
            payment_id,
        )

        return "OK"
        
    def _handle_method_detached(self, provider, payload):
        """
        Archive/remove payment.token
        """
        try:
            recurring_id = payload["recurring_billing"]["id"]
        except KeyError as e:
            _logger.error(
                "Malformed method_detached webhook payload, missing key: %s\n%s",
                e,
                pprint.pformat(payload),
            )
            return "OK"

        token = request.env["payment.token"].sudo().search([
            ("provider_id", "=", provider.id),
            ("provider_ref", "=", recurring_id),
        ], limit=1)
        
        if token:
            token.write({
                "active": False,
                "hitpay_method_status": "detached",
            })
            token.partner_id.message_post(
                body=_(
                    "The saved HitPay payment method has been detached by the customer "
                    "and can no longer be used for automatic renewals."
                )
            )
            
            _logger.info(
                "Detached recurring payment method %s",
                recurring_id,
            )
        
        return "OK"
