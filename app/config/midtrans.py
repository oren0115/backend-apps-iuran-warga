from midtransclient import Snap, CoreApi
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / '.env')

class MidtransConfig:
    def __init__(self):
        self.server_key = os.environ.get("MIDTRANS_SERVER_KEY")
        self.client_key = os.environ.get("MIDTRANS_CLIENT_KEY")
        self.is_production = os.environ.get("MIDTRANS_IS_PRODUCTION", "false").lower() == "true"
        
        if not self.server_key or not self.client_key:
            raise ValueError("MIDTRANS_SERVER_KEY and MIDTRANS_CLIENT_KEY must be set in environment variables")
    
    def get_snap_client(self):
        """Get configured Midtrans Snap client"""
        return Snap(
            is_production=self.is_production,
            server_key=self.server_key,
            client_key=self.client_key
        )
    
    def get_core_api_client(self):
        """Get configured Midtrans Core API client"""
        return CoreApi(
            is_production=self.is_production,
            server_key=self.server_key,
            client_key=self.client_key
        )

# Global instance
midtrans_config = MidtransConfig()
