import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        onMounted(() => {
            const pendingPaymentLine = this.currentOrder.payment_ids.find(
                (paymentLine) =>
                    paymentLine.payment_method_id.use_payment_terminal === "pos_hitpay" &&
                    !paymentLine.is_done() &&
                    paymentLine.get_payment_status() !== "pending"
            );
            if (pendingPaymentLine) {
                const paymentTerminal = pendingPaymentLine.payment_method_id.payment_terminal;
                pendingPaymentLine.set_payment_status('waiting');
                console.log('PaymentScreen');
                paymentTerminal.start_get_status_polling().then(isPaymentSuccessful => {
                     console.log('isPaymentSuccessful or not');
                    if (isPaymentSuccessful) {
                        console.log('isPaymentSuccessful done');
                        pendingPaymentLine.set_payment_status('done');
                        pendingPaymentLine.can_be_reversed = paymentTerminal.supports_reversals;
                    } else {
                        console.log('isPaymentSuccessful retry');
                        pendingPaymentLine.set_payment_status('retry');
                    }
                });
            }
        });
    },
});