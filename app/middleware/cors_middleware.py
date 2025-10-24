"""
CORS Middleware Configuration
"""
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI


def setup_cors_middleware(app: FastAPI) -> None:
    """
    Setup CORS middleware for the application
    """
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=[
            "http://localhost:5173",
            "https://iuran-warga-phi.vercel.app",
            "https://backend-apps-iuran-warga.onrender.com",
            "https://*.ngrok-free.app",
            "https://backend-apps-iuran-warga.vercel.app",
            "https://*.vercel.app",  # Allow all Vercel subdomains
            "https://www.iplcannary.cloud",
            "https://iplcannary.cloud"
        ],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    )
