class DomainError(Exception):
    """Base class for application domain errors."""


class ValidationError(DomainError):
    """Raised when entity data is invalid."""


class NotFoundError(DomainError):
    """Raised when an aggregate cannot be found."""


class ConflictError(DomainError):
    """Raised when a uniqueness or state conflict occurs."""


class BusinessRuleViolation(DomainError):
    """Raised when a domain invariant would be broken."""
