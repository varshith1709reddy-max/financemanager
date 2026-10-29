def test_create_and_contribute_goal(auth_client):
    acc = auth_client.get("/api/accounts").get_json()["accounts"][0]
    acc_id = acc["id"]
    initial_acc_bal = acc["balance"]

    # 1. Create a goal: Vacation Fund (Target: 1000, initial: 0)
    goal_res = auth_client.post("/api/goals", json={
        "name": "Vacation Fund",
        "target_amount": 1000.0,
        "current_amount": 200.0,
        "target_date": "2026-12-31",
        "color": "#3B82F6"
    })
    assert goal_res.status_code == 201
    goal = goal_res.get_json()["goal"]
    goal_id = goal["id"]
    assert goal["is_completed"] == 0

    # 2. Check list response calculations
    goals_list = auth_client.get("/api/goals").get_json()["goals"]
    g = next(item for item in goals_list if item["id"] == goal_id)
    assert g["progress_percentage"] == 20.0
    assert g["remaining_amount"] == 800.0

    # 3. Contribute 300 with account deduction
    contrib_res = auth_client.post(f"/api/goals/{goal_id}/contribute", json={
        "amount": 300.0,
        "account_id": acc_id,
        "date": "2026-10-10",
        "notes": "Transfer from Checking"
    })
    assert contrib_res.status_code == 200

    # Verify goal updated
    updated_goal = auth_client.get(f"/api/goals/{goal_id}").get_json()["goal"]
    assert updated_goal["current_amount"] == 500.0
    assert updated_goal["is_completed"] == 0

    # Verify account balance was deducted
    acc_after = auth_client.get(f"/api/accounts/{acc_id}").get_json()["account"]["balance"]
    assert acc_after == initial_acc_bal - 300.0

    # 4. Contribute remaining 500 without account deduction to reach target
    auth_client.post(f"/api/goals/{goal_id}/contribute", json={
        "amount": 500.0,
        "date": "2026-10-15"
    })
    completed_goal = auth_client.get(f"/api/goals/{goal_id}").get_json()["goal"]
    assert completed_goal["current_amount"] == 1000.0
    assert completed_goal["is_completed"] == 1

def test_delete_goal(auth_client):
    create_res = auth_client.post("/api/goals", json={
        "name": "Temporary Milestone",
        "target_amount": 500.0
    })
    g_id = create_res.get_json()["goal"]["id"]

    del_res = auth_client.delete(f"/api/goals/{g_id}")
    assert del_res.status_code == 200
    assert auth_client.get(f"/api/goals/{g_id}").status_code == 404
