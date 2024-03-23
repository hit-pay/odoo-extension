/* eslint-disable no-undef */
/* eslint-disable camelcase */
odoo.define('pos_hitpay.payment', function (require) {
  'use strict'

  const core = require('web.core')
  const rpc = require('web.rpc')
  const PaymentInterface = require('point_of_sale.PaymentInterface')
  const { Gui } = require('point_of_sale.Gui')

  const paymentStatus = {
    PENDING: 'pending',
    RETRY: 'retry',
    WAITING: 'waiting',
    FORCE_DONE: 'force_done'
  }

  // For string translations
  const _t = core._t

  const PaymentPosHitpay = PaymentInterface.extend({
    send_payment_request: function () {
      this._super.apply(this, arguments)
      this._reset_state()

      return this._hitpay_pay()
    },

    get_selected_payment: function () {
      const paymentLine = this.pos.get_order().selected_paymentline
      if (paymentLine && paymentLine.payment_method.use_payment_terminal === 'pos_hitpay') {
        return paymentLine
      }
      return false
    },

    send_payment_cancel: function () {
        this._super.apply(this, arguments);
        const paymentLine = this.get_selected_payment()
        if (paymentLine) {
          paymentLine.set_payment_status(paymentStatus.RETRY)
          return true;
        }
    },

    close: function () {
      this._super.apply(this, arguments)
    },

    // private methods
    _reset_state: function () {
      this.was_cancelled = false
      this.last_diagnosis_service_id = false
      this.remaining_polls = 2
      clearTimeout(this.polling)
    },

    
    _hitpay_get_sale_id: function () {
      const config = this.pos.config
      return _.str.sprintf('%s (ID: %s)', config.display_name, config.id)
    },

    _handle_odoo_connection_failure: function (data) {
      // handle timeout
      const paymentLine = this.get_selected_payment()
      if (paymentLine) {
        paymentLine.set_payment_status(paymentStatus.RETRY)
      }

      this._show_error(_t('Could not connect to the Odoo server, please check your internet connection and try again.'))
      return Promise.reject(data) // prevent subsequent onFullFilled's from being called
    },

    _hitpay_pay: function () {
      const self = this

      const order = this.pos.get_order()
      const paymentLine = this.get_selected_payment()
      if (paymentLine && paymentLine.amount <= 0) {
        this._show_error(
          _t('Cannot process transaction with zero or negative amount.')
        )
        return Promise.resolve()
      }

      const receipt_data = order.export_for_printing()
      receipt_data.amount = paymentLine.amount
      receipt_data.terminal_id = paymentLine.payment_method.pos_hitpay_terminal_identifier

      return this._call_hitpay(receipt_data).then(function (data) {
        return self._hitpay_handle_response(data)
      })
    },

    // Create the payment request
    _call_hitpay: function (data) {
      return rpc.query({
        model: 'pos.payment.method',
        method: 'request_payment',
        args: [data]
      }, {
        // When a payment terminal is disconnected it takes Hitpay
        // a while to return an error (~6s). So wait 10 seconds
        // before concluding Odoo is unreachable.
        timeout: 10000,
        shadow: true
      }).catch(
        this._handle_odoo_connection_failure.bind(this)
      )
    },

    _poll_for_response: function (resolve, reject) {
      const self = this
      if (this.was_cancelled) {
        resolve(false)
        return Promise.resolve()
      }

      const order = this.pos.get_order()
      const paymentLine = this.get_selected_payment()

      // If the payment line dont have hitpay invoice then stop polling retry.
      if (!paymentLine || paymentLine.getHitpayInvoiceId() == null) {
        resolve(false)
        return Promise.resolve()
      }

      const data = {
        sale_id: this._hitpay_get_sale_id(),
        transaction_id: order.uid,
        terminal_id: this.payment_method.pos_hitpay_terminal_identifier,
        requested_amount: paymentLine.amount,
        hitpay_invoice_id: paymentLine.getHitpayInvoiceId()
      }

      return rpc.query({
        model: 'pos.payment.method',
        method: 'get_latest_pos_hitpay_status',
        args: [data]
      }, {
        timeout: 5000,
        shadow: true
      }).catch(function (data) {
        reject()
        return self._handle_odoo_connection_failure(data)
      }).then(function (result) {

        self.remaining_polls = 2
        const invoice = result.response

        if (invoice.id === paymentLine.getHitpayInvoiceId()) {
          self._update_payment_status(invoice, resolve, reject)
        } else {
          paymentLine.set_payment_status(paymentStatus.RETRY)
          reject()
        }
      })
    },

    _update_payment_status: function (invoice, resolve, reject) {

      if (invoice.status === 'completed') {

        $('#hitpay-payment-status').text('Paid')
        $('#invoice-link > a').text('Paid')
        
        const paymentLine = this.get_selected_payment()
        if (paymentLine) {

          paymentLine['hitpay_paymentRequestId'] = invoice.id;
          paymentLine['hitpay_paymentReference'] = invoice.reference_number;
          paymentLine['hitpay_paymentStatus'] = invoice.status;
          paymentLine['hitpay_paymentAmount'] = invoice.amount;
          paymentLine['hitpay_paymentCurrency'] = invoice.currency;
          paymentLine['hitpay_paymentId'] = invoice.payments[0].id;

          paymentLine.set_payment_status('done')
  
        }
        resolve(true)
      } else if (invoice.status === 'failed') {
        $('#hitpay-payment-status').text('Failed')
         const paymentLine = this.get_selected_payment()
        if (paymentLine) {
          paymentLine.set_payment_status(paymentStatus.RETRY)
        }
        reject()
      } else if (invoice.status === 'canceled') {
        $('#hitpay-payment-status').text('Canceled')
        const paymentLine = this.get_selected_payment()
        if (paymentLine) {
          paymentLine.set_payment_status(paymentStatus.RETRY)
        }
        reject()
      }
    },

    _hitpay_handle_response: function (response) {

        const self = this
        const paymentLine = this.get_selected_payment()

        if (response.message) {
            let errorMessage = _t(response.message)
            this._show_error(
              _t('System Error'),
              errorMessage
            )
            if (paymentLine) {
              paymentLine.set_payment_status(paymentStatus.FORCE_DONE)
            }
            return Promise.resolve()
        } else if (response.id) {

          let posHitpaySelf = self;
          if (!window.HitPay.inited) {
            window.HitPay.init(response.url, {
              domain: response.domain,
              apiDomain: response.api_domain,
            },
            {
              onClose: function() {
                const paymentLine = posHitpaySelf.get_selected_payment()
                if (paymentLine) {
                    paymentLine.set_payment_status(paymentStatus.RETRY)
                }
              },
              onSuccess: function() {
                const paymentLine = posHitpaySelf.get_selected_payment()
                if (paymentLine) {
                    paymentLine.setHitpayInvoiceId(response.id)
                    paymentLine.set_payment_status(paymentStatus.WAITING)
                }
              },
              onError: function(error) {
                const paymentLine = posHitpaySelf.get_selected_payment()
                if (paymentLine) {
                    paymentLine.set_payment_status(paymentStatus.RETRY)
                }
                posHitpaySelf._show_error(_t('Payment Error. ')+error)
              },
            });
          }

          window.HitPay.toggle({
              paymentRequest: response.id,          
          });
                            
          if (paymentLine) {
            paymentLine.setHitpayInvoiceId(response.id)
            paymentLine.set_payment_status(paymentStatus.WAITING)
          }

          return this.start_get_status_polling()
      }
    },

    start_get_status_polling () {
      const self = this
      const res = new Promise(function (resolve, reject) {
        clearTimeout(self.polling)
        self._poll_for_response(resolve, reject)
        self.polling = setInterval(function () {
          self._poll_for_response(resolve, reject)
        }, 5500)
      })

      // make sure to stop polling when we're done
      res.finally(function () {
        self._reset_state()
      })

      Promise.resolve()
      return res
    },

    _show_error: function (title, msg) {
      if (!title) {
        title = _t('Hitpay Error')
      }
      Gui.showPopup('ErrorPopup', {
        title,
        body: msg
      })
    }
    
  })

  return PaymentPosHitpay
})
