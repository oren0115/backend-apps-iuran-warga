from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from app.config.database import init_database, close_database
from app.routes import user_routes, fee_routes, payment_routes, notification_routes, admin_routes, websocket_routes
from app.middleware import setup_cors_middleware, setup_security_middleware, setup_rate_limiting_middleware
from app.middleware.security_middleware import add_security_headers, add_hsts_header
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Don't raise exception, let app start without database for testing
    
    logger.info("Application started successfully")
    yield
    
    # Shutdown
    try:
        await close_database()
        logger.info("Database connection closed successfully")
    except Exception as e:
        logger.error(f"Failed to close database: {e}")
    
    logger.info("Application shut down successfully")

# Create the main app with lifespan
app = FastAPI(title="IPL Cluster Cannary Management API", lifespan=lifespan)



# Setup middleware
setup_rate_limiting_middleware(app)
setup_security_middleware(app)
setup_cors_middleware(app)

# Add custom middleware
@app.middleware("http")
async def security_headers_middleware(request, call_next):
    return await add_security_headers(request, call_next)

@app.middleware("http")
async def hsts_middleware(request, call_next):
    return await add_hsts_header(request, call_next)


# Include routers
app.include_router(user_routes.router, prefix="/api", tags=["users"])
app.include_router(fee_routes.router, prefix="/api", tags=["fees"])
app.include_router(payment_routes.router, prefix="/api", tags=["payments"])
app.include_router(notification_routes.router, prefix="/api", tags=["notifications"])
app.include_router(admin_routes.router, prefix="/api/admin", tags=["admin"])
app.include_router(websocket_routes.router, prefix="/api", tags=["websocket"])


# Health check endpoint untuk testing
@app.get("/health")
async def health_check():
    from app.config.database import database_manager
    
    database_status = "disconnected"
    if database_manager.database:
        try:
            await database_manager.database.command("ping")
            database_status = "connected"
        except Exception as e:
            database_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "message": "API is running",
        "database": database_status,
        "environment": {
            "mongo_url_set": bool(os.getenv("MONGO_URL")),
            "db_name_set": bool(os.getenv("DB_NAME")),
        }
    }

@app.get("/")
async def root():
    return {"message": "Api IPL Cluster Cannary is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
