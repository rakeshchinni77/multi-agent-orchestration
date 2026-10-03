import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_create_task_success():
    with TestClient(app) as client:
        payload = {"prompt": "What is the current weather in Tokyo and what should I pack?"}
        response = client.post("/api/tasks", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "task_id" in data
        assert uuid.UUID(data["task_id"], version=4)
        assert data["status"] == "PENDING"


def test_create_task_validation_error():
    with TestClient(app) as client:
        response = client.post("/api/tasks", json={"prompt": "hi"})
        assert response.status_code == 422


def test_get_task_details_not_found():
    with TestClient(app) as client:
        random_id = str(uuid.uuid4())
        response = client.get(f"/api/tasks/{random_id}")
        assert response.status_code == 404


def test_get_task_details_invalid_uuid():
    with TestClient(app) as client:
        response = client.get("/api/tasks/not-a-valid-uuid")
        assert response.status_code == 400
