from fastapi import HTTPException, Depends, status, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta, timezone
import hashlib
import jwt
import os
from dotenv import load_dotenv
from app.config.database import get_database

# Load environment variables
load_dotenv()

# Security
security = HTTPBearer()

# JWT Configuration with validation
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Validate JWT configuration
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is required but not set")

if len(JWT_SECRET) < 32:
    raise ValueError("JWT_SECRET must be at least 32 characters long for security")

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
        try:
            to_encode = data.copy()
            # Use Jakarta timezone for token expiration
            jakarta_tz = timezone(timedelta(hours=7))
            expire = datetime.now(jakarta_tz) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            to_encode.update({"exp": expire})
            return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create access token: {str(e)}"
            )

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
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication error: {str(e)}"
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

async def get_current_user_websocket(websocket: WebSocket, token: str = None):
    """Get current user from WebSocket token"""
    try:
        if not token:
            await websocket.close(code=1008, reason="No token provided")
            return None
            
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            await websocket.close(code=1008, reason="Invalid token")
            return None
        
        db = get_database()
        user = await db.users.find_one({"username": username})
        if user is None:
            await websocket.close(code=1008, reason="User not found")
            return None
        
        return user
    except jwt.ExpiredSignatureError:
        await websocket.close(code=1008, reason="Token has expired")
        return None
    except jwt.InvalidTokenError:
        await websocket.close(code=1008, reason="Invalid token")
        return None
    except Exception as e:
        await websocket.close(code=1011, reason="Internal error")
        return None
