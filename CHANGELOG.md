# Changelog

All notable changes to the HitPay Odoo Payment Gateway modules.

## Odoo 18.0

### [v18.0.0.4] - 2024

#### payment_hitpay v18.0.0.2
- Upgraded to be compatible with POS online payment method as a payment provider

#### pos_hitpay v18.0.0.4
- Fixed invalid webhook URL when used with POS online payment method
- Fixed conflict when both payment_hitpay and pos_hitpay addons are installed
- Upgraded to support multi-terminal/register usage
- Fixed bug when deleting/canceling payment line
- Added feature to delete payment request via HitPay API when canceling payment
- Backend refund feature upgraded
- New frontend POS checkout refund feature added

### [v18.0.0.0] - 2024
- Initial release for Odoo 18.0
- Added payment_hitpay module
- Added pos_hitpay module

---

## Odoo 17.0

### [v17.0.0.1] - 2024
- Initial release for Odoo 17.0
- payment_hitpay module only (pos_hitpay not available for this version)
- Fixed neutralize.sql column name error (hitpay_api_salty → hitpay_api_salt)

---

## Odoo 16.0

### [v16.0.1.0] - 2023
- Initial release for Odoo 16.0
- Added payment_hitpay module
- Added pos_hitpay module
- Added channel parameter support
- Fixed image field not exist error

---

## Odoo 15.0

### [v15.0.1.0] - 2023
- Initial release for Odoo 15.0
- Added payment_hitpay module
- Added pos_hitpay module
- Added channel parameter support
