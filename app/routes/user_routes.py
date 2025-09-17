from fastapi import APIRouter, Depends
from app.models.schemas import UserCreate, UserLogin, UserResponse, LoginResponse, MessageResponse
from app.controllers.user_controller import UserController
from app.utils.auth import get_current_user

router = APIRouter()
user_controller = UserController()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    return await user_controller.register_user(user_data)

@router.post("/login", response_model=LoginResponse)
async def login(login_data: UserLogin):
    """Login user and return access token"""
    return await user_controller.login_user(login_data)

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user = Depends(get_current_user)):
    """Get current user profile"""
    return await user_controller.get_user_profile(current_user)

@router.put("/toggle-admin", response_model=MessageResponse)
async def toggle_admin(current_user = Depends(get_current_user)):
    """Toggle user admin status (for testing purposes)"""
    return await user_controller.toggle_admin_status(current_user)