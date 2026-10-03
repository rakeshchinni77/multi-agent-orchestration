import pytest
import os


def test_project_structure_exists():
    """Verify that essential project directories and files exist as specified."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    expected_paths = [
        "backend/app/main.py",
        "backend/app/agents/graph.py",
        "backend/app/tools/registry.py",
        "backend/app/worker/celery_app.py",
        "frontend/src/App.tsx",
        "docker-compose.yml",
        ".env.example",
        "README.md",
        "EVALUATION.md",
        "ARCHITECTURE.md",
    ]
    for p in expected_paths:
        full_path = os.path.join(root, p)
        assert os.path.exists(full_path), f"Expected path does not exist: {p}"
