import datetime
from flask import Blueprint, request, jsonify, g
from backend.database import get_db
from backend.auth import login_required

budgets_bp = Blueprint("budgets", __name__, url_prefix="/api/budgets")

@budgets_bp.route("", methods=["GET"])
@login_required
def list_budgets():
    # Month format YYYY-MM
    current_month = datetime.date.today().strftime("%Y-%m")
    month = request.args.get("month", default=current_month, type=str)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.*, c.name as category_name, c.color as category_color, c.icon as category_icon
            FROM budgets b
            JOIN categories c ON b.category_id = c.id
            WHERE b.user_id = ? AND (b.month = ? OR b.month IS NULL)
            ORDER BY c.name ASC;
        """, (g.user_id, month))
        raw_budgets = cursor.fetchall()

        budgets = []
        total_limit = 0.0
        total_spent = 0.0

        for b in raw_budgets:
            cat_id = b["category_id"]
            limit = float(b["amount_limit"])
            alert_threshold = float(b.get("alert_threshold") or 0.8)

            # Calculate spent in category for this month
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) as spent
                FROM transactions
                WHERE user_id = ? AND category_id = ? AND type = 'expense'
                  AND strftime('%Y-%m', date) = ?;
            """, (g.user_id, cat_id, month))
            spent = round(float(cursor.fetchone()["spent"] or 0.0), 2)

            remaining = round(max(0.0, limit - spent), 2)
            pct = round((spent / limit) * 100, 1) if limit > 0 else 0.0
            is_exceeded = spent > limit
            is_warning = (spent >= (limit * alert_threshold)) and not is_exceeded

            budgets.append({
                "id": b["id"],
                "category_id": cat_id,
                "category_name": b["category_name"],
                "category_color": b["category_color"],
                "category_icon": b["category_icon"],
                "amount_limit": limit,
                "spent_amount": spent,
                "remaining_amount": remaining,
                "percentage_spent": pct,
                "is_warning": is_warning,
                "is_exceeded": is_exceeded,
                "month": b["month"],
                "alert_threshold": alert_threshold,
                "created_at": b["created_at"]
            })

            total_limit += limit
            total_spent += spent

    total_remaining = round(max(0.0, total_limit - total_spent), 2)
    overall_pct = round((total_spent / total_limit) * 100, 1) if total_limit > 0 else 0.0

    return jsonify({
        "month": month,
        "budgets": budgets,
        "summary": {
            "total_budgeted": round(total_limit, 2),
            "total_spent": round(total_spent, 2),
            "total_remaining": total_remaining,
            "overall_percentage": overall_pct
        }
    }), 200

@budgets_bp.route("", methods=["POST"])
@login_required
def create_or_update_budget():
    data = request.get_json(silent=True) or {}
    category_id = data.get("category_id")
    amount_limit = data.get("amount_limit")
    month = (data.get("month") or datetime.date.today().strftime("%Y-%m")).strip()
    alert_threshold = float(data.get("alert_threshold") or 0.8)

    if not category_id:
        return jsonify({"error": "Category is required"}), 400
    try:
        amount_limit = round(float(amount_limit), 2)
        if amount_limit <= 0:
            return jsonify({"error": "Budget limit must be greater than zero"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid budget limit amount"}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        # Verify category exists
        cursor.execute("SELECT id, name FROM categories WHERE id = ?;", (category_id,))
        cat = cursor.fetchone()
        if not cat:
            return jsonify({"error": "Category not found"}), 404

        # Upsert budget for user, category, and month
        cursor.execute("""
            INSERT INTO budgets (user_id, category_id, amount_limit, month, alert_threshold)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, category_id, month) DO UPDATE SET
                amount_limit = excluded.amount_limit,
                alert_threshold = excluded.alert_threshold,
                updated_at = CURRENT_TIMESTAMP;
        """, (g.user_id, category_id, amount_limit, month, alert_threshold))

        cursor.execute("""
            SELECT b.*, c.name as category_name
            FROM budgets b
            JOIN categories c ON b.category_id = c.id
            WHERE b.user_id = ? AND b.category_id = ? AND b.month = ?;
        """, (g.user_id, category_id, month))
        budget = cursor.fetchone()

    return jsonify({"message": "Budget saved successfully", "budget": budget}), 201

@budgets_bp.route("/<int:budget_id>", methods=["PUT"])
@login_required
def update_budget(budget_id: int):
    data = request.get_json(silent=True) or {}
    amount_limit = data.get("amount_limit")
    alert_threshold = data.get("alert_threshold")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budgets WHERE id = ? AND user_id = ?;", (budget_id, g.user_id))
        budget = cursor.fetchone()
        if not budget:
            return jsonify({"error": "Budget not found"}), 404

        new_limit = float(amount_limit) if amount_limit is not None else budget["amount_limit"]
        new_threshold = float(alert_threshold) if alert_threshold is not None else budget["alert_threshold"]

        if new_limit <= 0:
            return jsonify({"error": "Budget limit must be greater than zero"}), 400

        cursor.execute("""
            UPDATE budgets
            SET amount_limit = ?, alert_threshold = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (new_limit, new_threshold, budget_id))

        cursor.execute("SELECT * FROM budgets WHERE id = ?;", (budget_id,))
        updated = cursor.fetchone()

    return jsonify({"message": "Budget updated successfully", "budget": updated}), 200

@budgets_bp.route("/<int:budget_id>", methods=["DELETE"])
@login_required
def delete_budget(budget_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM budgets WHERE id = ? AND user_id = ?;", (budget_id, g.user_id))
        if not cursor.fetchone():
            return jsonify({"error": "Budget not found"}), 404
        cursor.execute("DELETE FROM budgets WHERE id = ?;", (budget_id,))

    return jsonify({"message": "Budget deleted successfully"}), 200
