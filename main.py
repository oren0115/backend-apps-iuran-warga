from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.config.database import init_database, close_database
from app.routes import user_routes, fee_routes, payment_routes, notification_routes, admin_routes
import logging

# Create the main app
app = FastAPI(title="RT/RW Fee Management API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user_routes.router, prefix="/api", tags=["users"])
app.include_router(fee_routes.router, prefix="/api", tags=["fees"])
app.include_router(payment_routes.router, prefix="/api", tags=["payments"])
app.include_router(notification_routes.router, prefix="/api", tags=["notifications"])
app.include_router(admin_routes.router, prefix="/api/admin", tags=["admin"])

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
    return {"message": "RT/RW Fee Management API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)