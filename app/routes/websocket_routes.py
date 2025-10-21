from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.websocket_manager import websocket_manager
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str = Query(None)):
    """WebSocket endpoint for real-time notifications"""
    # For now, we'll skip authentication to test the connection
    # In production, you should validate the token here
    
    await websocket_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Keep the connection alive by listening for messages
            data = await websocket.receive_text()
            
            # Echo back the message (optional)
            await websocket.send_text(f"Echo: {data}")
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        websocket_manager.disconnect(websocket)

