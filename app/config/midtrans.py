from midtransclient import Snap, CoreApi
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / '.env')

class MidtransConfig:
    def __init__(self):
        server_key = os.environ.get("MIDTRANS_SERVER_KEY")
        client_key = os.environ.get("MIDTRANS_CLIENT_KEY")
        self.is_production = os.environ.get("MIDTRANS_IS_PRODUCTION", "false").lower() == "true"
        
        # Frontend domain configuration
        self.frontend_domain = os.environ.get("FRONTEND_DOMAIN", "http://localhost:5173")
        self.backend_domain = os.environ.get("BACKEND_DOMAIN", "http://localhost:8000/api")
        
        if not server_key or not client_key:
            raise ValueError("MIDTRANS_SERVER_KEY and MIDTRANS_CLIENT_KEY must be set in environment variables")
        self.server_key = server_key
        self.client_key = client_key
    
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
    
    def get_frontend_callback_urls(self):
        """Get frontend callback URLs for payment completion"""
        return {
            "finish": f"{self.frontend_domain}/payment/success",
            "unfinish": f"{self.frontend_domain}/payment/pending", 
            "error": f"{self.frontend_domain}/payment/failed"
        }
    
    def get_notification_url(self):
        """Get backend notification URL for webhook"""
        return f"{self.backend_domain}/api/payments/notification"

# Global instance
midtrans_config = MidtransConfig()
