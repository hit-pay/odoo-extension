# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
import re

import requests
from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment_hitpay_subscription import const
from odoo.addons.payment_hitpay_subscription.controllers.main import HitpaySubscriptionController
from odoo.addons.payment_hitpay_subscription.exceptions import HitPayAPIError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[(const.PROVIDER_CODE, "HitPay Payment Gateway Subscription")],
        ondelete={const.PROVIDER_CODE: 'set default'}
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
    
    hitpay_debug_logging = fields.Boolean(
        string="API Logging",
        default=False,
        help=(
            "Log sanitized HitPay API requests and responses "
            "for troubleshooting."
        ),
    )
    
    _WEBHOOK_TRIGGER_FIELDS = {
        "state",
        "hitpay_subscription_api_key",
    }
    
    def _clear_webhook_credentials(self):
        """Clear the locally stored HitPay webhook lifecycle data."""
        self.ensure_one()

        super(PaymentProvider, self).write({
            "hitpay_webhook_event_id": False,
            "hitpay_webhook_event_salt": False,
        })
        
    def _write_webhook_credentials(self, webhook_id, webhook_salt):
        """Persist webhook lifecycle data without triggering provider write hooks."""
        self.ensure_one()

        super(PaymentProvider, self).write({
            "hitpay_webhook_event_id": webhook_id or False,
            "hitpay_webhook_event_salt": webhook_salt or False,
        })
        
    def _get_webhook(self, webhook_id):
        """Retrieve a HitPay webhook."""
        self.ensure_one()

        return self._hitpay_make_request(
            f"/webhook-events/{webhook_id}",
            method="GET",
        )
        
    def _get_webhooks(self):
        """Retrieve HitPay webhooks."""
        self.ensure_one()

        return self._hitpay_make_request(
            "/webhook-events",
            method="GET",
        )
        
    def _create_webhook(self):
        """Create the HitPay webhook and persist its ID and salt."""
        self.ensure_one()

        event = self._hitpay_make_request(
            "/webhook-events",
            payload=self._prepare_webhook_payload(),
            method="POST",
            content_type=const.CONTENT_TYPE_JSON,
        )
        
        if not isinstance(event, dict):
            raise ValidationError(
                _("HitPay returned an invalid webhook creation response.")
            )

        webhook_id = event.get("id")
        webhook_salt = event.get("salt")

        if not webhook_id or not webhook_salt:
            raise ValidationError(
                _(
                    "HitPay webhook creation did not return "
                    "the webhook ID and salt."
                )
            )

        self._write_webhook_credentials(
            webhook_id,
            webhook_salt,
        )

        return event
        
    def _update_webhook(self, webhook_id):
        """Update the HitPay webhook while preserving the local webhook salt."""
        self.ensure_one()

        event = self._hitpay_make_request(
            f"/webhook-events/{webhook_id}",
            payload=self._prepare_webhook_payload(),
            method="PUT",
            content_type=const.CONTENT_TYPE_JSON,
        )

        if (
            not isinstance(event, dict)
            or not event.get("id")
            or str(event["id"]) != str(webhook_id)
        ):
            raise ValidationError(
                _(
                    "HitPay returned an invalid webhook update response: "
                    "unexpected webhook ID."
                )
            )

        return event
        
    def _register_webhook(self):
        """Synchronize the provider webhook with HitPay."""
        self.ensure_one()

        webhook_id = self.hitpay_webhook_event_id

        if not webhook_id:
            return self._replace_webhooks_for_url()

        try:
            existing_webhook = self._get_webhook(webhook_id)

        except HitPayAPIError as error:
            if error.status_code == 404:
                self._clear_webhook_credentials()
                return self._replace_webhooks_for_url()

            raise

        if not isinstance(existing_webhook, dict):
            raise ValidationError(
                _("HitPay returned an invalid webhook response.")
            )

        if not existing_webhook.get("id"):
            raise ValidationError(
                _(
                    "HitPay returned an invalid webhook response: "
                    "missing webhook ID."
                )
            )

        if str(existing_webhook["id"]) != str(webhook_id):
            raise ValidationError(
                _("HitPay returned an unexpected webhook ID.")
            )

        if "url" not in existing_webhook:
            raise ValidationError(
                _(
                    "HitPay returned an invalid webhook response: "
                    "missing webhook URL."
                )
            )

        if not self.hitpay_webhook_event_salt:
            try:
                self._delete_remote_webhook(
                    api_url=self._get_api_url(),
                    api_key=self.hitpay_subscription_api_key,
                    webhook_id=webhook_id,
                )

            except HitPayAPIError as error:
                if error.status_code != 404:
                    raise

            self._clear_webhook_credentials()

            return self._replace_webhooks_for_url()

        webhook_url = self._get_webhook_url()

        if str(existing_webhook["url"]) != webhook_url:
            return self._update_webhook(webhook_id)

        return existing_webhook
        
    def _replace_webhooks_for_url(self):
        """
        Delete existing HitPay webhooks registered for this URL,
        then create a new webhook.

        A webhook disappearing between GET and DELETE is harmless.
        """
        self.ensure_one()

        webhook_url = self._get_webhook_url()

        webhooks = self._get_webhooks()

        if not isinstance(webhooks, list):
            raise ValidationError(
                _("HitPay returned an invalid webhook list response.")
            )

        for webhook in webhooks:
            if not isinstance(webhook, dict):
                continue

            webhook_id = webhook.get("id")
            remote_url = webhook.get("url")

            if (
                webhook_id
                and remote_url is not None
                and str(remote_url) == webhook_url
            ):
                try:
                    self._delete_remote_webhook(
                        api_url=self._get_api_url(),
                        api_key=self.hitpay_subscription_api_key,
                        webhook_id=webhook_id,
                    )

                except HitPayAPIError as error:
                    if error.status_code != 404:
                        raise

        return self._create_webhook()
        
    def _delete_remote_webhook(
        self,
        *,
        api_url,
        api_key,
        webhook_id,
    ):
        """
        Delete a remote HitPay webhook using explicit credentials.

        This method does not modify the provider's locally stored webhook fields.
        """
        self.ensure_one()

        if not webhook_id:
            return

        self._hitpay_make_request(
            f"/webhook-events/{webhook_id}",
            method="DELETE",
            api_url=api_url,
            api_key=api_key,
        )

        _logger.info(
            "Deleted HitPay webhook event %s.",
            webhook_id,
        )
    
    def _ensure_webhook_event(self):
        """Synchronize the provider webhook with HitPay."""
        self.ensure_one()

        if self.state == "disabled":
            return False

        return self._register_webhook()
        
    def write(self, vals):
        """
        Synchronize the HitPay webhook when the API key or environment changes,
        when the provider is disabled, and on relevant configuration saves.

        When credentials or environment change, create the replacement webhook
        before deleting the previous remote webhook. This prevents an Odoo
        transaction rollback from restoring provider configuration that points
        to a webhook that was already deleted remotely.
        """
        old_values = {
            provider.id: {
                "api_url": provider._get_api_url(),
                "api_key": provider.hitpay_subscription_api_key,
                "webhook_id": provider.hitpay_webhook_event_id,
                "state": provider.state,
            }
            for provider in self
        }

        res = super().write(vals)

        if not self._WEBHOOK_TRIGGER_FIELDS.intersection(vals):
            return res

        for provider in self.filtered(
            lambda p: p.code == const.PROVIDER_CODE
        ):
            old = old_values[provider.id]

            credentials_changed = (
                old["api_key"]
                != provider.hitpay_subscription_api_key
            )

            environment_changed = (
                old["api_url"]
                != provider._get_api_url()
            )

            became_disabled = (
                old["state"] != "disabled"
                and provider.state == "disabled"
            )

            # Provider disabled:
            #
            # No replacement webhook is required. Delete the previous remote
            # webhook using the previous credentials/environment, then clear the
            # local webhook credentials.
            if became_disabled:
                if old["webhook_id"] and old["api_key"]:
                    try:
                        provider._delete_remote_webhook(
                            api_url=old["api_url"],
                            api_key=old["api_key"],
                            webhook_id=old["webhook_id"],
                        )
                    except HitPayAPIError as error:
                        if error.status_code != 404:
                            _logger.warning(
                                "Failed to delete previous HitPay webhook event %s. "
                                "Reason: %s",
                                old["webhook_id"],
                                str(error),
                            )

                provider._clear_webhook_credentials()
                continue

            # Credentials/environment changed:
            #
            # 1. Clear the old local webhook credentials.
            # 2. Create a replacement webhook using the new configuration.
            # 3. Only after successful creation, delete the previous webhook.
            #
            # If replacement creation fails, ValidationError causes the database
            # transaction to roll back. Since the previous remote webhook has not
            # yet been deleted, the restored provider configuration remains valid.
            if credentials_changed or environment_changed:
                provider._clear_webhook_credentials()

                try:
                    provider._ensure_webhook_event()
                except HitPayAPIError as error:
                    raise ValidationError(str(error)) from None

                # The replacement webhook now exists. Delete the previous remote
                # webhook using the previous credentials/environment.
                if old["webhook_id"] and old["api_key"]:
                    try:
                        provider._delete_remote_webhook(
                            api_url=old["api_url"],
                            api_key=old["api_key"],
                            webhook_id=old["webhook_id"],
                        )
                    except HitPayAPIError as error:
                        if error.status_code != 404:
                            _logger.warning(
                                "Failed to delete previous HitPay webhook event %s. "
                                "Reason: %s",
                                old["webhook_id"],
                                str(error),
                            )

                continue

            # Relevant configuration save without a lifecycle change:
            #
            # Validate the existing webhook and synchronize its callback URL when
            # required.
            if provider.state != "disabled":
                try:
                    provider._ensure_webhook_event()
                except HitPayAPIError as error:
                    raise ValidationError(str(error)) from None

        return res
        
    @api.model_create_multi
    def create(self, vals_list):
        """Create providers and register the HitPay webhook when enabled."""
        providers = super().create(vals_list)

        for provider in providers.filtered(
            lambda p: (
                p.code == const.PROVIDER_CODE
                and p.state != "disabled"
            )
        ):
            try:
                provider._ensure_webhook_event()
            except HitPayAPIError as error:
                raise ValidationError(str(error)) from None

        return providers
        
    def unlink(self):
        """Delete managed HitPay webhooks after removing provider records."""
        webhook_data = [
            {
                "api_url": provider._get_api_url(),
                "api_key": provider.hitpay_subscription_api_key,
                "webhook_id": provider.hitpay_webhook_event_id,
            }
            for provider in self.filtered(
                lambda p: (
                    p.code == const.PROVIDER_CODE
                    and p.hitpay_webhook_event_id
                    and p.hitpay_subscription_api_key
                )
            )
        ]

        # Delete the provider records first.
        #
        # If unlink is blocked by Odoo constraints, access rules, or another
        # exception, no remote webhook has been deleted.
        res = super().unlink()

        # The local deletion succeeded. Perform best-effort remote cleanup.
        #
        # Do not raise here: an external API failure cannot safely restore the
        # already-deleted Odoo provider records.
        for data in webhook_data:
            try:
                self.env["payment.provider"]._delete_remote_webhook(
                    api_url=data["api_url"],
                    api_key=data["api_key"],
                    webhook_id=data["webhook_id"],
                )
            except HitPayAPIError as error:
                if error.status_code != 404:
                    _logger.warning(
                        "Failed to delete HitPay webhook event %s after deleting "
                        "the payment provider. Reason: %s",
                        data["webhook_id"],
                        str(error),
                    )

        return res
        
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
        api_url=None,
        api_key=None,
    ):
        """Make a request to the HitPay API."""
        self.ensure_one()
        
        effective_api_url = api_url or self._get_api_url()
        
        url = effective_api_url + endpoint
        
        environment = (
            "sandbox"
            if effective_api_url == const.API_SANDBOX_URL
            else "live"
        )

        headers = self._get_request_headers(api_key=api_key)

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

        self._log_hitpay_request(
            environment,
            method,
            endpoint,
            payload,
        )

        try:
            response = requests.request(
                method,
                url,
                **request_kwargs,
            )

        except requests.exceptions.RequestException as error:
            self._log_hitpay_request_failure(
                environment,
                method,
                endpoint,
                None,
                error,
            )

            self._raise_api_error(
                "HitPay Subscription: "
                + _("Could not establish the connection to the API."),
                status_code=0,
            )

        try:
            response_content = response.json()
        except ValueError:
            response_content = {
                "_raw_response": response.text,
            }

        try:
            response.raise_for_status()

        except requests.exceptions.HTTPError as error:
            self._log_hitpay_request_failure(
                environment,
                method,
                endpoint,
                response,
                error,
                response_content,
            )

            # Keep an ERROR log regardless of the provider debug setting.
            _logger.error(
                "HitPay HTTP %s for %s.",
                response.status_code,
                self._sanitize_hitpay_endpoint(endpoint),
            )

            error_code = (
                response_content.get("error")
                if isinstance(response_content, dict)
                else None
            )

            error_message = (
                response_content.get("message")
                if isinstance(response_content, dict)
                else None
            )

            self._raise_api_error(
                "HitPay Subscription: "
                + _(
                    "The communication with the API failed. "
                    "HitPay Payment Gateway gave us the following "
                    "information: '%s' (code %s)",
                    error_message,
                    error_code,
                ),
                status_code=response.status_code,
                response_data=response_content,
            )

        self._log_hitpay_response(
            environment,
            method,
            endpoint,
            response,
            response_content,
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
        
    def _get_request_headers(self, api_key=None):
        return {
            "X-Requested-With": "XMLHttpRequest",
            "X-BUSINESS-API-KEY": api_key or self.hitpay_subscription_api_key,
        }
        
    def _raise_api_error(
        self,
        message,
        *,
        status_code=0,
        response_data=None,
    ):
        raise HitPayAPIError(
            message,
            status_code=status_code,
            response_data=response_data,
        )
        
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

        sale_order = self.env["sale.order"].browse(sale_order_id).exists()

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
        
    def _sanitize_debug_data(self, data):
        """Return API data with sensitive values redacted for logging."""
        sensitive_keys = {
            "api_key",
            "api_secret",
            "authorization",
            "salt",
            "signature",
            "card_number",
            "card",
            "cvv",
            "cvc",
            "email",
            "phone",
            "phone_number",
            "name",
            "first_name",
            "last_name",
            "customer_name",
            "customer_email",
            "buyer_phone",
            "buyer_email",
            "webhook",
            'url',
            'return_url',
            'customer_phone_number',
        }

        if isinstance(data, dict):
            return {
                key: (
                    "[REDACTED]"
                    if str(key).lower() in sensitive_keys
                    else self._sanitize_debug_data(value)
                )
                for key, value in data.items()
            }

        if isinstance(data, list):
            return [
                self._sanitize_debug_data(value)
                for value in data
            ]
            
        if isinstance(data, str):
            data = re.sub(
                r"(?<=/charge/recurring-billing/)[^/?#\s]+",
                "<redacted>",
                data,
            )

            data = re.sub(
                r"(?<=/webhook-events/)[^/?#\s]+",
                "<redacted>",
                data,
            )

            # HitPay 404 responses can include:
            #
            # No query results for Webhook #<webhook_id>
            data = re.sub(
                r"(?i)(Webhook\s+#)[^\s'\"/]+",
                r"\1<redacted>",
                data,
            )

        return data

    def _log_hitpay_request(
        self,
        environment,
        method,
        endpoint,
        payload,
    ):
        """Log a sanitized HitPay API request."""
        self.ensure_one()
        
        if not self.hitpay_debug_logging:
            return

        _logger.info(
            "HitPay API [%s] request: %s %s. Payload: %s",
            environment,
            method,
            self._sanitize_hitpay_endpoint(endpoint),
            self._sanitize_debug_data(payload),
        )


    def _log_hitpay_response(
        self,
        environment,
        method,
        endpoint,
        response,
        data,
    ):
        """Log a sanitized HitPay API response."""
        self.ensure_one()
        
        if not self.hitpay_debug_logging:
            return

        _logger.info(
            "HitPay API [%s] response: %s %s. Status: %s. Response: %s",
            environment,
            method,
            self._sanitize_hitpay_endpoint(endpoint),
            response.status_code,
            pprint.pformat(
                self._sanitize_debug_data(data)
            ),
        )


    def _log_hitpay_request_failure(
        self,
        environment,
        method,
        endpoint,
        response,
        error,
        data=None,
    ):
        """Log a sanitized HitPay API request failure."""
        self.ensure_one()

        status_code = (
            response.status_code
            if response is not None
            else 0
        )

        # requests HTTPError messages may contain the complete request URL,
        # including sensitive identifiers in endpoint path parameters.
        #
        # For HTTP failures, log only the exception class. The status code,
        # sanitized endpoint, and sanitized response payload provide the
        # necessary diagnostic information.
        error_reason = (
            type(error).__name__
            if response is not None
            else str(error)
        )

        _logger.warning(
            "HitPay API [%s] failure: %s %s. Status: %s. "
            "Reason: %s. Response: %s",
            environment,
            method,
            self._sanitize_hitpay_endpoint(endpoint),
            status_code,
            error_reason,
            pprint.pformat(
                self._sanitize_debug_data(data)
            ),
        )
        
    def _sanitize_hitpay_endpoint(self, endpoint):
        """Redact sensitive identifiers from HitPay API endpoint paths."""
        self.ensure_one()

        if not endpoint:
            return endpoint

        endpoint = str(endpoint)

        # Redact recurring billing identifiers.
        #
        # /charge/recurring-billing/{recurring_id}
        # ->
        # /charge/recurring-billing/<redacted>
        endpoint = re.sub(
            r"(?<=/charge/recurring-billing/)[^/?#]+",
            "<redacted>",
            endpoint,
        )

        # Redact webhook identifiers.
        #
        # /webhook-events/{webhook_id}
        # ->
        # /webhook-events/<redacted>
        endpoint = re.sub(
            r"(?<=/webhook-events/)[^/?#]+",
            "<redacted>",
            endpoint,
        )

        return endpoint      

