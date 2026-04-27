"""Domain errors for IOC input validation."""


class IocInputError(ValueError):
    """Raised when user-supplied IOC text is invalid (e.g. empty after sanitization)."""
