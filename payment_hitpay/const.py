TRANSACTION_STATUS_MAPPING = {
    'pending': ('pending'),
    'done': ('completed'),
    'canceled': ('canceled', 'null', 'failed'),
}

DEFAULT_PAYMENT_METHOD_CODES = {
    'hitpay',
}