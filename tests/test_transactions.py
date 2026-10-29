def test_income_transaction_adjusts_balance(auth_client):
    acc_res = auth_client.get("/api/accounts")
    acc_id = acc_res.get_json()["accounts"][0]["id"]
    initial_balance = acc_res.get_json()["accounts"][0]["balance"]

    txn_res = auth_client.post("/api/transactions", json={
        "account_id": acc_id,
        "type": "income",
        "amount": 1500.0,
        "date": "2026-10-01",
        "description": "Consulting Income"
    })
    assert txn_res.status_code == 201

    updated_acc = auth_client.get(f"/api/accounts/{acc_id}").get_json()["account"]
    assert updated_acc["balance"] == initial_balance + 1500.0

def test_expense_transaction_adjusts_balance(auth_client):
    acc_res = auth_client.get("/api/accounts")
    acc_id = acc_res.get_json()["accounts"][0]["id"]
    initial_balance = acc_res.get_json()["accounts"][0]["balance"]

    txn_res = auth_client.post("/api/transactions", json={
        "account_id": acc_id,
        "type": "expense",
        "amount": 250.0,
        "date": "2026-10-02",
        "description": "Grocery shopping"
    })
    assert txn_res.status_code == 201

    updated_acc = auth_client.get(f"/api/accounts/{acc_id}").get_json()["account"]
    assert updated_acc["balance"] == initial_balance - 250.0

def test_transfer_between_accounts(auth_client):
    accounts = auth_client.get("/api/accounts").get_json()["accounts"]
    src_id = accounts[0]["id"]
    dst_id = accounts[1]["id"]
    src_initial = accounts[0]["balance"]
    dst_initial = accounts[1]["balance"]

    transfer_res = auth_client.post("/api/transactions/transfer", json={
        "from_account_id": src_id,
        "to_account_id": dst_id,
        "amount": 300.0,
        "date": "2026-10-03",
        "description": "Savings Allocation"
    })
    assert transfer_res.status_code == 201

    src_after = auth_client.get(f"/api/accounts/{src_id}").get_json()["account"]["balance"]
    dst_after = auth_client.get(f"/api/accounts/{dst_id}").get_json()["account"]["balance"]

    assert src_after == src_initial - 300.0
    assert dst_after == dst_initial + 300.0

def test_transactions_filtering(auth_client):
    acc_id = auth_client.get("/api/accounts").get_json()["accounts"][0]["id"]

    auth_client.post("/api/transactions", json={
        "account_id": acc_id,
        "type": "expense",
        "amount": 45.0,
        "date": "2026-10-05",
        "description": "Special Dinner",
        "tags": "dining,special"
    })
    auth_client.post("/api/transactions", json={
        "account_id": acc_id,
        "type": "income",
        "amount": 200.0,
        "date": "2026-10-06",
        "description": "Freelance Gig",
        "tags": "work"
    })

    # Search filter
    search_res = auth_client.get("/api/transactions?search=Special").get_json()
    assert search_res["total"] == 1
    assert search_res["transactions"][0]["description"] == "Special Dinner"

    # Type filter
    type_res = auth_client.get("/api/transactions?type=income").get_json()
    assert all(t["type"] == "income" for t in type_res["transactions"])

def test_update_and_delete_transaction_balance_sync(auth_client):
    acc_id = auth_client.get("/api/accounts").get_json()["accounts"][0]["id"]
    initial_balance = auth_client.get(f"/api/accounts/{acc_id}").get_json()["account"]["balance"]

    # 1. Create 100 expense
    create_res = auth_client.post("/api/transactions", json={
        "account_id": acc_id,
        "type": "expense",
        "amount": 100.0,
        "date": "2026-10-07",
        "description": "Office supplies"
    })
    txn_id = create_res.get_json()["transaction"]["id"]
    assert auth_client.get(f"/api/accounts/{acc_id}").get_json()["account"]["balance"] == initial_balance - 100.0

    # 2. Update to 150 expense
    auth_client.put(f"/api/transactions/{txn_id}", json={"amount": 150.0})
    assert auth_client.get(f"/api/accounts/{acc_id}").get_json()["account"]["balance"] == initial_balance - 150.0

    # 3. Delete transaction -> balance restores to initial
    auth_client.delete(f"/api/transactions/{txn_id}")
    assert auth_client.get(f"/api/accounts/{acc_id}").get_json()["account"]["balance"] == initial_balance
