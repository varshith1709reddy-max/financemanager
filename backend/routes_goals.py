import datetime
from flask import Blueprint, request, jsonify, g
from backend.database import get_db
from backend.auth import login_required
from backend.routes_accounts import recalculate_account_balance

goals_bp = Blueprint("goals", __name__, url_prefix="/api/goals")

@goals_bp.route("", methods=["GET"])
@login_required
def list_goals():
    today = datetime.date.today()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM savings_goals
            WHERE user_id = ?
            ORDER BY is_completed ASC, target_date ASC, id DESC;
        """, (g.user_id,))
        raw_goals = cursor.fetchall()

        goals = []
        total_target = 0.0
        total_saved = 0.0

        for g_row in raw_goals:
            target = float(g_row["target_amount"])
            saved = float(g_row["current_amount"])
            pct = round(min(100.0, (saved / target) * 100), 1) if target > 0 else 100.0
            remaining = round(max(0.0, target - saved), 2)

            days_left = None
            if g_row.get("target_date"):
                try:
                    t_date = datetime.date.fromisoformat(g_row["target_date"])
                    days_left = (t_date - today).days
                except ValueError:
                    pass

            goals.append({
                "id": g_row["id"],
                "name": g_row["name"],
                "target_amount": target,
                "current_amount": saved,
                "target_date": g_row["target_date"],
                "color": g_row["color"],
                "notes": g_row["notes"],
                "is_completed": bool(g_row["is_completed"]),
                "progress_percentage": pct,
                "remaining_amount": remaining,
                "days_left": days_left,
                "created_at": g_row["created_at"]
            })
            total_target += target
            total_saved += saved

    overall_pct = round((total_saved / total_target) * 100, 1) if total_target > 0 else 0.0

    return jsonify({
        "goals": goals,
        "summary": {
            "total_goals": len(goals),
            "completed_goals": sum(1 for g_item in goals if g_item["is_completed"]),
            "total_target": round(total_target, 2),
            "total_saved": round(total_saved, 2),
            "overall_percentage": overall_pct
        }
    }), 200

@goals_bp.route("", methods=["POST"])
@login_required
def create_goal():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    target_amount = data.get("target_amount")
    current_amount = float(data.get("current_amount") or 0.0)
    target_date = (data.get("target_date") or "").strip() or None
    color = (data.get("color") or "#10B981").strip()
    notes = (data.get("notes") or "").strip()

    if not name:
        return jsonify({"error": "Goal name is required"}), 400
    try:
        target_amount = round(float(target_amount), 2)
        if target_amount <= 0:
            return jsonify({"error": "Target amount must be greater than zero"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid target amount"}), 400

    is_completed = 1 if current_amount >= target_amount else 0

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO savings_goals (user_id, name, target_amount, current_amount, target_date, color, notes, is_completed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (g.user_id, name, target_amount, current_amount, target_date, color, notes, is_completed))
        goal_id = cursor.lastrowid
        cursor.execute("SELECT * FROM savings_goals WHERE id = ?;", (goal_id,))
        new_goal = cursor.fetchone()

    return jsonify({"message": "Savings goal created successfully", "goal": new_goal}), 201

@goals_bp.route("/<int:goal_id>", methods=["GET"])
@login_required
def get_goal(goal_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM savings_goals WHERE id = ? AND user_id = ?;", (goal_id, g.user_id))
        goal = cursor.fetchone()
        if not goal:
            return jsonify({"error": "Goal not found"}), 404

        cursor.execute("""
            SELECT gc.*, a.name as account_name
            FROM goal_contributions gc
            LEFT JOIN accounts a ON gc.account_id = a.id
            WHERE gc.goal_id = ?
            ORDER BY gc.date DESC, gc.id DESC;
        """, (goal_id,))
        contributions = cursor.fetchall()

    return jsonify({"goal": goal, "contributions": contributions}), 200

@goals_bp.route("/<int:goal_id>", methods=["PUT"])
@login_required
def update_goal(goal_id: int):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM savings_goals WHERE id = ? AND user_id = ?;", (goal_id, g.user_id))
        goal = cursor.fetchone()
        if not goal:
            return jsonify({"error": "Goal not found"}), 404

        name = data.get("name", goal["name"]).strip()
        target_amount = float(data.get("target_amount", goal["target_amount"]))
        current_amount = float(data.get("current_amount", goal["current_amount"]))
        target_date = data.get("target_date", goal["target_date"])
        color = data.get("color", goal["color"])
        notes = data.get("notes", goal["notes"])
        is_completed = 1 if current_amount >= target_amount else int(data.get("is_completed", goal["is_completed"]))

        cursor.execute("""
            UPDATE savings_goals
            SET name = ?, target_amount = ?, current_amount = ?, target_date = ?,
                color = ?, notes = ?, is_completed = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (name, target_amount, current_amount, target_date, color, notes, is_completed, goal_id))

        cursor.execute("SELECT * FROM savings_goals WHERE id = ?;", (goal_id,))
        updated = cursor.fetchone()

    return jsonify({"message": "Goal updated successfully", "goal": updated}), 200

@goals_bp.route("/<int:goal_id>/contribute", methods=["POST"])
@login_required
def contribute_to_goal(goal_id: int):
    data = request.get_json(silent=True) or {}
    amount = data.get("amount")
    account_id = data.get("account_id")
    date_val = (data.get("date") or datetime.date.today().isoformat()).strip()
    notes = (data.get("notes") or "").strip()

    try:
        amount = round(float(amount), 2)
        if amount <= 0:
            return jsonify({"error": "Contribution amount must be greater than zero"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid contribution amount"}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM savings_goals WHERE id = ? AND user_id = ?;", (goal_id, g.user_id))
        goal = cursor.fetchone()
        if not goal:
            return jsonify({"error": "Savings goal not found"}), 404

        # If an account is provided, record an expense transaction or deduction
        if account_id:
            cursor.execute("SELECT id, name FROM accounts WHERE id = ? AND user_id = ?;", (account_id, g.user_id))
            acc = cursor.fetchone()
            if not acc:
                return jsonify({"error": "Account not found"}), 404

            # Create transaction for the contribution
            desc = f"Contribution to goal: {goal['name']}"
            cursor.execute("""
                INSERT INTO transactions (user_id, account_id, type, amount, date, description, notes, tags)
                VALUES (?, ?, 'expense', ?, ?, ?, ?, 'goal-savings');
            """, (g.user_id, account_id, amount, date_val, desc, notes))
            recalculate_account_balance(cursor, account_id)

        # Record goal contribution
        cursor.execute("""
            INSERT INTO goal_contributions (goal_id, user_id, account_id, amount, date, notes)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (goal_id, g.user_id, account_id, amount, date_val, notes))

        # Update goal current amount
        new_saved = round(float(goal["current_amount"]) + amount, 2)
        target = float(goal["target_amount"])
        is_completed = 1 if new_saved >= target else 0

        cursor.execute("""
            UPDATE savings_goals
            SET current_amount = ?, is_completed = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (new_saved, is_completed, goal_id))

        cursor.execute("SELECT * FROM savings_goals WHERE id = ?;", (goal_id,))
        updated_goal = cursor.fetchone()

    return jsonify({
        "message": "Contribution recorded successfully",
        "goal": updated_goal,
        "amount_contributed": amount
    }), 200

@goals_bp.route("/<int:goal_id>", methods=["DELETE"])
@login_required
def delete_goal(goal_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM savings_goals WHERE id = ? AND user_id = ?;", (goal_id, g.user_id))
        if not cursor.fetchone():
            return jsonify({"error": "Goal not found"}), 404
        cursor.execute("DELETE FROM savings_goals WHERE id = ?;", (goal_id,))

    return jsonify({"message": "Goal deleted successfully"}), 200
