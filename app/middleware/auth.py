"""
middleware/auth.py — Authentication via Dependency Injection
=============================================================
CONCEPT: FastAPI Dependency Injection (Depends)

Dependency Injection (DI) is one of FastAPI's most powerful features.
Instead of duplicating auth logic in every endpoint, you write it ONCE
and inject it wherever needed.

How it works:
  1. You write a function (the "dependency")
  2. You pass it to Depends() in your route function signature
  3. FastAPI calls your dependency automatically before calling your route
  4. If the dependency raises an HTTPException, the route never runs

Analogy: Think of it like a bouncer. The bouncer checks the ID.
If ID is invalid → nobody gets in. If valid → the main function runs.

Why AI engineers need this:
  - Every production AI API (OpenAI, HuggingFace, etc.) uses API key auth
  - You'll protect /predict, /stream, /vision behind auth
  - Health check stays public (no auth) — useful for load balancers
"""

from fastapi import Header, HTTPException, status
from app.config import settings


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """
    Dependency function: validates the API key from the request header.

    Parameters:
      x_api_key: FastAPI reads the "X-API-Key" header automatically.
                 `alias="X-API-Key"` maps the HTTP header name to the
                 Python variable name (headers use hyphens, Python uses underscores).

    Returns:
      The API key string if valid (used by the route if it needs it).

    Raises:
      HTTPException 401 if the key is missing or wrong.

    USAGE in a router:
      @router.post("/predict")
      async def predict(
          body: PredictRequest,
          api_key: str = Depends(verify_api_key)   # ← inject here
      ):
          ...
    """
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key. Pass your key in the X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},  # standard HTTP practice
        )
    return x_api_key


# ─────────────────────────────────────────────────────────
# ADVANCED: You can chain dependencies (dependency of a dependency)
#
# Example: a dependency that checks the key AND checks rate limits:
#
# async def rate_limited_auth(api_key: str = Depends(verify_api_key)):
#     if is_rate_limited(api_key):
#         raise HTTPException(429, "Rate limit exceeded")
#     return api_key
#
# Then in your route:
#   async def predict(..., _=Depends(rate_limited_auth)):
#       ...
# ─────────────────────────────────────────────────────────
