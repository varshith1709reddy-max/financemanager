import datetime

def test_dashboard_summary_calculations(auth_client):
    today = datetime.date.today()
    curr_month = today.strftime("%Y-%m")
    date_str = f"{curr_month}-05"

    acc_id = auth_client.get("/api/accounts").get_json()["accounts"][0]["id"]

    # Post income of 2000
    auth_client.post("/api/transactions", json={
        "account_id": acc_id,
        "type": "income",
        "amount": 2000.0,
        "date": date_str,
        "description": "Salary Payday"
    })

    # Post expense of 500
    auth_client.post("/api/transactions", json={
        "account_id": acc_id,
        "type": "expense",
        "amount": 500.0,
        "date": date_str,
        "description": "Groceries"
    })

    dash_res = auth_client.get("/api/dashboard/summary")
    assert dash_res.status_code == 200
    data = dash_res.get_json()

    metrics = data["metrics"]
    assert metrics["this_month_income"] == 2000.0
    assert metrics["this_month_expense"] == 500.0
    assert metrics["this_month_net"] == 1500.0
    # savings_rate = (1500 / 2000) * 100 = 75.0%
    assert metrics["savings_rate"] == 75.0
    assert metrics["net_worth"] == 1500.0

    assert len(data["recent_transactions"]) == 2
    assert len(data["monthly_trends"]) == 6

def test_reports_cash_flow_and_spending(auth_client):
    today = datetime.date.today()
    curr_month = today.strftime("%Y-%m")
    date_str = f"{curr_month}-08"

    acc_id = auth_client.get("/api/accounts").get_json()["accounts"][0]["id"]
    categories = auth_client.get("/api/categories?type=expense").get_json()["categories"]
    cat_id = categories[0]["id"]

    auth_client.post("/api/transactions", json={
        "account_id": acc_id,
        "type": "income",
        "amount": 1000.0,
        "date": date_str,
        "description": "Bonus"
    })
    auth_client.post("/api/transactions", json={
        "account_id": acc_id,
        "category_id": cat_id,
        "type": "expense",
        "amount": 400.0,
        "date": date_str,
        "description": "Supplies"
    })

    # 1. Cash flow report
    cf_res = auth_client.get("/api/reports/cash-flow")
    assert cf_res.status_code == 200
    cf_data = cf_res.get_json()
    assert cf_data["summary"]["total_income"] >= 1000.0
    assert cf_data["summary"]["total_expense"] >= 400.0

    # 2. Category spending report
    spend_res = auth_client.get(f"/api/reports/spending?start_date={curr_month}-01&end_date={curr_month}-28")
    assert spend_res.status_code == 200
    spend_data = spend_res.get_json()
    assert spend_data["total_spending"] >= 400.0
    assert any(c["id"] == cat_id for c in spend_data["categories"])

def test_export_csv(auth_client):
    acc_id = auth_client.get("/api/accounts").get_json()["accounts"][0]["id"]
    auth_client.post("/api/transactions", json={
        "account_id": acc_id,
        "type": "income",
        "amount": 750.0,
        "date": "2026-10-01",
        "description": "Direct Deposit"
    })

    res = auth_client.get("/api/reports/export")
    assert res.status_code == 200
    assert "text/csv" in res.content_type
    csv_text = res.get_data(as_text=True)
    assert "Date,Type,Account" in csv_text
    assert "Direct Deposit" in csv_text
    assert "750.00" in csv_text
