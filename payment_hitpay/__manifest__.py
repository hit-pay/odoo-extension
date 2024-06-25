{
    'name': "HitPay Payment Gateway",
    'version': '17.0.0.1',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': "HitPay Payment Gateway Plugin allows merchants to accept PayNow QR, Cards, Apple Pay, Google Pay, WeChatPay, AliPay and GrabPay Payments.",
    'author': 'HitPay Payment Solutions Pte Ltd',
    'website': 'https://www.hitpayapp.com',
    'depends': ['payment'],
    'data': [
        'views/payment_hitpay_templates.xml',
        'views/payment_provider_views.xml',
		'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
    ],
    'images': ['images/main_screenshot.png'],
    'application': True,
    'installable': True,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}
