import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import ws_manager
from app.services.task_service import TaskService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["WebSockets"])


@router.websocket("/api/ws/{task_id}")
async def task_websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time multi-agent execution streaming.
    
    1. Accepts connection and registers client in WebSocketConnectionManager.
    2. Immediately replays any prior persisted events (enabling reconnects).
    3. Runs an active heartbeat keep-alive loop to prevent network proxy timeouts.
    4. Handles client disconnects and task completion cleanly.
    """
    await ws_manager.connect(task_id, websocket)

    # Replay historical events for this task if it already has progress
    try:
        task_data = await TaskService.get_task_details(task_id)
        if task_data and task_data.get("events"):
            for event in task_data["events"]:
                replay_payload = {
                    "task_id": task_id,
                    "agent": event.get("agent_name"),
                    "event_type": event.get("event_type"),
                    "payload": event.get("payload", {}),
                    "timestamp": event.get("timestamp"),
                    "replayed": True
                }
                await websocket.send_text(json.dumps(replay_payload, default=str))

            # If task is already completed or failed, emit terminal notice
            if task_data.get("status") in ["COMPLETED", "FAILED"]:
                status_payload = {
                    "task_id": task_id,
                    "agent": "System",
                    "event_type": f"TASK_{task_data.get('status')}",
                    "payload": {
                        "message": f"Task already reached terminal state: {task_data.get('status')}",
                        "final_result": task_data.get("final_result"),
                        "error": task_data.get("error_message")
                    },
                    "timestamp": task_data.get("completed_at")
                }
                await websocket.send_text(json.dumps(status_payload, default=str))

    except Exception as e:
        logger.warning(f"Error during WebSocket event replay for task {task_id}: {e}")

    # Start periodic ping/heartbeat task to satisfy FAQ requirement
    async def heartbeat_loop():
        try:
            while True:
                await asyncio.sleep(15)
                ping_payload = {
                    "task_id": task_id,
                    "agent": "System",
                    "event_type": "HEARTBEAT",
                    "payload": {"status": "alive"},
                    "timestamp": asyncio.get_event_loop().time()
                }
                await websocket.send_text(json.dumps(ping_payload))
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        except Exception as ping_err:
            logger.debug(f"Heartbeat loop stopped: {ping_err}")

    heartbeat_task = asyncio.create_task(heartbeat_loop())

    try:
        # Keep connection open waiting for incoming messages or disconnect
        while True:
            # Client may send ping messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"event_type": "PONG"}))

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected cleanly from task {task_id}")
    except Exception as e:
        logger.warning(f"WebSocket connection error on task {task_id}: {e}")
    finally:
        heartbeat_task.cancel()
        await ws_manager.disconnect(task_id, websocket)
