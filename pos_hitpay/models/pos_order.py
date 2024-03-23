# -*- coding: utf-8 -*-
import logging
import pprint
from odoo import models, fields, api, _
from . import hitpaypos_client
from . import pos_payment_method
import requests
from odoo.exceptions import UserError

class PosOrder(models.Model):
    _inherit = 'pos.order'

    hitpayPosClient = hitpaypos_client.HitpayPosClient
    posPaymentMethod = pos_payment_method.PosPaymentMethod

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        fields = super(PosOrder, self)._payment_fields(order, ui_paymentline)
        payment = self.env['pos.payment']
        fields.update({
            'hitpay_paymentStatus': ui_paymentline.get('hitpay_paymentStatus'),
            'hitpay_paymentId': ui_paymentline.get('hitpay_paymentId'),
            'hitpay_paymentRequestId': ui_paymentline.get('hitpay_paymentRequestId'),
            'hitpay_paymentAmount': ui_paymentline.get('hitpay_paymentAmount'),
            'hitpay_paymentCurrency': ui_paymentline.get('hitpay_paymentCurrency'),
            'hitpay_paymentReference': ui_paymentline.get('hitpay_paymentReference')
        })

        return fields
    
    @api.model
    def add_payment(self, data):
        """Create a new payment for the order"""
        self.ensure_one()

        payment_method = self.posPaymentMethod.get_current_hitpay_payment_method(self.posPaymentMethod)

        if payment_method.id == data['payment_method_id']:
            if data['amount'] < 0 :
                pos_reference = self.pos_reference
                pos_reference = pos_reference.replace("Order ", "")
            
                posPayment = self.env["pos.payment"].search([('hitpay_paymentReference', '=', pos_reference)], limit=1)
                hitpay_payment_id = posPayment.hitpay_paymentId

                if hitpay_payment_id != '':
                    payload = {
                        'payment_id': hitpay_payment_id,
                        'amount': data['amount'] * -1,
                    }

                    logging.getLogger(__name__).info(
                        "Refund payload for %s ", pprint.pformat(payload),
                    )

                    result = self.hitpayPosClient.refundPayment(
                        self.hitpayPosClient,
                        payment_method,
                        payload
                    )

                    logging.getLogger(__name__).info(
                        "Response for %s ", pprint.pformat(result),
                    )

                    if result.get('message') :
                        raise UserError(result.get('message'))
                    
                    data["hitpay_refundId"] = result.get('id')
                    data["hitpay_refundAmount"] = result.get('amount_refunded')
                    data["hitpay_refundCurrency"] = result.get('currency')
      
        self.env['pos.payment'].create(data)
        self.amount_paid = sum(self.payment_ids.mapped('amount'))