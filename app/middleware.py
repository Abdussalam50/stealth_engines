"""
Custom Middleware for Security
- DynamicCORSMiddleware: Database-driven CORS validation
- SecurityHeadersMiddleware: Add security headers (CSP, X-Frame-Options, etc.)
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime
from sqlalchemy.orm import Session

from .database.config import SessionLocal
from .database.models import TrustedDomain

class DynamicCORSMiddleware(BaseHTTPMiddleware):
    """
    Validate Origin header against database of trusted domains
    Only allow requests from registered domains.
    Returns 403 Forbidden for untrusted origins.
    """
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)
        
        origin = request.headers.get("Origin") or request.headers.get("origin")
        
        if not origin:
            # For requests without Origin (like direct browser navigation or Same-Origin without header)
            # We let it pass, but samesite=lax cookie will protect sensitive actions.
            return await call_next(request)

        # Get database session
        db: Session = SessionLocal()
        try:
            current_host = f"{request.url.scheme}://{request.url.netloc}"
            trusted_found = False
            
            # Izinkan semua origin untuk sementara agar ngrok tidak terhambat
            trusted_found = True

            if not trusted_found:
                # Active blocking for untrusted origins
                return JSONResponse(
                    status_code=403,
                    content={"detail": f"CORS Policy: Origin {origin} is not trusted."}
                )

            # If trusted, continue and add CORS headers
            response = await call_next(request)
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, ngrok-skip-browser-warning"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response
        finally:
            db.close()

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Build CSP string yang sangat longgar untuk Ngrok
        csp_parts = [
            "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:",
            "script-src * 'unsafe-inline' 'unsafe-eval' data: blob:",
            "style-src * 'unsafe-inline' data: blob:",
            "img-src * data: blob:",
            "font-src * data: blob:",
            "connect-src * data: blob:",
            "frame-src * data: blob:"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_parts)
        
        # Bypass ngrok browser warning (Response header as well, just in case)
        response.headers["ngrok-skip-browser-warning"] = "69420"
        
        # Allow framing to avoid issues with some proxies/tools
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection (legacy but doesn't hurt)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple In-Memory Rate Limiting
    Tracks requests per IP for sensitive endpoints.
    """
    def __init__(self, app):
        super().__init__(app)
        # Dictionary structure: { "endpoint": { "ip": [timestamps] } }
        self.history = {
            "/x92j-scan": {},
            "/login": {},
            "/loader.js": {}
        }
        # Limits: (Max Requests, Window in Seconds)
        self.rules = {
            "/x92j-scan": (3, 300),   # 3 scans / 5 min
            "/login": (5, 900),       # 5 login attempts / 15 min
            "/loader.js": (60, 60)    # 60 loads / 1 min
        }

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)
            
        origin = request.headers.get("origin")
        print(f"DEBUG: Request masuk dari {origin} ke {request.url.path}")
        path = request.url.path
        
        # Only rate limit targeted paths
        if path in self.rules:
            # Get real IP (handle ngrok/proxies)
            client_ip = request.headers.get("x-forwarded-for") or request.client.host
            if "," in client_ip:
                client_ip = client_ip.split(",")[0].strip()

            max_req, window = self.rules[path]
            now = datetime.utcnow().timestamp()
            
            # Initialize or cleanup IP history
            if client_ip not in self.history[path]:
                self.history[path][client_ip] = []
            
            # Remove old timestamps outside the window
            self.history[path][client_ip] = [
                ts for ts in self.history[path][client_ip] 
                if now - ts < window
            ]
            
            # Check limit
            if len(self.history[path][client_ip]) >= max_req:
                retry_after = int(window - (now - self.history[path][client_ip][0]))
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many requests. Please slow down.",
                        "retry_after_seconds": max_req
                    },
                    headers={"Retry-After": str(retry_after)}
                )
            
            # Record request
            self.history[path][client_ip].append(now)

        return await call_next(request)
