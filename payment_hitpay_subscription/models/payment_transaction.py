# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, models, fields
from odoo.exceptions import ValidationError

from odoo.addons.payment_hitpay_subscription import const

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    hitpay_recurring_billing_id = fields.Char(
        string="HitPay Recurring Billing ID",
        copy=False,
        help="Temporary recurring billing identifier returned by HitPay before the payment token is created.",
    )
    
    def _get_specific_rendering_values(self, processing_values):
        """ Override of `payment` to return Hitpay-specific rendering values.

        Note: self.ensure_one() from `_get_rendering_values`.

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != const.PROVIDER_CODE:
            return res

        # Initiate the payment and retrieve the payment link data.
        payload = self._prepare_recurring_billing_payload()

        
        payment_response = self.provider_id._hitpay_make_request(
            '/recurring-billing', payload=payload
        )
        
        self.write({
            "hitpay_recurring_billing_id": payment_response["id"],
        })

        # Extract the payment link URL and embed it in the redirect form.
        return {
            "api_url": payment_response["url"],
        }

    def _prepare_recurring_billing_payload(self):
        """ Create the payload for the preference request based on the transaction values.

        :return: The request payload.
        :rtype: dict
        """
        
        return_url = self.provider_id._get_return_url()

        webhook_url = self.provider_id._get_webhook_url()

        return {
            'name': const.DEFAULT_SUBSCRIPTION_NAME,
            'reference': self.reference,
            'amount': self.amount,
            'currency': self.currency_id.name,
            'redirect_url': return_url,
            'webhook': webhook_url,
            'customer_name': self._get_customer_name(self.partner_name),
            'customer_email': self._get_customer_email(self.partner_email),
            'channel': 'api_odoo',
            'save_payment_method': 'true'
        }

    def _search_by_reference(self, provider_code, payment_data):

        """ Override of `payment` to find the transaction based on hitpay data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict payment_data: The normalized payment data sent by the provider
        :return: The transaction if found
        :rtype: payment.transaction
        :raise: ValidationError if the data match no transaction
        """
        
        tx = super()._search_by_reference(provider_code, payment_data)
        if provider_code != const.PROVIDER_CODE or len(tx) == 1:
            return tx

        payment_id = payment_data.get("id")

        if not payment_id:
            raise ValidationError(
                _("HitPay payment notification is missing required 'id' field.")
            )

        tx = self.sudo().search([
            ("provider_reference", "=", payment_id),
            ("provider_code", "=", const.PROVIDER_CODE),
        ], limit=1)

        if not tx:
            raise ValidationError(
                _("No HitPay transaction found for payment ID %s.") % payment_id
            )
        return tx

    def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data."""
        
        if self.provider_code != const.PROVIDER_CODE:
            return super()._apply_updates(payment_data)
  
        payment_status = payment_data.get("status")
        payment_id = payment_data.get("id")
        payment_amount = payment_data.get("amount")
        
        if not payment_id:
            self.provider_id._raise_api_error("Hitpay: Received data with missing payment id.")

        if not payment_status:
            self.provider_id._raise_api_error("Hitpay: Received data with missing status.")

        if payment_status in const.TRANSACTION_STATUS_MAPPING['pending']:
            message = (
                f"Payment is Pending. "
                f"Transaction ID: {payment_id}, "
                f"Amount Paid: {payment_amount}"
            )
            self._set_pending(state_message=message)
        elif payment_status in const.TRANSACTION_STATUS_MAPPING['done']:
            message = (
                f"Payment successful. "
                f"Transaction ID: {payment_id}, "
                f"Amount Paid: {payment_amount}"
            )
            self._set_done(state_message=message)
        elif payment_status in const.TRANSACTION_STATUS_MAPPING['canceled']:
            self._set_canceled()
        else:  # Classify unsupported payment status as the `error` tx state.
            _logger.warning(
                "Hitpay: Received data for transaction with invalid payment status: %s",
                 payment_status
            )
            self._set_error(
                "Hitpay: Received data with invalid status: "+payment_status
            )
    
    def _get_customer_name(self, customer_name):
        if customer_name and customer_name.strip():
            return customer_name

        return "NA"
    
    def _get_customer_email(self, customer_email):
        
        if customer_email and customer_email.strip():
            return customer_email

        login = self.env.user.login

        if login:
            return login

        return "na@notapplicable.com"
        
    def _extract_amount_data(self, payment_data):
        """Override of payment to extract the amount and currency from the payment data."""
        if self.provider_code != const.PROVIDER_CODE:
            return super()._extract_amount_data(payment_data)

        # Amount and currency are not sent in the payment data when redirecting to the return route.
        if 'amount' not in payment_data or 'currency' not in payment_data:
            return

        amount = payment_data['amount']
        return {
            'amount': float(amount),
            'currency_code': str(payment_data['currency']).upper(),
        }
        
    def _send_payment_request(self):
        
        if self.provider_code != const.PROVIDER_CODE:
            return super()._send_payment_request()

        recurring_id = self.token_id.provider_ref
        
        _logger.info(
            "SPS: Charging HitPay recurring billing %s",
            recurring_id,
        ) 

        payload = {
            'amount': self.amount,
            'currency': self.currency_id.name
        }
        
        response = self.provider_id._hitpay_make_request(
            f"/charge/recurring-billing/{recurring_id}",
            payload=payload,
        )
        
        payment_id = response.get("payment_id")
        
        if not payment_id:
            self.provider_id._raise_api_error(
                _("HitPay did not return a payment ID.")
            )
        
        if response.get("status") not in const.TRANSACTION_STATUS_MAPPING["done"]:
            self.provider_id._raise_api_error(
                _(
                    "SPS: HitPay Subscription charge failed for the recurring billing ID %s with status %s."
                ) % (
                    recurring_id,
                    response.get("status"),
                )
            )
            
        _logger.info(
            "SPS: Recurring charge created. Payment ID: %s",
            payment_id,
        )
        
        self.write({
            "provider_reference": payment_id,
        })
        
        response["currency_code"] = response["currency"]
        response["id"] = payment_id

        self._process(const.PROVIDER_CODE, response)
            
    def _is_tokenization_required(self, **kwargs):
        return True