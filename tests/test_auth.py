def test_register_success(client):
    res = client.post("/api/auth/register", json={
        "username": "janedoe",
        "email": "jane@example.com",
        "password": "securepassword",
        "full_name": "Jane Doe",
        "currency": "EUR"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert "token" in data
    assert data["user"]["username"] == "janedoe"
    assert data["user"]["email"] == "jane@example.com"
    assert data["user"]["currency"] == "EUR"

def test_register_duplicate(client):
    client.post("/api/auth/register", json={
        "username": "duplicate_user",
        "email": "dup@example.com",
        "password": "password123"
    })
    res = client.post("/api/auth/register", json={
        "username": "duplicate_user",
        "email": "different@example.com",
        "password": "password123"
    })
    assert res.status_code == 409

def test_login_success(client):
    client.post("/api/auth/register", json={
        "username": "login_user",
        "email": "login@example.com",
        "password": "correct_password"
    })
    res = client.post("/api/auth/login", json={
        "username": "login_user",
        "password": "correct_password"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "token" in data
    assert data["user"]["username"] == "login_user"

def test_login_invalid_password(client):
    client.post("/api/auth/register", json={
        "username": "wrong_pwd_user",
        "email": "wrongpwd@example.com",
        "password": "mypassword"
    })
    res = client.post("/api/auth/login", json={
        "username": "wrong_pwd_user",
        "password": "wrongpassword"
    })
    assert res.status_code == 401

def test_get_me_unauthorized(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401

def test_get_me_authorized(auth_client):
    res = auth_client.get("/api/auth/me")
    assert res.status_code == 200
    data = res.get_json()
    assert data["user"]["username"] == "tester"

def test_update_profile(auth_client):
    res = auth_client.put("/api/auth/profile", json={
        "full_name": "Updated Name",
        "currency": "GBP"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["user"]["full_name"] == "Updated Name"
    assert data["user"]["currency"] == "GBP"

def test_logout(auth_client):
    res = auth_client.post("/api/auth/logout")
    assert res.status_code == 200
