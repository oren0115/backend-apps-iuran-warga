from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Load environment variables from .env file
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / '.env')

class DatabaseManager:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

# Create global instance
database_manager = DatabaseManager()

async def init_database():
    # inisiasi koneksi database
    try:
        mongo_url = os.environ.get("MONGO_URL")
        database_name = os.environ.get("DB_NAME")
        
        if not mongo_url:
            logger.warning("MONGO_URL not set, using default localhost")
            mongo_url = "mongodb://localhost:27017"
        
        if not database_name:
            logger.warning("DB_NAME not set, using default")
            database_name = "rt_rw_management"
        
        logger.info(f"Connecting to MongoDB: {mongo_url}")
        logger.info(f"Database name: {database_name}")
        
        database_manager.client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
        database_manager.database = database_manager.client[database_name]
        
        # Test connection
        await database_manager.database.command("ping")
        logger.info("Database connection successful")
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        # Don't raise exception in production, let app start without database
        logger.warning("Continuing without database connection")
        database_manager.client = None
        database_manager.database = None

async def close_database():
    # tutup koneksi database
    if database_manager.client:
        database_manager.client.close()

def get_database() -> AsyncIOMotorDatabase:
    """
    Get the database instance.
    Raises RuntimeError if database is not initialized.
    """
    if database_manager.database is None:
        raise RuntimeError("Database not initialized. Make sure to call init_database() first.")
    return database_manager.database

