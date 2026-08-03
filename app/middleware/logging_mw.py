"""
middleware/logging_mw.py — Request/Response Logging
=====================================================
CONCEPT: Starlette Middleware (BaseHTTPMiddleware)

Middleware sits BETWEEN the client and your route handlers.
Every request passes through middleware before reaching your endpoint,
and every response passes back through it.

Use middleware for cross-cutting concerns:
  - Logging every request/response (this file)
  - Adding headers to all responses (e.g., CORS, request IDs)
  - Rate limiting
  - Timing all requests

Why AI engineers need this:
  - You need to log every inference request (latency, model used, errors)
  - Track p95/p99 latency across all endpoints
  - Add request IDs so you can trace a request through logs
"""

import time
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Standard Python logging — in prod, ship these logs to CloudWatch / Datadog
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every incoming request and outgoing response.

    BaseHTTPMiddleware requires you to implement `dispatch`.
    `call_next(request)` passes the request to the next handler
    (either another middleware or the actual route).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate a unique ID for this request — attach to logs
        request_id = str(uuid.uuid4())[:8]

        # Log the incoming request
        logger.info(
            f"→ [{request_id}] {request.method} {request.url.path} "
            f"| client: {request.client.host if request.client else 'unknown'}"
        )

        start_time = time.time()

        # Pass request to the next handler (your route)
        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000

        # Attach the request ID to the response header — useful for debugging
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

        # Log the outgoing response
        logger.info(
            f"← [{request_id}] {response.status_code} "
            f"| {duration_ms:.1f}ms"
        )

        return response
