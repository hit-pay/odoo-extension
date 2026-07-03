# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

import requests
from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment_hitpay_subscription import const
from odoo.addons.payment_hitpay_subscription.controllers.main import HitpaySubscriptionController


_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[(const.PROVIDER_CODE, "HitPay Payment Gateway Subscription")], ondelete={const.PROVIDER_CODE: 'set default'}
    )

    hitpay_subscription_api_key = fields.Char(
        string="API Key", 
        required_if_provider=const.PROVIDER_CODE)
    
    hitpay_subscription_api_salt = fields.Char(
        string="Salt",
        required_if_provider=const.PROVIDER_CODE,
        groups='base.group_system')
        
    hitpay_webhook_event_id = fields.Char(
        string="HitPay Webhook Event ID",
        copy=False,
    )
    
    hitpay_webhook_event_salt = fields.Char(
        string="HitPay Webhook Event Salt",
        copy=False,
        groups='base.group_system',
    )
        
    def _ensure_webhook_event(self):

        self.ensure_one()

        existing = self._get_existing_webhook()

        if existing:
            return existing

        return self._create_webhook()    
        
    def _get_existing_webhook(self):
        self.ensure_one()
        
        if self.hitpay_webhook_event_id:
            try:
                return self._hitpay_make_request(
                    f"/webhook-events/{self.hitpay_webhook_event_id}",
                    method="GET",
                )
            except ValidationError:
                self.write({
                    "hitpay_webhook_event_id": False,
                    "hitpay_webhook_event_salt": False,
                })

        events = self._hitpay_make_request(
            "/webhook-events",
            method="GET",
        )

        webhook_url = self._get_webhook_url()

        for event in events:
            if event.get("url") == webhook_url:
                self.write({
                    "hitpay_webhook_event_id": event["id"],
                    "hitpay_webhook_event_salt": event["salt"],
                })
                return event

        return False
 
    def _create_webhook(self):
 
        payload = self._prepare_webhook_payload()

        event = self._hitpay_make_request(
            "/webhook-events",
            payload=payload, 
            method='POST', 
            content_type='json'
        )
        
        self.write({
            "hitpay_webhook_event_id": event["id"],
            "hitpay_webhook_event_salt": event["salt"],
        })
       
        return event
        
    def write(self, vals):
        res = super().write(vals)

        watched = {
            "state",
            "hitpay_subscription_api_key",
            "hitpay_subscription_api_salt",
        }

        if watched.intersection(vals):
            providers = self.filtered(
                lambda p: p.code == const.PROVIDER_CODE
                and p.state != "disabled"
            )

            for provider in providers:
                provider._ensure_webhook_event()

        return res
        
    @api.model_create_multi
    def create(self, vals_list):
        providers = super().create(vals_list)

        for provider in providers.filtered(
            lambda p: p.code == const.PROVIDER_CODE
            and p.state != "disabled"
        ):
            provider._ensure_webhook_event()

        return providers
  
    def _get_api_url(self):
        return const.API_SANDBOX_URL if self.state == "test" else const.API_BASE_URL

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        
        self.filtered(
            lambda p: p.code == const.PROVIDER_CODE
        ).update({
            "support_tokenization": True,
            "support_manual_capture": False,
            "support_express_checkout": False,
        })    
    
    def _hitpay_make_request(
        self,
        endpoint,
        payload=None,
        method="POST",
        content_type=const.CONTENT_TYPE_FORM,
    ):
        """ Make a request to HitPay API at the specified endpoint.

        Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request.
        :param dict payload: The payload of the request.
        :param str method: The HTTP method of the request.
        :return The JSON-formatted content of the response.
        :rtype: dict
        :raise ValidationError: If an HTTP error occurs.
        """
        self.ensure_one()

        url = self._get_api_url() + endpoint

        headers = self._get_request_headers()
        
        request_kwargs = {
            "headers": headers,
            "timeout": const.REQUEST_TIMEOUT,
        }

        if method == "GET":
            request_kwargs["params"] = payload

        elif content_type == const.CONTENT_TYPE_JSON:
            headers["Content-Type"] = "application/json"
            request_kwargs["json"] = payload

        else:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            request_kwargs["data"] = payload
		
        try:

            _logger.debug(
                "[HitPay][%s] %s %s\n%s",
                self.state,
                method,
                endpoint,
                pprint.pformat(payload),
            )

            response = requests.request(
                method,
                url,
                **request_kwargs,
            )

            try:
                response_content = response.json()
            except ValueError:
                response_content = {}

            _logger.debug(
                "[HitPay][%s] Response %s\n%s",
                self.state,
                endpoint,
                pprint.pformat(response_content),
            )
            
            try:
                response.raise_for_status()
                        
            except requests.exceptions.HTTPError:
                _logger.exception(
                    "HitPay HTTP %s for %s",
                    response.status_code,
                    endpoint,
                )
                error_code = response_content.get('error')
                error_message = response_content.get('message')
                self._raise_api_error("HitPay Subscription: " + _(
                    "The communication with the API failed. HitPay Payment Gateway gave us the following "
                    "information: '%s' (code %s)", error_message, error_code
                ))
        except requests.exceptions.RequestException:
            _logger.exception("Unable to reach endpoint at %s", url)
            self._raise_api_error(
                "HitPay Subscription: " + _("Could not establish the connection to the API.")
            )
 
        return response_content

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != const.PROVIDER_CODE:
            return default_codes
        return const.DEFAULT_PAYMENT_METHOD_CODES
   
    def _get_webhook_url(self):
        return urls.url_join(
            self.get_base_url(),
            HitpaySubscriptionController._webhook_url,
        )
        
    def _get_return_url(self):
        return urls.url_join(
            self.get_base_url(),
            HitpaySubscriptionController._return_url
        )
    
    def _prepare_webhook_payload(self):
        webhook_url = self._get_webhook_url()
 
        return {
            "name": const.DEFAULT_WEBHOOK_NAME,
            "url": webhook_url,
            "event_types": list(const.WEBHOOK_EVENT_TYPES)
        }
        
    def _get_request_headers(self):
        return {
            "X-Requested-With": "XMLHttpRequest",
            "X-BUSINESS-API-KEY": self.hitpay_subscription_api_key,
        }
        
    def _raise_api_error(self, message):
        raise ValidationError(message)
        
    @api.model
    def _get_compatible_providers(
        self,
        company_id,
        partner_id,
        amount,
        currency_id=None,
        force_tokenization=False,
        is_express_checkout=False,
        is_validation=False,
        report=None,
        **kwargs,
    ):
        providers = super()._get_compatible_providers(
            company_id,
            partner_id,
            amount,
            currency_id=currency_id,
            force_tokenization=force_tokenization,
            is_express_checkout=is_express_checkout,
            is_validation=is_validation,
            report=report,
            **kwargs,
        )

        subscription_provider = providers.filtered(
            lambda p: p.code == const.PROVIDER_CODE
        )

        if not subscription_provider:
            return providers
            
        sale_order_id = kwargs.get("sale_order_id")
        
        if not sale_order_id:
            return providers
            
        sale_order = self.env["sale.order"].browse(sale_order_id)
            
        if not sale_order:
            return providers
        
        has_subscription = bool(
            sale_order.order_line.filtered("recurring_invoice")
        )
        
        has_token = bool(
            self.env["payment.token"].sudo().search_count(
                [
                    ("partner_id", "=", partner_id),
                    ("provider_id", "in", subscription_provider.ids),
                    ("active", "=", True),
                    ("hitpay_method_status", "=", "active"),
                ],
                limit=1,
            )
        )
        
        if not has_subscription and not has_token:
            providers -= subscription_provider
        
        return providers