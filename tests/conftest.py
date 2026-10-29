import os
import sys
import tempfile
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from backend.database import init_db

@pytest.fixture
def app():
    # Create temporary database file for isolated testing
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    app = create_app({
        "TESTING": True,
        "DATABASE_PATH": db_path,
        "SECRET_KEY": "test-secret-key"
    })

    yield app

    # Cleanup temporary database file
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """Registers a user and returns client with authorization headers."""
    reg_res = client.post("/api/auth/register", json={
        "username": "tester",
        "email": "tester@example.com",
        "password": "password123",
        "full_name": "Test User",
        "currency": "USD"
    })
    data = reg_res.get_json()
    token = data["token"]

    class AuthClient:
        def __init__(self, raw_client, auth_token):
            self.raw = raw_client
            self.headers = {"Authorization": f"Bearer {auth_token}"}
            self.user = data["user"]

        def get(self, url, **kwargs):
            headers = {**self.headers, **kwargs.pop("headers", {})}
            return self.raw.get(url, headers=headers, **kwargs)

        def post(self, url, **kwargs):
            headers = {**self.headers, **kwargs.pop("headers", {})}
            return self.raw.post(url, headers=headers, **kwargs)

        def put(self, url, **kwargs):
            headers = {**self.headers, **kwargs.pop("headers", {})}
            return self.raw.put(url, headers=headers, **kwargs)

        def delete(self, url, **kwargs):
            headers = {**self.headers, **kwargs.pop("headers", {})}
            return self.raw.delete(url, headers=headers, **kwargs)

    return AuthClient(client, token)
