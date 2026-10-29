import sqlite3
import datetime
import os

def seed_varshith_data():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "finance.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    user_id = 2
    today = datetime.date.today()
    cur_month = today.strftime("%Y-%m")
    first_this = today.replace(day=1)
    prev_month_date = first_this - datetime.timedelta(days=1)
    prev_month = prev_month_date.strftime("%Y-%m")

    # 1. Fetch categories
    cur.execute("SELECT id, name, type FROM categories WHERE user_id IS NULL OR user_id = ?", (user_id,))
    cats = {c["name"]: c["id"] for c in cur.fetchall()}

    # 2. Accounts
    cur.execute("SELECT id, name, type FROM accounts WHERE user_id = ?", (user_id,))
    existing_accs = {a["name"]: a["id"] for a in cur.fetchall()}

    acc_defs = [
        ("Main Checking", "checking", 35000.0, "4144"),
        ("Emergency Savings", "savings", 50000.0, "8812"),
        ("HDFC Regalia Credit Card", "credit_card", 7250.0, "9021"),
        ("Zerodha Investment Portfolio", "investment", 125000.0, "ZER-552"),
        ("Cash & UPI Wallet", "cash", 3500.0, "UPI-01")
    ]

    for name, atype, init_b, num in acc_defs:
        if name not in existing_accs:
            cur.execute("""
                INSERT INTO accounts (user_id, name, type, balance, initial_balance, currency, account_number)
                VALUES (?, ?, ?, ?, ?, 'INR', ?);
            """, (user_id, name, atype, init_b, init_b, num))
            existing_accs[name] = cur.lastrowid
        else:
            cur.execute("UPDATE accounts SET initial_balance = ? WHERE id = ?", (init_b, existing_accs[name]))

    chk_id = existing_accs["Main Checking"]
    sav_id = existing_accs["Emergency Savings"]
    cc_id = existing_accs.get("HDFC Regalia Credit Card")
    inv_id = existing_accs.get("Zerodha Investment Portfolio")
    cash_id = existing_accs.get("Cash & UPI Wallet")

    # 3. Add transactions for user 2 if none exist
    cur.execute("SELECT count(*) as count FROM transactions WHERE user_id = ?", (user_id,))
    if cur.fetchone()["count"] == 0:
        txns = [
            # Income - This month
            (chk_id, None, cats.get("Salary"), "income", 85000.0, f"{cur_month}-01", "Monthly Tech Salary", "Direct bank deposit", "salary"),
            (chk_id, None, cats.get("Freelance & Side Hustles"), "income", 18500.0, f"{cur_month}-10", "Fullstack App Consulting", "Client milestone payout", "freelance"),
            (sav_id, None, cats.get("Investments & Dividends"), "income", 1450.0, f"{cur_month}-15", "Quarterly Dividend Yield", "Direct credited to savings", "dividend"),
            
            # Expenses - This month
            (chk_id, None, cats.get("Housing & Rent"), "expense", 22000.0, f"{cur_month}-01", "Apartment Rent", "Monthly rent transfer to landlord", "rent,fixed"),
            (chk_id, None, cats.get("Utilities & Bills"), "expense", 2850.0, f"{cur_month}-03", "Electricity & Water Bill", "Bescom electricity bill", "utility"),
            (chk_id, None, cats.get("Utilities & Bills"), "expense", 999.0, f"{cur_month}-04", "Airtel Fiber Broadband", "100 Mbps Unlimited WiFi", "internet"),
            (cc_id, None, cats.get("Groceries"), "expense", 5420.0, f"{cur_month}-02", "Zepto & Blinkit Groceries", "Weekly organic vegetables & dairy", "groceries"),
            (cc_id, None, cats.get("Groceries"), "expense", 4180.0, f"{cur_month}-11", "Nature Basket Supermarket", "Household staples restock", "groceries"),
            (cc_id, None, cats.get("Groceries"), "expense", 3250.0, f"{cur_month}-18", "Farmers Fresh Mart", "Fruits & nuts", "groceries"),
            (cc_id, None, cats.get("Food & Dining"), "expense", 1850.0, f"{cur_month}-05", "Dinner at Olive Bistro", "Weekend team dinner", "dining"),
            (cc_id, None, cats.get("Food & Dining"), "expense", 850.0, f"{cur_month}-09", "Swiggy Gourmet Order", "Healthy salads and lunch", "swiggy"),
            (cc_id, None, cats.get("Food & Dining"), "expense", 420.0, f"{cur_month}-14", "Third Wave Coffee Roasters", "Cold brew & croissant", "coffee"),
            (cc_id, None, cats.get("Food & Dining"), "expense", 680.0, f"{cur_month}-21", "Zomato Pizza Delivery", "Friday movie night dinner", "zomato"),
            (cc_id, None, cats.get("Transportation"), "expense", 3200.0, f"{cur_month}-06", "Petrol Fuel Station", "Car tank fill-up", "fuel"),
            (cc_id, None, cats.get("Transportation"), "expense", 950.0, f"{cur_month}-12", "Uber Premier Rides", "Airport & downtown transit", "uber"),
            (cc_id, None, cats.get("Entertainment"), "expense", 649.0, f"{cur_month}-02", "Netflix 4K Premium", "Monthly family plan", "subscription"),
            (cc_id, None, cats.get("Entertainment"), "expense", 119.0, f"{cur_month}-08", "Spotify Premium", "Hi-Fi music streaming", "subscription"),
            (cc_id, None, cats.get("Shopping & Personal"), "expense", 4250.0, f"{cur_month}-16", "Amazon India", "Wireless noise cancelling headset", "electronics"),
            (cash_id, None, cats.get("Miscellaneous"), "expense", 450.0, f"{cur_month}-13", "Local Artisan Market", "Cash handicraft purchase", "cash"),

            # Transfers
            (chk_id, sav_id, None, "transfer", 15000.0, f"{cur_month}-05", "Auto-Transfer to Emergency Savings", "Monthly automated safety deposit", "transfer"),
            (chk_id, inv_id, None, "transfer", 20000.0, f"{cur_month}-07", "SIP Monthly Investment", "Index fund SIP investment", "investment"),
            (chk_id, cc_id, None, "transfer", 7250.0, f"{cur_month}-15", "Credit Card Statement Settlement", "Paid in full", "card-payment"),

            # Previous Month transactions
            (chk_id, None, cats.get("Salary"), "income", 85000.0, f"{prev_month}-01", "Monthly Tech Salary", "", "salary"),
            (chk_id, None, cats.get("Housing & Rent"), "expense", 22000.0, f"{prev_month}-01", "Apartment Rent", "", "rent"),
            (cc_id, None, cats.get("Groceries"), "expense", 11800.0, f"{prev_month}-10", "Supermarket monthly grocery run", "", "groceries"),
            (cc_id, None, cats.get("Food & Dining"), "expense", 4650.0, f"{prev_month}-15", "Dining out & takeout", "", "dining"),
            (cc_id, None, cats.get("Transportation"), "expense", 3800.0, f"{prev_month}-20", "Fuel & cabs", "", "transit"),
        ]

        for s_id, d_id, c_id, t_type, amt, d_str, desc, notes, tags in txns:
            cur.execute("""
                INSERT INTO transactions (user_id, account_id, to_account_id, category_id, type, amount, date, description, notes, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (user_id, s_id, d_id, c_id, t_type, amt, d_str, desc, notes, tags))

    # 4. Add Budgets for User 2
    cur.execute("SELECT count(*) as count FROM budgets WHERE user_id = ?", (user_id,))
    if cur.fetchone()["count"] == 0:
        budgets_data = [
            (cats.get("Housing & Rent"), 25000.0, 0.9),
            (cats.get("Groceries"), 16000.0, 0.8),
            (cats.get("Food & Dining"), 6000.0, 0.8),
            (cats.get("Transportation"), 5500.0, 0.8),
            (cats.get("Utilities & Bills"), 5000.0, 0.8),
            (cats.get("Entertainment"), 2500.0, 0.75),
            (cats.get("Shopping & Personal"), 8000.0, 0.8),
        ]
        for cat_id, limit, thresh in budgets_data:
            if cat_id:
                cur.execute("""
                    INSERT INTO budgets (user_id, category_id, amount_limit, month, alert_threshold)
                    VALUES (?, ?, ?, ?, ?);
                """, (user_id, cat_id, limit, cur_month, thresh))

    # 5. Add Savings Goals for User 2
    cur.execute("SELECT count(*) as count FROM savings_goals WHERE user_id = ?", (user_id,))
    if cur.fetchone()["count"] == 0:
        goals_data = [
            ("Emergency Fund (6 Months)", 250000.0, 145000.0, "2027-04-30", "#10B981", "6 months of living expenses safety cushion"),
            ("Ladakh & Spiti Road Trip", 45000.0, 32000.0, "2027-02-15", "#3B82F6", "Royal Enfield bike tour, gear and homestays"),
            ("New M4 Max MacBook Pro", 180000.0, 115000.0, "2026-12-31", "#8B5CF6", "Dev workstation upgrade"),
            ("Zerodha Long-Term Wealth Milestone", 500000.0, 185000.0, "2028-01-01", "#F59E0B", "Equity and index funds long-term compounding portfolio")
        ]
        for g_name, tgt, cur_amt, dt, clr, note in goals_data:
            comp = 1 if cur_amt >= tgt else 0
            cur.execute("""
                INSERT INTO savings_goals (user_id, name, target_amount, current_amount, target_date, color, notes, is_completed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (user_id, g_name, tgt, cur_amt, dt, clr, note, comp))

    # 6. Recalculate balances for all User 2 accounts
    cur.execute("SELECT id, initial_balance FROM accounts WHERE user_id = ?", (user_id,))
    for acc in cur.fetchall():
        aid = acc["id"]
        init_b = float(acc["initial_balance"] or 0.0)

        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE account_id = ? AND type = 'income'", (aid,))
        inc = cur.fetchone()[0]

        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE account_id = ? AND type = 'expense'", (aid,))
        exp = cur.fetchone()[0]

        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE account_id = ? AND type = 'transfer'", (aid,))
        xfer_out = cur.fetchone()[0]

        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE to_account_id = ? AND type = 'transfer'", (aid,))
        xfer_in = cur.fetchone()[0]

        bal = round(init_b + inc - exp - xfer_out + xfer_in, 2)
        cur.execute("UPDATE accounts SET balance = ? WHERE id = ?", (bal, aid))

    conn.commit()
    conn.close()
    print("SUCCESS: Populated Varshith Reddy (user_id=2) with complete personal finance dataset!")

if __name__ == "__main__":
    seed_varshith_data()
