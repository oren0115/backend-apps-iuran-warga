from fastapi import APIRouter, Depends
from app.models.schemas import NotificationResponse, MessageResponse
from app.controllers.notification_controller import NotificationController
from app.utils.auth import get_current_user
from typing import List

router = APIRouter()
notification_controller = NotificationController()

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(current_user = Depends(get_current_user)):
    """Get all notifications for the current user"""
    return await notification_controller.get_user_notifications(current_user["id"])

@router.put("/notifications/{notification_id}/read", response_model=MessageResponse)
async def mark_notification_read(notification_id: str, current_user = Depends(get_current_user)):
    """Mark a notification as read"""
    return await notification_controller.mark_notification_as_read(notification_id, current_user["id"])

@router.delete("/notifications/{notification_id}", response_model=MessageResponse)
async def delete_notification(notification_id: str, current_user = Depends(get_current_user)):
    """Delete a notification"""
    return await notification_controller.delete_notification(notification_id, current_user["id"])