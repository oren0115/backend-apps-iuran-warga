from fastapi import APIRouter, Depends
from app.models import FeeResponse
from app.controllers.fee_controller import FeeController
from app.security.auth import get_current_user
from typing import List

router = APIRouter()
fee_controller = FeeController()

@router.get("/fees", response_model=List[FeeResponse])
async def get_user_fees(current_user = Depends(get_current_user)):
    """Get all fees for the current user - only latest versions (not regenerated)"""
    return await fee_controller.get_user_latest_fees(current_user["id"])