-- Neutralize HitPay Subscription credentials
UPDATE payment_provider
SET hitpay_subscription_api_key = NULL,
    hitpay_subscription_api_salt = NULL,
    hitpay_webhook_event_salt = NULL
WHERE code = 'hitpay_subscription';
