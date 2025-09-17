from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
import hashlib
import jwt
from app.config.database import get_database

# Security
security = HTTPBearer()
JWT_SECRET = "rt_rw_secret_key_123"
JWT_ALGORITHM = "HS256"

class AuthManager:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return AuthManager.hash_password(password) == hashed

    @staticmethod
    def create_access_token(data: dict) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=24)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current user from JWT token"""
        try:
            payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            db = get_database()
            user = await db.users.find_one({"username": username})
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            return user
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    @staticmethod
    async def get_current_admin(current_user = Depends(get_current_user)):
        """Get current admin user"""
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akses ditolak - hanya admin yang diizinkan"
            )
        return current_user

# Create dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await AuthManager.get_current_user(credentials)

async def get_current_admin(current_user = Depends(get_current_user)):
    return await AuthManager.get_current_admin(current_user)