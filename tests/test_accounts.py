def test_list_default_accounts(auth_client):
    res = auth_client.get("/api/accounts")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["accounts"]) >= 2
    names = [a["name"] for a in data["accounts"]]
    assert "Main Checking" in names
    assert "Emergency Savings" in names

def test_create_account(auth_client):
    res = auth_client.post("/api/accounts", json={
        "name": "Crypto & Stocks",
        "type": "investment",
        "initial_balance": 5000.0,
        "currency": "USD",
        "account_number": "INV-1001"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["account"]["name"] == "Crypto & Stocks"
    assert data["account"]["balance"] == 5000.0
    assert data["account"]["type"] == "investment"

def test_create_account_invalid_type(auth_client):
    res = auth_client.post("/api/accounts", json={
        "name": "Invalid Account",
        "type": "unsupported_type"
    })
    assert res.status_code == 400

def test_get_account_detail(auth_client):
    res = auth_client.get("/api/accounts")
    first_acc_id = res.get_json()["accounts"][0]["id"]

    detail_res = auth_client.get(f"/api/accounts/{first_acc_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.get_json()
    assert detail_data["account"]["id"] == first_acc_id
    assert "recent_transactions" in detail_data

def test_update_account(auth_client):
    res = auth_client.post("/api/accounts", json={
        "name": "Old Name",
        "type": "checking",
        "initial_balance": 100.0
    })
    acc_id = res.get_json()["account"]["id"]

    update_res = auth_client.put(f"/api/accounts/{acc_id}", json={
        "name": "Renamed Checking",
        "initial_balance": 250.0
    })
    assert update_res.status_code == 200
    updated = update_res.get_json()["account"]
    assert updated["name"] == "Renamed Checking"
    assert updated["balance"] == 250.0

def test_delete_account(auth_client):
    res = auth_client.post("/api/accounts", json={
        "name": "Temporary Account",
        "type": "cash",
        "initial_balance": 50.0
    })
    acc_id = res.get_json()["account"]["id"]

    del_res = auth_client.delete(f"/api/accounts/{acc_id}")
    assert del_res.status_code == 200

    check_res = auth_client.get(f"/api/accounts/{acc_id}")
    assert check_res.status_code == 404
