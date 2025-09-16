from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp
import time
from collections import defaultdict
import logging
import os

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, allowed_origins: list = None, rate_limit: int = 100, rate_limit_interval: int = 60):
        super().__init__(app)
        self.allowed_origins = allowed_origins if allowed_origins is not None else []
        self.rate_limit = rate_limit
        self.rate_limit_interval = rate_limit_interval
        self.request_counts = defaultdict(lambda: {'count': 0, 'timestamp': 0})

    async def dispatch(self, request, call_next):
        # 1. CORS Headers
        origin = request.headers.get('origin')
        if origin and origin in self.allowed_origins:
            request.scope['headers'].append((b'access-control-allow-origin', origin.encode()))
            request.scope['headers'].append((b'access-control-allow-credentials', b'true'))
            request.scope['headers'].append((b'access-control-allow-methods', b'*'))
            request.scope['headers'].append((b'access-control-allow-headers', b'*'))

        # 2. Security Headers
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';"

        # 3. Rate Limiting
        client_ip = request.client.host
        current_time = time.time()

        if current_time - self.request_counts[client_ip]['timestamp'] > self.rate_limit_interval:
            self.request_counts[client_ip] = {'count': 1, 'timestamp': current_time}
        else:
            self.request_counts[client_ip]['count'] += 1

        if self.request_counts[client_ip]['count'] > self.rate_limit:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."}
            )

        # 4. Request Logging
        logger.info(f"Request: {request.method} {request.url} from {client_ip}")
        return response
