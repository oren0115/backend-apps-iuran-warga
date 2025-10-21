from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models import UserCreate, UserLogin, UserResponse, LoginResponse, MessageResponse, UserUpdate
from app.controllers.user_controller import UserController
from app.security.auth import get_current_user, get_current_admin

router = APIRouter()
user_controller = UserController()

# Initialize limiter for this router
limiter = Limiter(key_func=get_remote_address)

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, current_user = Depends(get_current_admin)):
    """Register a new user (admin only)"""
    return await user_controller.register_user(user_data)

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(login_data: UserLogin, request: Request):
    """Login user and return access token"""
    return await user_controller.login_user(login_data)

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user = Depends(get_current_user)):
    """Get current user profile"""
    return await user_controller.get_user_profile(current_user)

@router.put("/profile", response_model=UserResponse)
async def update_profile(data: UserUpdate, current_user = Depends(get_current_admin)):
    """Update current user profile (admin only)"""
    return await user_controller.update_user_profile(current_user, data)