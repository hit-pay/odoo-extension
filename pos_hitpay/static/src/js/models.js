/** @odoo-module */

import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { PaymentPosHitpay } from "@pos_hitpay/js/payment_hitpay_pos";
import { Payment } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

register_payment_method("pos_hitpay", PaymentPosHitpay);

patch(Payment.prototype, {
    setup() {
        super.setup(...arguments);
        this.hitpayInvoiceId = this.hitpayInvoiceId || null
    },
	export_as_JSON () {
		const data = super.export_as_JSON(...arguments)
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
		
		return data
	},
    export_for_printing(){
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
      },
	  init_from_JSON (json) {
		super.init_from_JSON(...arguments)
		this.hitpayInvoiceId = json.hitpay_invoice_id;
		this.hitpay_paymentRequestId = json.hitpay_paymentRequestId;
		this.hitpay_paymentReference = json.hitpay_paymentReference;
		this.hitpay_paymentStatus = json.hitpay_paymentStatus;
		this.hitpay_paymentAmount = json.hitpay_paymentAmount;
		this.hitpay_paymentCurrency = json.hitpay_paymentCurrency;
		this.hitpay_paymentId = json.hitpay_paymentId;
		
		this.hitpay_refundId = json.hitpay_refundId;
        this.hitpay_refundAmount = json.hitpay_refundAmount;
        this.hitpay_refundCurrency = json.hitpay_refundCurrency;
	},
      setHitpayInvoiceId (id) {
        this.hitpayInvoiceId = id
      },
      getHitpayInvoiceId () {
        return this.hitpayInvoiceId
      }
});


