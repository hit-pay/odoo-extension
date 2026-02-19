import { register_payment_method } from "@point_of_sale/app/services/pos_store";
import { PaymentPosHitpay } from "@pos_hitpay/js/payment_hitpay_pos";
import { PosPayment } from "@point_of_sale/app/models/pos_payment";
import { patch } from "@web/core/utils/patch";

register_payment_method("pos_hitpay", PaymentPosHitpay);

patch(PosPayment.prototype, {
    setup() {
        super.setup(...arguments);
        this.hitpayInvoiceId = this.hitpayInvoiceId || null
    },
    /*export_for_printing(){
        var data = super.export_for_printing(...arguments);
        data.hitpay_invoice_id = this.hitpayInvoiceId
        data.hitpayInvoiceId = this.hitpay_invoice_id;
        data.hitpay_paymentRequestId = this.hitpay_paymentRequestId;
        data.hitpay_paymentReference = this.hitpay_paymentReference;
        data.hitpay_paymentStatus = this.hitpay_paymentStatus;
        data.hitpay_paymentAmount = this.hitpay_paymentAmount;
        data.hitpay_paymentCurrency = this.hitpay_paymentCurrency;
        data.hitpay_paymentId = this.hitpay_paymentId;

        data.hitpay_refundId = this.hitpay_refundId;
        data.hitpay_refundAmount = this.hitpay_refundAmount;
        data.hitpay_refundCurrency = this.hitpay_refundCurrency;

        return data;
      },*/
      setHitpayInvoiceId (id) {
        this.hitpayInvoiceId = id
      },
      getHitpayInvoiceId () {
        return this.hitpayInvoiceId
      }
});


