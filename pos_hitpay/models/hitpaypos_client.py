# -*- coding: utf-8 -*-

import logging
import pprint

import json
import requests
from datetime import datetime

from werkzeug import urls

from odoo.http import request
from odoo import models, fields
from . import error_handler
from odoo.exceptions import UserError

from odoo.addons.pos_hitpay.controllers.main import PosHitpayController

_logger = logging.getLogger(__name__)

class HitpayPosClient():

    errorHandler = error_handler.ErrorHandler()

    def getApiURL(self, payment_method):
        ctx_key = payment_method.pos_hitpay_test_mode
        ctx_value = 'https://api.sandbox.hit-pay.com/v1' if ctx_key else 'https://api.hit-pay.com/v1'

        return ctx_value

    def getDomain(self, payment_method):
        ctx_key = payment_method.pos_hitpay_test_mode
        ctx_value = 'sandbox.hit-pay.com' if ctx_key else 'hit-pay.com'

        return ctx_value
    
    def getApiDomain(self, payment_method):
        ctx_key = payment_method.pos_hitpay_test_mode
        ctx_value = 'sandbox.hit-pay.com' if ctx_key else 'hit-pay.com'

        return ctx_value
    
    def isEmptyString(self, str):
        return not (str and str.strip())
    
    def getCustomerName(self, data):
        customerName = 'NA'
        if data and not self.isEmptyString(self, data['name']):
            customerName = data['name']
        return customerName
    
    def getCustomerEmail(self, data):
        customerEmail = 'na@notapplicable.com'
        if data and not self.isEmptyString(self, data['email']):
            customerEmail = data['email']
        return customerEmail

    def createPaymentRequest(self, payment_method, data):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-BUSINESS-API-KEY': payment_method.pos_hitpay_api_key,
        }
        
        endpoint = '/payment-requests'
        
        url = self.getApiURL(self, payment_method)+endpoint
        
        base_url = payment_method.get_base_url()
        return_url = urls.url_join(
            base_url, f'{PosHitpayController._notification_url}'
        )
        webhook_url = urls.url_join(
            base_url, f'{PosHitpayController._notification_url}'
        ) 

        method = 'POST'
        
        endpoint = ''

        payload = {
            'reference_number': data['name'].split(' ')[1],
            'amount': data['amount'],
            'currency':  data['currency']['name'],
            'redirect_url': return_url,
            'webhook': webhook_url,
            'name': self.getCustomerName(self, data['partner']),
            'email': self.getCustomerEmail(self, data['partner']),
            'channel': 'api_odoo'
        }

        terminal_id = payment_method.pos_hitpay_terminal_identifier

        if not self.isEmptyString(self, terminal_id):
            payload.update({'payment_methods[]': 'wifi_card_reader'})
            payload.update({'wifi_terminal_id': terminal_id})

        _logger.info(
            "CreatePaymentRequest Payload for %s :",
            pprint.pformat(payload),
        )
 
        try:
            if method == 'GET':
                res = requests.get(url, params=payload, headers=headers, timeout=10)
            else:
                res = requests.post(url, data=dict(payload), headers=headers, timeout=10)
                _logger.info(
                    "Response for %s :\n%s",
                    endpoint, pprint.pformat(payload),
                )
        except requests.exceptions.RequestException as err:
            return self.errorHandler.handleError('createPaymentRequest', err)
        
        response = json.loads(res.text)
                
        response['domain'] = self.getDomain(self, payment_method)
        response['api_domain'] = self.getApiDomain(self, payment_method)
        
        _logger.info(
                    "Response for %s :\n%s",
                    endpoint, pprint.pformat(response),
                )

        return response

    def getPaymentStatus(self, payment_method, payment_request_id):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-BUSINESS-API-KEY': payment_method.pos_hitpay_api_key,
        }
        
        endpoint = '/payment-requests/'
        
        url = self.getApiURL(self, payment_method)+endpoint+payment_request_id
  
        try:
            res = requests.get(url, headers=headers, timeout=10)
        except requests.exceptions.RequestException as err:
            return self.errorHandler.handleError('getPaymentStatus', err)

        response = json.loads(res.text)

        return response

    def refundPayment(self, payment_method, payload):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-BUSINESS-API-KEY': payment_method.pos_hitpay_api_key,
        }
        
        endpoint = '/refund'
        
        url = self.getApiURL(self, payment_method)+endpoint

        try:
            res = requests.post(url, data=dict(payload), headers=headers, timeout=10)
        except requests.exceptions.RequestException as err:
            raise UserError('Refund Failed. ' + err)

        response = json.loads(res.text)

        return response
        
    