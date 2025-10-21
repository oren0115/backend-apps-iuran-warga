from fastapi import FastAPI, Request, Response
from app.config.database import init_database, close_database
from app.routes import user_routes, fee_routes, payment_routes, notification_routes, admin_routes, websocket_routes, telegram_routes
from app.middleware import setup_cors_middleware, setup_security_middleware, setup_rate_limiting_middleware
from app.middleware.security_middleware import add_security_headers, add_hsts_header
import logging

# Create the main app
app = FastAPI(title="IPL Cluster Cannary Management API")



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
app.include_router(telegram_routes.router, prefix="/api/telegram", tags=["telegram"])


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await init_database()
    
    # Setup Telegram webhook if configured
    # try:
    #     from app.config.telegram import TelegramConfig
    #     if TelegramConfig.is_configured():
    #         from setup_telegram_webhook import TelegramWebhookSetup
    #         setup = TelegramWebhookSetup()
    #         await setup.set_webhook()
    #         logger.info("Telegram webhook configured successfully")
    #     else:
    #         logger.warning("Telegram not configured, skipping webhook setup")
    # except Exception as e:
    #     logger.error(f"Failed to setup Telegram webhook: {e}")
    
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
