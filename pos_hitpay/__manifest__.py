# -*- coding: utf-8 -*-
{
    'name': "HitPay Payment Gateway POS",
    'license': 'LGPL-3',
    'summary': """
        Integrate your POS with a HitPay Payment Gateway payment terminal. 
        """,
    'description': """
        HitPay Payment Gateway POS module for Odoo POS is an official built by HitPay Payment Solutions Pte Ltd to allow you in accepting online payments instantly. 
    """,
    'author': "HitPay Payment Solutions Pte Ltd",
    'website': "https://www.hitpayapp.com",
    'category': 'Sales/Point of Sale',
    'version': '18.0.0.2',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_payment_method_views.xml',
        'views/pos_payment.xml',
    ],
    'images': ['images/main_screenshot.png'],
    'application': True,
    'installable': True,
    'assets': {
		'point_of_sale._assets_pos': [
            'pos_hitpay/static/src/js/PaymentScreen.js',
            'pos_hitpay/static/src/js/payment_hitpay_pos.js',
            'pos_hitpay/static/src/js/models.js',
			'https://hit-pay.com/hitpay.js',
            "pos_hitpay/static/src/xml/ReceiptScreen/OrderReceipt.xml",
		],
    }
}
