PROVIDER_CODE = "hitpay_subscription"

DEFAULT_PAYMENT_METHOD_CODES = (
    PROVIDER_CODE,
)

TRANSACTION_STATUS_MAPPING = {
    "pending": ("pending",),
    "done": ("completed", "succeeded"),
    "canceled": ("canceled", "failed", "null"),
}

REQUEST_TIMEOUT = 20

CONTENT_TYPE_FORM = "form"
CONTENT_TYPE_JSON = "json"

API_BASE_URL = "https://api.hit-pay.com/v1"
API_SANDBOX_URL = "https://api.sandbox.hit-pay.com/v1"

WEBHOOK_EVENT_TYPES = (
    "charge.created",
    "recurring_billing.method_attached",
    "recurring_billing.method_detached",
)

DEFAULT_WEBHOOK_NAME = "Odoo Subscription"
DEFAULT_SUBSCRIPTION_NAME = "Odoo Subscription"