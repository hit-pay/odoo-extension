# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR
import logging

_logger = logging.getLogger(__name__)


class POSSession(models.Model):
    _name = 'pos.session'
    _inherit = 'pos.session'

    def _loader_params_pos_payment_method(self):
        params = super(POSSession, self)._loader_params_pos_payment_method()
        params['search_params']['fields'].extend(
            ["pos_hitpay_api_key", "pos_hitpay_api_salt", "pos_hitpay_test_mode", "pos_hitpay_terminal_identifier"])
        return params
