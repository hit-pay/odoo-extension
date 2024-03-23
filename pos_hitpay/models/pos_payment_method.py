# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

from odoo.http import request
from . import hitpaypos_client

_logger = logging.getLogger(__name__)

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        return super(PosPaymentMethod, self)._get_payment_terminal_selection() + [('pos_hitpay', 'HitPay Payment Gateway')]

    pos_hitpay_api_key = fields.Char(string="API Key", help='As provided on HitPay dashboard', copy=False)
    pos_hitpay_api_salt = fields.Char(string="API Salt", help='As provided on HitPay dashboard', copy=False)	
    pos_hitpay_test_mode = fields.Boolean(string="Test Mode", help='Run transactions in the test environment.')
    pos_hitpay_terminal_identifier = fields.Char(string="Terminal ID", help='[Terminal model]-[Serial number], for example: P400Plus-123456789', copy=False)
    pos_hitpay_latest_response = fields.Char(help='Technical field used to buffer the latest asynchronous notification from HitPay.', copy=False, groups='base.group_erp_manager')

    hitpay_invoice_id = ''
    hitpayPosClient = hitpaypos_client.HitpayPosClient

    def get_current_hitpay_payment_method(self):
        return request.env['pos.payment.method'].sudo().search(
            [
                ('use_payment_terminal', '=', 'pos_hitpay')
            ], limit=1)

    @api.constrains('pos_hitpay_terminal_identifier')
    def _check_pos_hitpay_terminal_identifier(self):
        for payment_method in self:
            if not payment_method.pos_hitpay_terminal_identifier:
                continue
            existing_payment_method = self.search([('id', '!=', payment_method.id),
                                                   ('pos_hitpay_terminal_identifier', '=', payment_method.pos_hitpay_terminal_identifier)],
                                                  limit=1)
            if existing_payment_method:
                raise ValidationError(_('Terminal %s is already used on payment method %s.')
                                      % (payment_method.pos_hitpay_terminal_identifier, existing_payment_method.display_name))

    def _is_write_forbidden(self, fields):
        whitelisted_fields = set(('pos_hitpay_latest_response'))
        return super(PosPaymentMethod, self)._is_write_forbidden(fields - whitelisted_fields)

    @api.model
    def get_latest_pos_hitpay_status(self, data):
        '''See the description of proxy_pos_hitpay_request as to why this is an
        @api.model function.
        '''

        # Poll the status of the terminal if there's no new
        # notification we received. This is done so we can quickly
        # notify the user if the terminal is no longer reachable due
        # to connectivity issues.

        payment_method = self.get_current_hitpay_payment_method()

        invoice = self.hitpayPosClient.getPaymentStatus(
            self.hitpayPosClient,
            payment_method,
            data["hitpay_invoice_id"]
        )
        return { 'response': invoice }

    @api.model
    def request_payment(self, data):
        '''Necessary because Hitpay's endpoints don't have CORS enabled. This is an
        @api.model function to avoid concurrent update errors. Hitpay's
        async endpoint can still take well over a second to complete a
        request. By using @api.model and passing in all data we need from
        the POS we avoid locking the pos_payment_method table. This way we
        avoid concurrent update errors when Hitpay calls us back on
        /hitpay/notification which will need to write on
        pos.payment.method.
        '''

        invoice = self.hitpayPosClient.createPaymentRequest(
            self.hitpayPosClient,
            self.get_current_hitpay_payment_method(),
            json.loads(json.dumps(data))
        )
        return invoice

    @api.onchange('use_payment_terminal')
    def _onchange_use_payment_terminal(self):
        super(PosPaymentMethod, self)._onchange_use_payment_terminal()
        if self.use_payment_terminal != 'pos_hitpay':
            self.pos_hitpay_api_key = False
            self.pos_hitpay_terminal_identifier = False
 