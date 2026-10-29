import urllib.request
import urllib.parse
import json
import time
import subprocess
import sys
import os

BASE_URL = "http://127.0.0.1:5005"

def run_live_verification():
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    env["PORT"] = "5005"
    env["DATABASE_PATH"] = os.path.join(project_dir, "data", "test_live.db")

    # Start server process
    proc = subprocess.Popen([sys.executable, os.path.join(project_dir, "app.py")], env=env)
    time.sleep(2.5)

    try:
        # 1. Health check
        with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert data["status"] == "healthy"
            print("[OK] Health Check Passed")

        # 2. Frontend HTML delivery
        with urllib.request.urlopen(f"{BASE_URL}/", timeout=5) as resp:
            assert resp.status == 200
            html = resp.read().decode()
            assert "Finance Manager" in html
            print("[OK] Index HTML Delivery Passed")

        # 3. Static assets delivery (CSS & JS)
        with urllib.request.urlopen(f"{BASE_URL}/static/css/styles.css", timeout=5) as resp:
            assert resp.status == 200
            assert "var(--primary)" in resp.read().decode()
            print("[OK] Static CSS Delivery Passed")

        with urllib.request.urlopen(f"{BASE_URL}/static/js/app.js", timeout=5) as resp:
            assert resp.status == 200
            assert "App =" in resp.read().decode()
            print("[OK] Static JS Delivery Passed")

        # 4. Demo Seed
        req = urllib.request.Request(f"{BASE_URL}/api/demo/seed", data=b"{}", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            demo_data = json.loads(resp.read().decode())
            token = demo_data["token"]
            assert demo_data["user"]["full_name"] == "Rahul Sharma (Student)"
            print("[OK] Demo Seed Passed")

        auth_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # 5. Dashboard Calculations
        req = urllib.request.Request(f"{BASE_URL}/api/dashboard/summary", headers=auth_headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            dash = json.loads(resp.read().decode())
            metrics = dash["metrics"]
            assert metrics["net_worth"] > 0
            assert metrics["this_month_income"] > 0
            assert metrics["this_month_expense"] > 0
            assert len(dash["accounts"]) >= 3
            assert len(dash["category_breakdown"]) >= 3
            assert len(dash["monthly_trends"]) == 6
            print(f"[OK] Dashboard Calculations Verified: Net Worth=Rs {metrics['net_worth']}, Savings Rate={metrics['savings_rate']}%")

        # 6. Accounts List & CRUD
        req = urllib.request.Request(f"{BASE_URL}/api/accounts", headers=auth_headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            accounts = json.loads(resp.read().decode())["accounts"]
            assert len(accounts) >= 3
            chk_acc = next(a for a in accounts if a["type"] == "checking")
            sav_acc = next(a for a in accounts if a["type"] == "savings")
            print("[OK] Accounts Verified")

        # 7. Create New Account
        new_acc_payload = json.dumps({"name": "Travel Fund", "type": "savings", "initial_balance": 1500.0}).encode()
        req = urllib.request.Request(f"{BASE_URL}/api/accounts", data=new_acc_payload, headers=auth_headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 201
            new_acc = json.loads(resp.read().decode())["account"]
            assert new_acc["balance"] == 1500.0
            print("[OK] Account Creation Verified")

        # 8. Transfer Funds
        transfer_payload = json.dumps({
            "from_account_id": chk_acc["id"],
            "to_account_id": sav_acc["id"],
            "amount": 250.0,
            "date": "2026-10-25",
            "description": "Weekly Auto-Save"
        }).encode()
        req = urllib.request.Request(f"{BASE_URL}/api/transactions/transfer", data=transfer_payload, headers=auth_headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 201
            print("[OK] Transfer Flow Verified")

        # 9. Budgets
        req = urllib.request.Request(f"{BASE_URL}/api/budgets", headers=auth_headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            budgets_data = json.loads(resp.read().decode())
            assert len(budgets_data["budgets"]) > 0
            assert budgets_data["summary"]["total_budgeted"] > 0
            print(f"[OK] Budgets Verified: {len(budgets_data['budgets'])} category budgets active")

        # 10. Savings Goals & Contribution
        req = urllib.request.Request(f"{BASE_URL}/api/goals", headers=auth_headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            goals = json.loads(resp.read().decode())["goals"]
            assert len(goals) > 0
            first_goal = goals[0]
            print(f"[OK] Savings Goals Verified: {len(goals)} goals tracked")

        # Contribute to goal
        contrib_payload = json.dumps({
            "amount": 100.0,
            "date": "2026-10-25",
            "account_id": chk_acc["id"],
            "notes": "Verified test deposit"
        }).encode()
        req = urllib.request.Request(f"{BASE_URL}/api/goals/{first_goal['id']}/contribute", data=contrib_payload, headers=auth_headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            updated_goal = json.loads(resp.read().decode())["goal"]
            assert updated_goal["current_amount"] == first_goal["current_amount"] + 100.0
            print("[OK] Goal Contribution Flow Verified")

        # 11. Reports & CSV Export
        req = urllib.request.Request(f"{BASE_URL}/api/reports/cash-flow", headers=auth_headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            cf = json.loads(resp.read().decode())
            assert "total_income" in cf["summary"]
            print("[OK] Cash Flow Analytics Verified")

        req = urllib.request.Request(f"{BASE_URL}/api/reports/export", headers=auth_headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            csv_content = resp.read().decode()
            assert "Date,Type,Account" in csv_content
            print("[OK] CSV Export Verified")

        print("\n[SUCCESS] ALL LIVE SERVER END-TO-END FLOWS VERIFIED SUCCESSFULLY!")

    finally:
        proc.terminate()
        proc.wait()
        # Clean up test live db
        db_file = os.path.join(project_dir, "data", "test_live.db")
        for ext in ["", "-wal", "-shm"]:
            f = db_file + ext
            if os.path.exists(f):
                try: os.remove(f)
                except: pass

if __name__ == "__main__":
    run_live_verification()
