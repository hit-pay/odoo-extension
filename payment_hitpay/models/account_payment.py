import logging
import pprint
from odoo import api, models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    hitpay_payment_status = fields.Char('Hitpay Transaction Status')
    hitpay_payment_id = fields.Char('Hitpay Payment ID')
    hitpay_transaction_id = fields.Char('Hitpay Transaction ID')
    hitpay_payment_request_id = fields.Char('Hitpay Payment Request ID')
    hitpay_payment_amount = fields.Char('Hitpay Payment Amount')
    hitpay_payment_currency = fields.Char('Hitpay Payment Currency')
    hitpay_refund_id = fields.Char('Hitpay Refund ID')
    hitpay_refund_amount = fields.Char('Hitpay Refunded Amount')
    hitpay_refund_currency = fields.Char('Hitpay Refunded Currency')
    hitpay_refund_createdat = fields.Char('Hitpay Refunded Date')
    
    def action_post(self):
        res = super().action_post()

        if self.id and self.payment_transaction_id:
            payment_transaction_id = self.payment_transaction_id.id
            paymentTransaction = self.env["payment.transaction"].search([('id', '=', payment_transaction_id)], limit=1)
            if (paymentTransaction):
                hitpay_payment_status = paymentTransaction.hitpay_payment_status
                hitpay_payment_id = paymentTransaction.hitpay_payment_id
                hitpay_transaction_id = paymentTransaction.hitpay_transaction_id
                hitpay_payment_request_id = paymentTransaction.hitpay_payment_request_id
                hitpay_payment_amount = paymentTransaction.hitpay_payment_amount
                hitpay_payment_currency = paymentTransaction.hitpay_payment_currency
                
                account_id = self.id
                if (account_id > 0):
                    accountPayment = self.env["account.payment"].search([('id', '=', account_id)], limit=1)
                    if (accountPayment):
                        dataUpdate = {
                            'hitpay_payment_status': hitpay_payment_status,
                            'hitpay_payment_id': hitpay_payment_id,
                            'hitpay_transaction_id': hitpay_transaction_id,
                            'hitpay_payment_request_id': hitpay_payment_request_id,
                            'hitpay_payment_amount': hitpay_payment_amount,
                            'hitpay_payment_currency': hitpay_payment_currency
                        }
              
                        accountPayment.write(dataUpdate)
    
        return res