import json
import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # Dictionary to store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Dictionary to store user_id by websocket for cleanup
        self.websocket_to_user: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new WebSocket connection and associate it with a user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.websocket_to_user[websocket] = user_id
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.websocket_to_user:
            user_id = self.websocket_to_user[websocket]
            
            # Remove from user's connections
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                
                # Clean up empty user entry
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Remove from websocket mapping
            del self.websocket_to_user[websocket]
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to a specific user"""
        if user_id in self.active_connections:
            # Create a copy of the set to avoid modification during iteration
            connections = self.active_connections[user_id].copy()
            
            # Send to all connections for this user in parallel
            import asyncio
            tasks = []
            for websocket in connections:
                task = self._send_to_websocket(websocket, message, user_id)
                tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_to_websocket(self, websocket: WebSocket, message: dict, user_id: str):
        """Helper method to send message to a single websocket"""
        try:
            # Convert datetime objects to strings for JSON serialization
            def json_serializer(obj):
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            await websocket.send_text(json.dumps(message, default=json_serializer))
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {e}")
            # Remove the failed connection
            self.disconnect(websocket)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected users"""
        # Create a copy of all connections to avoid modification during iteration
        all_connections = []
        for user_connections in self.active_connections.values():
            all_connections.extend(user_connections)
        
        for websocket in all_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                # Remove the failed connection
                self.disconnect(websocket)
    
    async def send_notification(self, user_id: str, notification: dict):
        """Send a notification to a specific user"""
        message = {
            "type": "notification",
            "data": notification
        }
        await self.send_personal_message(message, user_id)
    
    async def broadcast_notification(self, notification: dict):
        """Broadcast a notification to all connected users"""
        message = {
            "type": "notification",
            "data": notification
        }
        await self.broadcast_to_all(message)
    
    def get_connected_users(self) -> List[str]:
        """Get list of currently connected user IDs"""
        return list(self.active_connections.keys())
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.websocket_to_user)

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
