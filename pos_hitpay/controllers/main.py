# coding: utf-8
import logging
import pprint
import json
from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)

class PosHitpayController(http.Controller):
    _notification_url = '/pos/hitpay/webhook'

    @http.route(_notification_url, type='json', methods=['POST'], auth='none', csrf=False)
    def notification(self):
        data = json.loads(request.httprequest.data)
        payment_method = request.env['pos.payment.method'].sudo().search([('use_payment_terminal', '=', 'pos_hitpay')], limit=1)
        payment_method.pos_hitpay_latest_response = json.dumps(data)
