/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

const paymentStatus = {
    PENDING: 'pending',
    RETRY: 'retry',
    WAITING: 'waiting',
    FORCE_DONE: 'force_done'
}

export class PaymentPosHitpay extends PaymentInterface {
    send_payment_request(cid) {
        super.send_payment_request(cid);
        this._reset_state()

        return this._hitpay_pay(cid)
    }

    send_payment_cancel(order, cid) {
        super.send_payment_cancel(order, cid);
        return this._hitpay_cancel();
    }

    _reset_state () {
      this.was_cancelled = false
      this.last_diagnosis_service_id = false
      this.remaining_polls = 2
      clearTimeout(this.polling)
    }

    async _hitpay_pay (cid) {

      const self = this

      const order = this.pos.get_order()

      const paymentLine = this.get_selected_payment()

      if (order._isRefundOrder()) {
        paymentLine.set_payment_status('waiting');
        const refunded_orderline_id = order.orderlines[0].refunded_orderline_id;
		
        const dataInput = {
          'order_line_id':refunded_orderline_id,
          'amount': paymentLine.amount,
          'payment_method_id': this.payment_method.id
        };

        return await self.env.services.orm.silent
          .call("pos.order", 'refund_payment', [dataInput])
          .catch(function(err) {
            self._show_error(_t(err.message))
          })
          .then(function (result) {
            if (result.status == 'success') {
              if (paymentLine) {
                paymentLine.hitpay_refundId = result.response.hitpay_refundId;
                paymentLine.hitpay_refundAmount = result.response.hitpay_refundAmount;
                paymentLine.hitpay_refundCurrency = result.response.hitpay_refundCurrency;
                
                paymentLine.set_payment_status('done')
              }
              return Promise.resolve(true);
            } else {
              self._show_error(
                _t(result.message)
              )
              return Promise.resolve()
            }
        });

      } else {
          if (paymentLine && paymentLine.amount <= 0) {
            this._show_error(
              _t('Cannot process transaction with zero or negative amount.')
            )
            return Promise.resolve()
          }

          const orderId = order.name.replace(" ", "").replaceAll("-", "").toUpperCase();
          const receipt_data = {
              amount: paymentLine.amount,
              currency: this.pos.currency.name,
              customer_name:this.pos.company.name,
              customer_email:this.pos.company.email,
              referenceId:orderId,
              payment_method_id: this.payment_method.id
          };

          return this._call_hitpay(receipt_data).then(function (data) {
            return self._hitpay_handle_response(data)
          })
      }
    }

    get_selected_payment () {
      const paymentLine = this.pos.get_order().selected_paymentline;
      if (paymentLine && paymentLine.payment_method.use_payment_terminal === 'pos_hitpay') {
        return paymentLine
      }
      return false
    }

    _call_hitpay(dataInput) {
      return this.env.services.orm.silent
            .call("pos.payment.method", 'request_payment', [[this.payment_method.id], dataInput])
            .catch(this._handle_odoo_connection_failure.bind(this));
    }

    _hitpay_cancel() {
        const self = this
        const paymentLine = this.get_selected_payment()

        const order = this.pos.get_order()

        if (order._isRefundOrder()) {
          return Promise.resolve(true);
        }

        const dataInput = {
          hitpay_invoice_id: paymentLine.getHitpayInvoiceId(),
          payment_method_id: this.payment_method.id
        };

        return this.env.services.orm.silent
            .call("pos.payment.method", 'delete_payment', [[this.payment_method.id], dataInput])
            .catch(this._handle_odoo_connection_failure_delete.bind(this))
            .then(function (result) {
                const invoice = result.response

                if (invoice.success) {
                } else {
                  self._show_error(invoice.message)
                  return Promise.resolve(false);
                }

                return Promise.resolve(true);
            })
    }

    _handle_odoo_connection_failure_delete (data) {
      // handle timeout
      const paymentLine = this.get_selected_payment()
      if (paymentLine) {
        paymentLine.set_payment_status(paymentStatus.RETRY)
      }

      this._show_error(_t('Could not connect to the Odoo server, please check your internet connection and try again.'))
      return Promise.reject(data) // prevent subsequent onFullFilled's from being called
    }

    _handle_odoo_connection_failure (data) {
      // handle timeout
      const paymentLine = this.get_selected_payment()
      if (paymentLine) {
        paymentLine.set_payment_status(paymentStatus.RETRY)
      }

      this._show_error(_t('Could not connect to the Odoo server, please check your internet connection and try again.'))
      return Promise.reject(data) // prevent subsequent onFullFilled's from being called
    }

    _hitpay_handle_response (response) {
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
              
          if (paymentLine) {
            paymentLine.setHitpayInvoiceId(response.id);
            paymentLine.set_payment_status(paymentStatus.WAITING)
          }

          return this.start_get_status_polling()
      }
    }

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
    }

    async _poll_for_response (resolve, reject) {
      const self = this
      if (this.was_cancelled) {
        resolve(false)
        return Promise.resolve()
      }

      const order = this.pos.get_order()
      const paymentLine = this.get_selected_payment()

      // If the payment line dont have hitpay invoice then stop polling retry.
      if (!paymentLine|| paymentLine.getHitpayInvoiceId() == null) {
        resolve(false)
        return Promise.resolve()
      }

      const dataInput = {
        sale_id: this._hitpay_get_sale_id(),
        transaction_id: order.uid,
        terminal_id: this.payment_method.pos_hitpay_terminal_identifier,
        requested_amount: paymentLine.amount,
        hitpay_invoice_id: paymentLine.getHitpayInvoiceId(),
        payment_method_id: this.payment_method.id
      };

      const data = await this.env.services.orm.silent
        .call("pos.payment.method", 'get_latest_pos_hitpay_status', [[this.payment_method.id], dataInput])
        .catch(this._handle_odoo_connection_failure.bind(this))
        .then(function (result) {
          self.remaining_polls = 2
          const invoice = result.response

          if (invoice.id === paymentLine.getHitpayInvoiceId()) {
            self._update_payment_status(invoice, resolve, reject)
          } else {
            paymentLine.set_payment_status(paymentStatus.RETRY)
            reject()
          }
      })
    }

    _hitpay_get_sale_id () {
      const config = this.pos.config
      return _t('%s (ID: %s)', config.display_name, config.id)
    }

    _update_payment_status (invoice, resolve, reject, data) {
      if (invoice.status === 'completed') {

        //$('#hitpay-payment-status').text('Paid')
        //$('#invoice-link > a').text('Paid')
        
        const paymentLine = this.get_selected_payment()
        if (paymentLine) {

          paymentLine.hitpay_paymentRequestId = invoice.id;
          paymentLine.hitpay_paymentReference = invoice.reference_number;
          paymentLine.hitpay_paymentStatus = invoice.status;
          paymentLine.hitpay_paymentAmount = invoice.amount;
          paymentLine.hitpay_paymentCurrency = invoice.currency;
          paymentLine.hitpay_paymentId = invoice.payments[0].id;

          paymentLine.set_payment_status('done')
        }
        resolve(true)
      } else if (invoice.status === 'failed') {
        //$('#hitpay-payment-status').text('Failed')
         const paymentLine = this.get_selected_payment()
        if (paymentLine) {
          paymentLine.set_payment_status(paymentStatus.RETRY)
        }
        reject()
      } else if (invoice.status === 'canceled') {
        //$('#hitpay-payment-status').text('Canceled')
        const paymentLine = this.get_selected_payment()
        if (paymentLine) {
          paymentLine.set_payment_status(paymentStatus.RETRY)
        }
        reject()
      }
    }

    _show_error (error_msg, title) {
        this.env.services.dialog.add(AlertDialog, {
            title: title || _t("HitPay Pos Error"),
            body: error_msg,
        });
    }
}
