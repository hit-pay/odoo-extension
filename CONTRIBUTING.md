# Contributing to HitPay Odoo Extension

Thank you for your interest in contributing to the HitPay Odoo Payment Gateway modules.

## Branch Strategy

This repository uses **version branches** to support multiple Odoo versions:

| Branch | Odoo Version | Status |
|--------|--------------|--------|
| `18.0` | Odoo 18.0 | Active |
| `17.0` | Odoo 17.0 | Active |
| `16.0` | Odoo 16.0 | Maintenance |
| `15.0` | Odoo 15.0 | Maintenance |
| `main` | Latest (18.0) | Active |

### Branch Definitions

- **Active**: Receives new features and bug fixes
- **Maintenance**: Receives critical bug fixes and security patches only

## How to Contribute

### Reporting Issues

1. Check if the issue already exists in [GitHub Issues](https://github.com/hit-pay/odoo-extension/issues)
2. Specify your Odoo version in the issue title (e.g., `[18.0] Payment fails on checkout`)
3. Include steps to reproduce, expected behavior, and actual behavior

### Submitting Changes

1. **Fork** the repository

2. **Clone** and checkout the correct version branch:
   ```bash
   git clone https://github.com/YOUR_USERNAME/odoo-extension.git
   cd odoo-extension
   git checkout 18.0  # Use the branch matching your Odoo version
   ```

3. **Create a feature branch** from the version branch:
   ```bash
   git checkout -b fix/payment-webhook-issue
   ```

4. **Make your changes** and test thoroughly

5. **Commit** with a clear message:
   ```bash
   git commit -m "Fix webhook signature validation for refunds"
   ```

6. **Push** to your fork:
   ```bash
   git push origin fix/payment-webhook-issue
   ```

7. **Open a Pull Request** against the correct version branch (not `main`)

### PR Guidelines

- Target the correct version branch (e.g., `18.0`, `17.0`)
- Include a clear description of changes
- Reference any related issues
- Ensure code follows Odoo coding standards
- Test on the target Odoo version

## Backporting Fixes

If a fix applies to multiple Odoo versions:

1. Submit the PR to the latest affected version branch first
2. Once merged, cherry-pick to older version branches if applicable
3. Note: Not all fixes can be backported due to API differences between Odoo versions

## Development Setup

1. Set up an Odoo development environment for your target version
2. Clone this repository into your addons directory
3. Install the module(s) in developer mode
4. Enable logging for debugging: `--log-level=debug --log-handler=odoo.addons.payment_hitpay:DEBUG`

## Code Style

- Follow [Odoo coding guidelines](https://www.odoo.com/documentation/18.0/contributing/development/coding_guidelines.html)
- Use meaningful variable and function names
- Add comments for complex logic
- Keep methods focused and concise

## Questions?

- Check the [documentation](https://docs.hitpayapp.com)
- Open an issue for questions related to development
