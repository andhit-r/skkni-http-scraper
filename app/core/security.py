from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Simple header-based API key check using x-api-key."""
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith(('/docs', '/openapi.json', '/health')):
            return await call_next(request)
        expected = (settings.API_KEY or "").strip()
        if expected:
            sent = request.headers.get("x-api-key", "")
            if sent != expected:
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        return await call_next(request)
