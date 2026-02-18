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
        fields.update({
            'hitpay_paymentStatus': ui_paymentline.get('hitpay_paymentStatus'),
            'hitpay_paymentId': ui_paymentline.get('hitpay_paymentId'),
            'hitpay_paymentRequestId': ui_paymentline.get('hitpay_paymentRequestId'),
            'hitpay_paymentAmount': ui_paymentline.get('hitpay_paymentAmount'),
            'hitpay_paymentCurrency': ui_paymentline.get('hitpay_paymentCurrency'),
            'hitpay_paymentReference': ui_paymentline.get('hitpay_paymentReference'),
            'hitpay_refundId': ui_paymentline.get('hitpay_refundId'),
            'hitpay_refundAmount': ui_paymentline.get('hitpay_refundAmount'),
            'hitpay_refundCurrency': ui_paymentline.get('hitpay_refundCurrency'),
        })

        return fields
    
    def get_hitpay_payment_id(self, order_line_id):
        posOrderLine = self.env["pos.order.line"].search([('id', '=', order_line_id)], limit=1)
        order_id = posOrderLine.order_id.id
        posPayment = self.env["pos.payment"].search([('pos_order_id', '=', order_id)], limit=1)
        hitpay_payment_id = posPayment.hitpay_paymentId

        return hitpay_payment_id
        
    def get_hitpay_payment_method_by_id(self, payment_method_id):
        return self.env['pos.payment.method'].sudo().search(
            [
                ('id', '=', payment_method_id),
                ('use_payment_terminal', '=', 'pos_hitpay')
            ], limit=1)
    
    @api.model
    def refund_payment(self, data):
        payment_method = self.get_hitpay_payment_method_by_id(data['payment_method_id'])
        order_line_id = data['order_line_id']

        hitpay_payment_id = self.get_hitpay_payment_id(order_line_id)

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
                return {'status':'error', 'message': result.get('message') }
            
            response = {
                'hitpay_refundId': result.get('id'),
                'hitpay_refundAmount': result.get('amount_refunded'),
                'hitpay_refundCurrency': result.get('currency')
            }

            dataUpdate = {
                'hitpay_refundId': result.get('id'),
                'hitpay_refundAmount': result.get('amount_refunded'),
                'hitpay_refundCurrency': result.get('currency')
            }
      
            self.env['pos.payment'].update(dataUpdate)

            return {'status':'success', 'response': response }
        
        return {'status':'error', 'message': 'Hitpay Payment Id not found for this order, try to refund from Backend or manually' }
    