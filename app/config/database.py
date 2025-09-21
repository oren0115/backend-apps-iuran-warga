from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Load environment variables from .env file
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / '.env.development')

class DatabaseManager:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

# Create global instance
database_manager = DatabaseManager()

async def init_database():
    # inisiasi koneksi database
    try:
        mongo_url = os.environ.get("MONGO_URL", "")
        database_name = os.environ.get("DB_NAME", "")
        database_manager.client = AsyncIOMotorClient(mongo_url)
        database_manager.database = database_manager.client[database_name]
        database_manager.database.command("ping")
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise e

async def close_database():
    # tutup koneksi database
    if database_manager.client:
        database_manager.client.close()
        logger.info("Database connection closed")

def get_database() -> AsyncIOMotorDatabase:
    """
    Get the database instance.
    Raises RuntimeError if database is not initialized.
    """
    if database_manager.database is None:
        raise RuntimeError("Database not initialized. Make sure to call init_database() first.")
    return database_manager.database

