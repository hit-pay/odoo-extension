from odoo.exceptions import ValidationError


class HitPayAPIError(ValidationError):
    """Raised when communication with the HitPay API fails."""

    def __init__(
        self,
        message,
        *,
        status_code=0,
        response_data=None,
    ):
        super().__init__(message)

        self.status_code = status_code
        self.response_data = response_data