import os
import json
import pytest

# Force in-memory backend for tests BEFORE importing app
os.environ["FORCE_BACKEND"] = "memory"
from api.app import app  # noqa: E402

@pytest.fixture()
def client():
    app.config.update({"TESTING": True})
    with app.test_client() as c:
        yield c


def test_list_empty(client):
    rv = client.get("/api/tasks")
    assert rv.status_code == 200
    assert rv.is_json
    assert rv.get_json() == []


def test_create_and_get(client):
    rv = client.post("/api/tasks", data=json.dumps({"title": "Test"}), content_type="application/json")
    assert rv.status_code == 201
    task = rv.get_json()
    assert task["id"] == 1
    assert task["title"] == "Test"
    assert task["done"] is False

    rv = client.get("/api/tasks/1")
    assert rv.status_code == 200
    assert rv.get_json()["title"] == "Test"


def test_update_toggle_and_title(client):
    # Create one
    client.post("/api/tasks", data=json.dumps({"title": "A"}), content_type="application/json")

    # Toggle done
    rv = client.put("/api/tasks/1", data=json.dumps({"done": True}), content_type="application/json")
    assert rv.status_code == 200
    assert rv.get_json()["done"] is True

    # Edit title
    rv = client.put("/api/tasks/1", data=json.dumps({"title": "B"}), content_type="application/json")
    assert rv.status_code == 200
    assert rv.get_json()["title"] == "B"


def test_delete_and_missing(client):
    client.post("/api/tasks", data=json.dumps({"title": "To del"}), content_type="application/json")

    rv = client.delete("/api/tasks/1")
    assert rv.status_code == 200

    # Now missing
    rv = client.get("/api/tasks/1")
    assert rv.status_code == 404
    assert rv.get_json()["error"] == "Task not found"

    rv = client.delete("/api/tasks/1")
    assert rv.status_code == 404
