# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields

class PaymentToken(models.Model):
    _inherit = "payment.token"

    hitpay_recurring_billing_id = fields.Char(
        string="HitPay Recurring Billing ID",
        readonly=True,
        index=True,
    )

    hitpay_method_status = fields.Selection(
        [
            ("active", "Active"),
            ("detached", "Detached"),
        ],
        string="HitPay Method Status",
        default="active",
    )