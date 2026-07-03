from . import controllers
from . import models

from odoo.addons.payment import setup_provider, reset_payment_provider
from odoo.addons.payment_hitpay_subscription import const

def post_init_hook(env):
    """Register the HitPay Subscription payment provider."""
    setup_provider(env, const.PROVIDER_CODE)


def uninstall_hook(env):
    """Reset the HitPay Subscription payment provider."""
    reset_payment_provider(env, const.PROVIDER_CODE)