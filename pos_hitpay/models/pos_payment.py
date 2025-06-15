# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from urllib.parse import urljoin
import requests
from requests.exceptions import ReadTimeout
from odoo.exceptions import UserError
import logging
import json

_logger = logging.getLogger(__name__)


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    hitpay_paymentStatus = fields.Char('Hitpay Payment Status')
    hitpay_paymentId = fields.Char('Hitpay Payment ID')
    hitpay_paymentRequestId = fields.Char('Hitpay Payment Request ID')
    hitpay_paymentAmount = fields.Char('Hitpay Payment Amount')
    hitpay_paymentCurrency = fields.Char('Hitpay Payment Currency')
    hitpay_paymentReference = fields.Char('Hitpay Payment Reference')
    hitpay_refundId = fields.Char('Hitpay Payment Refund ID')
    hitpay_refundAmount = fields.Char('Hitpay Payment Refund Amount')
    hitpay_refundCurrency = fields.Char('Hitpay Payment Refund Currency')
    
    def _export_for_ui(self, payment):
        data = super(PosPayment, self)._export_for_ui(payment)
        data.update({
            'hitpay_paymentStatus': payment.hitpay_paymentStatus,
            'hitpay_paymentId': payment.hitpay_paymentId,
            'hitpay_paymentRequestId': payment.hitpay_paymentRequestId,
            'hitpay_paymentAmount': payment.hitpay_paymentAmount,
            'hitpay_paymentCurrency': payment.hitpay_paymentCurrency,
            'hitpay_paymentReference': payment.hitpay_paymentReference,
        })
        return data
       
