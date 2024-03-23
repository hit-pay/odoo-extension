odoo.define('pos_hitpay.models', function (require) {
    const { register_payment_method, Payment } = require('point_of_sale.models')
    const PaymentHitPay = require('pos_hitpay.payment')
    const Registries = require('point_of_sale.Registries')

    register_payment_method('pos_hitpay', PaymentHitPay)

    const PosHitPayPayment = (Payment) => class PosHitPayPayment extends Payment {
      constructor (obj, options) {
        super(...arguments)
        this.hitpayInvoiceId = this.hitpayInvoiceId || null
      }

      // @override
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
        return data
      }

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
        return data;
      }

      // @override
      init_from_JSON (json) {
        super.init_from_JSON(...arguments)
        this.hitpayInvoiceId = json.hitpay_invoice_id;
        this.hitpay_paymentRequestId = json.hitpay_paymentRequestId;
        this.hitpay_paymentReference = json.hitpay_paymentReference;
        this.hitpay_paymentStatus = json.hitpay_paymentStatus;
        this.hitpay_paymentAmount = json.hitpay_paymentAmount;
        this.hitpay_paymentCurrency = json.hitpay_paymentCurrency;
        this.hitpay_paymentId = json.hitpay_paymentId;

      }

      setHitpayInvoiceId (id) {
        this.hitpayInvoiceId = id
      }

      getHitpayInvoiceId () {
        return this.hitpayInvoiceId
      }
    }
    Registries.Model.extend(Payment, PosHitPayPayment)
}) 
    