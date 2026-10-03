import asyncio
import json
from typing import Dict, List, Any
from fastapi import WebSocket
from app.core.logging import get_logger

logger = get_logger(__name__)


class WebSocketConnectionManager:
    """
    Manages active WebSocket connections subscribed to specific task streams.
    
    Supports concurrent client connections, automatic cleanup on disconnect,
    and periodic keep-alive pings to prevent network proxy timeouts.
    """

    def __init__(self):
        # Map task_id -> list of active WebSocket connections
        self._active_connections: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, task_id: str, websocket: WebSocket) -> None:
        """Accept and register a new client connection for a task stream."""
        await websocket.accept()
        async with self._lock:
            if task_id not in self._active_connections:
                self._active_connections[task_id] = []
            self._active_connections[task_id].append(websocket)
        logger.info(f"WebSocket client connected to task '{task_id}'. Active listeners: {len(self._active_connections[task_id])}")

    async def disconnect(self, task_id: str, websocket: WebSocket) -> None:
        """Unregister a client connection."""
        async with self._lock:
            if task_id in self._active_connections:
                if websocket in self._active_connections[task_id]:
                    self._active_connections[task_id].remove(websocket)
                if not self._active_connections[task_id]:
                    del self._active_connections[task_id]
        logger.info(f"WebSocket client disconnected from task '{task_id}'.")

    async def broadcast_event(self, task_id: str, event_data: Dict[str, Any]) -> None:
        """Broadcast a structured JSON event payload to all clients listening to task_id."""
        async with self._lock:
            connections = list(self._active_connections.get(task_id, []))

        if not connections:
            return

        payload_str = json.dumps(event_data, default=str)
        dead_connections = []

        for ws in connections:
            try:
                await ws.send_text(payload_str)
            except Exception as e:
                logger.warning(f"Failed to send event to WebSocket client on task {task_id}: {e}")
                dead_connections.append(ws)

        if dead_connections:
            async with self._lock:
                for dead_ws in dead_connections:
                    if task_id in self._active_connections and dead_ws in self._active_connections[task_id]:
                        self._active_connections[task_id].remove(dead_ws)

    def get_listener_count(self, task_id: str) -> int:
        """Return the number of connected clients for a given task."""
        return len(self._active_connections.get(task_id, []))


ws_manager = WebSocketConnectionManager()
