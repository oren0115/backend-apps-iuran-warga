from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / '.env')

class DatabaseManager:
    client: AsyncIOMotorClient = None
    database: None

# Create global instance
database_manager = DatabaseManager()

async def init_database():
    # inisiasi koneksi database
    try:
        mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        database_name = os.environ.get("DB_NAME", "rt_rw_management")
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

def get_database():
    return database_manager.database

