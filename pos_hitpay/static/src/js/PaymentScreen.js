odoo.define('pos_hitpay.PaymentScreen', function(require) {
    "use strict";

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const { onMounted } = owl;

    const PosHitpayPaymentScreen = PaymentScreen => class extends PaymentScreen {
        constructor() {
            super(...arguments);
            onMounted(() => {
                const pendingPaymentLine = this.currentOrder.paymentlines.find(
                    paymentLine => paymentLine.payment_method.use_payment_terminal === 'pos_hitpay' &&
                        (!paymentLine.is_done() && paymentLine.get_payment_status() !== 'pending')
                );
                if (pendingPaymentLine) {
                    const paymentTerminal = pendingPaymentLine.payment_method.payment_terminal;
                    pendingPaymentLine.set_payment_status('waiting');
                    paymentTerminal.start_get_status_polling().then(isPaymentSuccessful => {
                        if (isPaymentSuccessful) {
                            pendingPaymentLine.set_payment_status('done');
                            pendingPaymentLine.can_be_reversed = paymentTerminal.supports_reversals;
                        } else {
                            pendingPaymentLine.set_payment_status('retry');
                        }
                    });
                }
            });
        }
    };

    Registries.Component.extend(PaymentScreen, PosHitpayPaymentScreen);

    return PaymentScreen;
});
