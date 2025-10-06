from fastapi import FastAPI, Request, Response
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config.database import init_database, close_database
from app.routes import user_routes, fee_routes, payment_routes, notification_routes, admin_routes, websocket_routes, telegram_routes
import logging

# Create the main app
app = FastAPI(title="RT/RW Fee Management API")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app", "*.onrender.com", "*.ngrok-free.app"]
)

# Add CORS middleware
# NOTE: When allow_credentials=True, you cannot use wildcard "*" for allow_origins.
# Explicitly list the frontend origins (Vite defaults to 5173).
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://iuran-warga-phi.vercel.app",
        "https://backend-apps-iuran-warga.onrender.com",
        "https://*.ngrok-free.app",
    ],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# Include routers
app.include_router(user_routes.router, prefix="/api", tags=["users"])
app.include_router(fee_routes.router, prefix="/api", tags=["fees"])
app.include_router(payment_routes.router, prefix="/api", tags=["payments"])
app.include_router(notification_routes.router, prefix="/api", tags=["notifications"])
app.include_router(admin_routes.router, prefix="/api/admin", tags=["admin"])
app.include_router(websocket_routes.router, prefix="/api", tags=["websocket"])
app.include_router(telegram_routes.router, prefix="/api/telegram", tags=["telegram"])

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await init_database()
    logger.info("Application started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    await close_database()
    logger.info("Application shut down successfully")

@app.get("/")
async def root():
    return {"message": "Api IPL Cluster Cannary is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
