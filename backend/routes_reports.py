import io
import csv
import datetime
from flask import Blueprint, request, jsonify, Response, g
from backend.database import get_db
from backend.auth import login_required

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")

@reports_bp.route("/cash-flow", methods=["GET"])
@login_required
def cash_flow_report():
    today = datetime.date.today()
    default_start = (today - datetime.timedelta(days=365)).strftime("%Y-%m-01")
    default_end = today.strftime("%Y-%m-%d")

    start_date = request.args.get("start_date", default_start)
    end_date = request.args.get("end_date", default_end)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', date) as month,
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as expense,
                COUNT(id) as transaction_count
            FROM transactions
            WHERE user_id = ? AND date >= ? AND date <= ?
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month ASC;
        """, (g.user_id, start_date, end_date))
        rows = cursor.fetchall()

    data = []
    total_income = 0.0
    total_expense = 0.0

    for r in rows:
        inc = round(float(r["income"] or 0.0), 2)
        exp = round(float(r["expense"] or 0.0), 2)
        net = round(inc - exp, 2)
        rate = round((net / inc) * 100, 1) if inc > 0 else 0.0
        data.append({
            "month": r["month"],
            "income": inc,
            "expense": exp,
            "net": net,
            "savings_rate": max(0.0, rate),
            "transaction_count": r["transaction_count"]
        })
        total_income += inc
        total_expense += exp

    total_net = round(total_income - total_expense, 2)
    overall_rate = round((total_net / total_income) * 100, 1) if total_income > 0 else 0.0
    month_count = len(data) or 1

    return jsonify({
        "data": data,
        "summary": {
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "total_net": total_net,
            "overall_savings_rate": max(0.0, overall_rate),
            "avg_monthly_income": round(total_income / month_count, 2),
            "avg_monthly_expense": round(total_expense / month_count, 2)
        }
    }), 200

@reports_bp.route("/spending", methods=["GET"])
@login_required
def spending_report():
    today = datetime.date.today()
    default_start = today.replace(day=1).strftime("%Y-%m-%d")
    default_end = today.strftime("%Y-%m-%d")

    start_date = request.args.get("start_date", default_start)
    end_date = request.args.get("end_date", default_end)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.name, c.color, c.icon,
                   ROUND(SUM(t.amount), 2) as total_amount,
                   COUNT(t.id) as count
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = ? AND t.type = 'expense' AND t.date >= ? AND t.date <= ?
            GROUP BY c.id, c.name, c.color, c.icon
            ORDER BY total_amount DESC;
        """, (g.user_id, start_date, end_date))
        categories = cursor.fetchall()

    total_spending = sum(float(c["total_amount"]) for c in categories)
    for c in categories:
        c["percentage"] = round((float(c["total_amount"]) / total_spending) * 100, 1) if total_spending > 0 else 0.0

    return jsonify({
        "start_date": start_date,
        "end_date": end_date,
        "total_spending": round(total_spending, 2),
        "categories": categories
    }), 200

@reports_bp.route("/income", methods=["GET"])
@login_required
def income_report():
    today = datetime.date.today()
    default_start = today.replace(day=1).strftime("%Y-%m-%d")
    default_end = today.strftime("%Y-%m-%d")

    start_date = request.args.get("start_date", default_start)
    end_date = request.args.get("end_date", default_end)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.name, c.color, c.icon,
                   ROUND(SUM(t.amount), 2) as total_amount,
                   COUNT(t.id) as count
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = ? AND t.type = 'income' AND t.date >= ? AND t.date <= ?
            GROUP BY c.id, c.name, c.color, c.icon
            ORDER BY total_amount DESC;
        """, (g.user_id, start_date, end_date))
        sources = cursor.fetchall()

    total_income = sum(float(s["total_amount"]) for s in sources)
    for s in sources:
        if not s["name"]:
            s["name"] = "Uncategorized Income"
            s["color"] = "#10B981"
            s["icon"] = "cash"
        s["percentage"] = round((float(s["total_amount"]) / total_income) * 100, 1) if total_income > 0 else 0.0

    return jsonify({
        "start_date": start_date,
        "end_date": end_date,
        "total_income": round(total_income, 2),
        "sources": sources
    }), 200

@reports_bp.route("/export", methods=["GET"])
@login_required
def export_csv():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = """
        SELECT t.date, t.type, src.name as account_name, dst.name as to_account_name,
               c.name as category_name, t.amount, t.description, t.notes, t.tags
        FROM transactions t
        LEFT JOIN accounts src ON t.account_id = src.id
        LEFT JOIN accounts dst ON t.to_account_id = dst.id
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = ?
    """
    params = [g.user_id]
    if start_date:
        query += " AND t.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND t.date <= ?"
        params.append(end_date)
    query += " ORDER BY t.date DESC, t.id DESC;"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Account", "To Account", "Category", "Amount", "Description", "Notes", "Tags"])

    for r in rows:
        writer.writerow([
            r["date"],
            r["type"].capitalize(),
            r["account_name"] or "",
            r["to_account_name"] or "",
            r["category_name"] or "",
            f"{float(r['amount']):.2f}",
            r["description"] or "",
            r["notes"] or "",
            r["tags"] or ""
        ])

    csv_data = output.getvalue()
    filename = f"finance_transactions_{datetime.date.today().isoformat()}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
