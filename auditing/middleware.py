"""
Middleware to capture current request for audit logging.

This middleware stores the entire request in thread-local storage
so that signals can access request.user even when DRF authenticates
inside the view.
"""
import logging
from .signals import set_current_request, clear_current_request

logger = logging.getLogger(__name__)


class AuditLogMiddleware:
    """
    Middleware that stores the current request in thread-local storage.

    This allows signals to access the authenticated user from request.user,
    even when using DRF's JWT authentication which happens inside the view.

    IMPORTANT: This must be placed AFTER AuthenticationMiddleware in settings.MIDDLEWARE
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store the entire request object in thread-local
        # This way signals can access request.user during .save()
        set_current_request(request)
        logger.info(f"[AUDIT MIDDLEWARE] Stored request for {request.method} {request.path}")

        try:
            # Process the request - DRF will authenticate inside the view
            response = self.get_response(request)

            # Log if user was authenticated (for debugging)
            if hasattr(request, 'user') and request.user.is_authenticated:
                logger.info(f"[AUDIT MIDDLEWARE] Request completed with user: {request.user.username} (ID: {request.user.id})")
            else:
                logger.debug(f"[AUDIT MIDDLEWARE] Request completed without authenticated user")

            return response
        finally:
            # Always clear the request after processing
            clear_current_request()
            logger.debug(f"[AUDIT MIDDLEWARE] Cleared request")
