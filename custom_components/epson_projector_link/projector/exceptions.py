class ProjectorErrorResponse(Exception):
    """Error to indicate projector returned error response."""


class ProjectorAuthError(Exception):
    """Error to indicate the projector rejected the connect request due to a missing or incorrect remote password."""
