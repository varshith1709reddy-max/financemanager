import datetime
from flask import Blueprint, jsonify, g
from backend.database import get_db
from backend.auth import login_required
from backend.routes_accounts import recalculate_account_balance

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

@dashboard_bp.route("/summary", methods=["GET"])
@login_required
def get_dashboard_summary():
    today = datetime.date.today()
    current_month_str = today.strftime("%Y-%m")

    # Calculate last month string
    first_of_this_month = today.replace(day=1)
    last_month_date = first_of_this_month - datetime.timedelta(days=1)
    last_month_str = last_month_date.strftime("%Y-%m")

    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Accounts & Net worth
        cursor.execute("SELECT id FROM accounts WHERE user_id = ? AND is_active = 1;", (g.user_id,))
        acc_ids = [r["id"] for r in cursor.fetchall()]
        for aid in acc_ids:
            recalculate_account_balance(cursor, aid)

        cursor.execute("SELECT * FROM accounts WHERE user_id = ? AND is_active = 1;", (g.user_id,))
        accounts = cursor.fetchall()

        total_assets = 0.0
        total_liabilities = 0.0

        for acc in accounts:
            bal = float(acc["balance"] or 0.0)
            if acc["type"] == "credit_card":
                # In personal finance, if credit card is positive, it's typically current balance owed
                total_liabilities += max(0.0, bal)
            else:
                total_assets += bal

        net_worth = round(total_assets - total_liabilities, 2)

        # 2. This month income and expense
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as expense
            FROM transactions
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?;
        """, (g.user_id, current_month_str))
        curr_row = cursor.fetchone()
        this_month_income = round(float(curr_row["income"] or 0.0), 2)
        this_month_expense = round(float(curr_row["expense"] or 0.0), 2)
        this_month_net = round(this_month_income - this_month_expense, 2)

        savings_rate = 0.0
        if this_month_income > 0:
            savings_rate = round(max(0.0, ((this_month_income - this_month_expense) / this_month_income) * 100), 1)

        # 3. Last month income and expense for MoM comparison
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as expense
            FROM transactions
            WHERE user_id = ? AND strftime('%Y-%m', date) = ?;
        """, (g.user_id, last_month_str))
        prev_row = cursor.fetchone()
        last_month_income = round(float(prev_row["income"] or 0.0), 2)
        last_month_expense = round(float(prev_row["expense"] or 0.0), 2)

        income_change_pct = None
        if last_month_income > 0:
            income_change_pct = round(((this_month_income - last_month_income) / last_month_income) * 100, 1)

        expense_change_pct = None
        if last_month_expense > 0:
            expense_change_pct = round(((this_month_expense - last_month_expense) / last_month_expense) * 100, 1)

        # 4. Spending by category for current month
        cursor.execute("""
            SELECT c.id, c.name, c.color, c.icon,
                   ROUND(SUM(t.amount), 2) as amount,
                   COUNT(t.id) as count
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = ? AND t.type = 'expense' AND strftime('%Y-%m', t.date) = ?
            GROUP BY c.id, c.name, c.color, c.icon
            ORDER BY amount DESC;
        """, (g.user_id, current_month_str))
        category_breakdown = cursor.fetchall()
        for cat in category_breakdown:
            cat["percentage"] = round((cat["amount"] / this_month_expense) * 100, 1) if this_month_expense > 0 else 0.0

        # 5. Monthly trends (last 6 months)
        trends = []
        for i in range(5, -1, -1):
            # Compute month offset
            # Month arithmetic
            year = today.year
            month_num = today.month - i
            while month_num <= 0:
                month_num += 12
                year -= 1
            m_str = f"{year:04d}-{month_num:02d}"

            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as income,
                    COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as expense
                FROM transactions
                WHERE user_id = ? AND strftime('%Y-%m', date) = ?;
            """, (g.user_id, m_str))
            m_row = cursor.fetchone()
            inc = round(float(m_row["income"] or 0.0), 2)
            exp = round(float(m_row["expense"] or 0.0), 2)
            trends.append({
                "month": m_str,
                "label": datetime.date(year, month_num, 1).strftime("%b %Y"),
                "income": inc,
                "expense": exp,
                "net": round(inc - exp, 2)
            })

        # 6. Recent transactions (latest 8)
        cursor.execute("""
            SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon,
                   src.name as account_name, dst.name as to_account_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN accounts src ON t.account_id = src.id
            LEFT JOIN accounts dst ON t.to_account_id = dst.id
            WHERE t.user_id = ?
            ORDER BY t.date DESC, t.id DESC
            LIMIT 8;
        """, (g.user_id,))
        recent_transactions = cursor.fetchall()

        # 7. Budget alerts (active budgets near or over threshold)
        cursor.execute("""
            SELECT b.*, c.name as category_name, c.color as category_color
            FROM budgets b
            JOIN categories c ON b.category_id = c.id
            WHERE b.user_id = ? AND (b.month = ? OR b.month IS NULL);
        """, (g.user_id, current_month_str))
        user_budgets = cursor.fetchall()
        budget_alerts = []
        for b in user_budgets:
            limit = float(b["amount_limit"])
            threshold = float(b.get("alert_threshold") or 0.8)
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) as spent
                FROM transactions
                WHERE user_id = ? AND category_id = ? AND type = 'expense'
                  AND strftime('%Y-%m', date) = ?;
            """, (g.user_id, b["category_id"], current_month_str))
            spent = round(float(cursor.fetchone()["spent"] or 0.0), 2)
            pct = round((spent / limit) * 100, 1) if limit > 0 else 0.0
            if spent >= (limit * threshold):
                budget_alerts.append({
                    "category_id": b["category_id"],
                    "category_name": b["category_name"],
                    "amount_limit": limit,
                    "spent_amount": spent,
                    "percentage_spent": pct,
                    "is_exceeded": spent > limit
                })

        # 8. Top savings goals
        cursor.execute("""
            SELECT * FROM savings_goals
            WHERE user_id = ?
            ORDER BY is_completed ASC, current_amount / target_amount DESC
            LIMIT 4;
        """, (g.user_id,))
        top_goals_raw = cursor.fetchall()
        top_goals = []
        for g_row in top_goals_raw:
            tgt = float(g_row["target_amount"])
            cur = float(g_row["current_amount"])
            pct = round(min(100.0, (cur / tgt) * 100), 1) if tgt > 0 else 100.0
            top_goals.append({
                "id": g_row["id"],
                "name": g_row["name"],
                "target_amount": tgt,
                "current_amount": cur,
                "percentage": pct,
                "color": g_row["color"],
                "is_completed": bool(g_row["is_completed"])
            })

    return jsonify({
        "metrics": {
            "net_worth": net_worth,
            "total_assets": round(total_assets, 2),
            "total_liabilities": round(total_liabilities, 2),
            "this_month_income": this_month_income,
            "this_month_expense": this_month_expense,
            "this_month_net": this_month_net,
            "savings_rate": savings_rate,
            "income_change_pct": income_change_pct,
            "expense_change_pct": expense_change_pct,
            "current_month": current_month_str
        },
        "accounts": accounts,
        "category_breakdown": category_breakdown,
        "monthly_trends": trends,
        "recent_transactions": recent_transactions,
        "budget_alerts": budget_alerts,
        "top_goals": top_goals
    }), 200
