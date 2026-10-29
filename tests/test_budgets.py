def test_create_and_calculate_budget(auth_client):
    acc_id = auth_client.get("/api/accounts").get_json()["accounts"][0]["id"]
    categories = auth_client.get("/api/categories?type=expense").get_json()["categories"]
    cat_id = categories[0]["id"]

    # 1. Set budget limit of 200 for month 2026-10 with 80% threshold
    budget_res = auth_client.post("/api/budgets", json={
        "category_id": cat_id,
        "amount_limit": 200.0,
        "month": "2026-10",
        "alert_threshold": 0.8
    })
    assert budget_res.status_code == 201

    # Initially spent should be 0
    res = auth_client.get("/api/budgets?month=2026-10").get_json()
    b = next(item for item in res["budgets"] if item["category_id"] == cat_id)
    assert b["spent_amount"] == 0.0
    assert not b["is_warning"]
    assert not b["is_exceeded"]

    # 2. Add 170 expense (85% of 200 -> should trigger warning!)
    auth_client.post("/api/transactions", json={
        "account_id": acc_id,
        "category_id": cat_id,
        "type": "expense",
        "amount": 170.0,
        "date": "2026-10-10",
        "description": "Category Expense"
    })

    res = auth_client.get("/api/budgets?month=2026-10").get_json()
    b = next(item for item in res["budgets"] if item["category_id"] == cat_id)
    assert b["spent_amount"] == 170.0
    assert b["is_warning"] is True
    assert b["is_exceeded"] is False

    # 3. Add another 50 expense (total 220 > 200 limit -> should be exceeded!)
    auth_client.post("/api/transactions", json={
        "account_id": acc_id,
        "category_id": cat_id,
        "type": "expense",
        "amount": 50.0,
        "date": "2026-10-15",
        "description": "Over limit expense"
    })

    res = auth_client.get("/api/budgets?month=2026-10").get_json()
    b = next(item for item in res["budgets"] if item["category_id"] == cat_id)
    assert b["spent_amount"] == 220.0
    assert b["is_exceeded"] is True

def test_delete_budget(auth_client):
    categories = auth_client.get("/api/categories?type=expense").get_json()["categories"]
    cat_id = categories[1]["id"]

    create_res = auth_client.post("/api/budgets", json={
        "category_id": cat_id,
        "amount_limit": 500.0,
        "month": "2026-10"
    })
    b_id = create_res.get_json()["budget"]["id"]

    del_res = auth_client.delete(f"/api/budgets/{b_id}")
    assert del_res.status_code == 200

    list_res = auth_client.get("/api/budgets?month=2026-10").get_json()
    assert all(b["id"] != b_id for b in list_res["budgets"])
