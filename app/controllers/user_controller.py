from fastapi import HTTPException, status
from app.models.schemas import User, UserCreate, UserLogin, UserResponse, LoginResponse, UserUpdate, PasswordUpdate
from app.utils.auth import AuthManager
from app.config.database import get_database
import uuid
from datetime import datetime

class UserController:
    def __init__(self):
        self.auth_manager = AuthManager()

    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user"""
        db = get_database()
        
        # Check if username exists
        existing_user = await db.users.find_one({"username": user_data.username})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username sudah digunakan"
            )
        
        # Create user
        user_dict = user_data.dict()
        user_dict["password"] = self.auth_manager.hash_password(user_dict["password"])
        user_dict["id"] = str(uuid.uuid4())
        user_dict["is_admin"] = False
        user_dict["created_at"] = datetime.utcnow()
        
        await db.users.insert_one(user_dict)
        
        return UserResponse(**{k: v for k, v in user_dict.items() if k != "password"})

    async def login_user(self, login_data: UserLogin) -> LoginResponse:
        """Login user and return token"""
        db = get_database()
        
        user = await db.users.find_one({"username": login_data.username})
        if not user or not self.auth_manager.verify_password(login_data.password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username atau password salah"
            )
        
        access_token = self.auth_manager.create_access_token(data={"sub": user["username"]})
        user_response = UserResponse(**{k: v for k, v in user.items() if k != "password"})
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )

    async def get_user_profile(self, current_user: dict) -> UserResponse:
        """Get current user profile"""
        return UserResponse(**{k: v for k, v in current_user.items() if k != "password"})

    async def update_user_profile(self, current_user: dict, updates: UserUpdate) -> UserResponse:
        """Update current user profile"""
        db = get_database()
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        if not update_dict:
            return UserResponse(**{k: v for k, v in current_user.items() if k != "password"})
        await db.users.update_one({"id": current_user["id"]}, {"$set": update_dict})
        user = await db.users.find_one({"id": current_user["id"]})
        return UserResponse(**{k: v for k, v in user.items() if k != "password"})

    async def toggle_admin_status(self, current_user: dict) -> dict:
        """Toggle user admin status"""
        db = get_database()
        
        await db.users.update_one(
            {"id": current_user["id"]}, 
            {"$set": {"is_admin": not current_user["is_admin"]}}
        )
        return {"message": "Status admin berhasil diubah"}

    async def get_all_users(self) -> list[UserResponse]:
        """Get all users (admin only)"""
        db = get_database()
        
        users = await db.users.find().to_list(1000)
        return [UserResponse(**{k: v for k, v in user.items() if k != "password"}) for user in users]

    async def update_user_by_id(self, user_id: str, updates: UserUpdate) -> UserResponse:
        """Update a user's profile by id (admin only)"""
        db = get_database()
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        if not update_dict:
            user = await db.users.find_one({"id": user_id})
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")
            return UserResponse(**{k: v for k, v in user.items() if k != "password"})
        result = await db.users.update_one({"id": user_id}, {"$set": update_dict})
        if result.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")
        user = await db.users.find_one({"id": user_id})
        return UserResponse(**{k: v for k, v in user.items() if k != "password"})

    async def update_user_password_by_id(self, user_id: str, payload: PasswordUpdate) -> dict:
        """Update a user's password by id (admin only)"""
        db = get_database()
        hashed = self.auth_manager.hash_password(payload.new_password)
        result = await db.users.update_one({"id": user_id}, {"$set": {"password": hashed}})
        if result.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")
        return {"message": "Password pengguna berhasil diperbarui"}