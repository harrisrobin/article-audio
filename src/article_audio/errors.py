class UserError(Exception):
    """A safe, actionable error suitable for an agent's JSON response."""

    def __init__(self, message: str, code: str = "invalid_request"):
        super().__init__(message)
        self.code = code
