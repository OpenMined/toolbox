"""Discord API exceptions."""


class DiscordException(Exception):
    """Base exception for Discord API errors."""
    pass


class AuthenticationException(DiscordException):
    """Raised when authentication fails."""
    pass


class RateLimitException(DiscordException):
    """Raised when rate limited by Discord."""
    pass


class NotFoundException(DiscordException):
    """Raised when a resource is not found."""
    pass


class ForbiddenException(DiscordException):
    """Raised when access is forbidden."""
    pass