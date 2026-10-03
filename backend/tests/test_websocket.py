import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.websocket_manager import ws_manager

client = TestClient(app)


def test_websocket_connection_and_ping():
    with client.websocket_connect("/api/ws/test-ws-task-1") as websocket:
        # Send ping
        websocket.send_text("ping")
        data = websocket.receive_json()
        assert data.get("event_type") == "PONG"


@pytest.mark.asyncio
async def test_websocket_broadcast():
    task_id = "test-broadcast-task"
    # Verify manager listeners count
    assert ws_manager.get_listener_count(task_id) == 0
