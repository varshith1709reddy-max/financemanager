from flask import Blueprint, request, jsonify, g
from backend.database import get_db
from backend.auth import login_required
from backend.routes_accounts import recalculate_account_balance

transactions_bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")

@transactions_bp.route("", methods=["GET"])
@login_required
def list_transactions():
    account_id = request.args.get("account_id", type=int)
    category_id = request.args.get("category_id", type=int)
    txn_type = request.args.get("type", type=str)
    start_date = request.args.get("start_date", type=str)
    end_date = request.args.get("end_date", type=str)
    search = request.args.get("search", type=str)
    page = max(1, request.args.get("page", default=1, type=int))
    limit = max(1, min(100, request.args.get("limit", default=25, type=int)))
    sort_by = request.args.get("sort_by", default="date", type=str)
    sort_order = request.args.get("sort_order", default="desc", type=str).upper()

    if sort_by not in ["date", "amount", "description", "id"]:
        sort_by = "date"
    if sort_order not in ["ASC", "DESC"]:
        sort_order = "DESC"

    query_conditions = ["t.user_id = ?"]
    params = [g.user_id]

    if account_id:
        query_conditions.append("(t.account_id = ? OR t.to_account_id = ?)")
        params.extend([account_id, account_id])
    if category_id:
        query_conditions.append("t.category_id = ?")
        params.append(category_id)
    if txn_type:
        query_conditions.append("t.type = ?")
        params.append(txn_type.lower())
    if start_date:
        query_conditions.append("t.date >= ?")
        params.append(start_date)
    if end_date:
        query_conditions.append("t.date <= ?")
        params.append(end_date)
    if search:
        query_conditions.append("(t.description LIKE ? OR t.notes LIKE ? OR t.tags LIKE ?)")
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern, search_pattern])

    where_clause = " WHERE " + " AND ".join(query_conditions)

    with get_db() as conn:
        cursor = conn.cursor()

        # Count total matching rows
        count_query = f"SELECT COUNT(*) as total FROM transactions t {where_clause};"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()["total"]

        # Fetch paginated rows with joined account and category details
        offset = (page - 1) * limit
        data_query = f"""
            SELECT t.*,
                   c.name as category_name, c.color as category_color, c.icon as category_icon,
                   src.name as account_name, src.type as account_type,
                   dst.name as to_account_name, dst.type as to_account_type
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN accounts src ON t.account_id = src.id
            LEFT JOIN accounts dst ON t.to_account_id = dst.id
            {where_clause}
            ORDER BY t.{sort_by} {sort_order}, t.id DESC
            LIMIT ? OFFSET ?;
        """
        cursor.execute(data_query, params + [limit, offset])
        transactions = cursor.fetchall()

    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    return jsonify({
        "transactions": transactions,
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }), 200

@transactions_bp.route("", methods=["POST"])
@login_required
def create_transaction():
    data = request.get_json(silent=True) or {}
    account_id = data.get("account_id")
    to_account_id = data.get("to_account_id")
    category_id = data.get("category_id")
    txn_type = (data.get("type") or "expense").strip().lower()
    amount = data.get("amount")
    date_val = (data.get("date") or "").strip()
    description = (data.get("description") or "").strip()
    notes = (data.get("notes") or "").strip()
    tags = (data.get("tags") or "").strip()

    if txn_type not in ["income", "expense", "transfer"]:
        return jsonify({"error": "Type must be 'income', 'expense', or 'transfer'"}), 400
    try:
        amount = round(float(amount), 2)
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than zero"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount"}), 400

    if not date_val:
        return jsonify({"error": "Date is required (YYYY-MM-DD)"}), 400
    if not description:
        return jsonify({"error": "Description is required"}), 400
    if not account_id:
        return jsonify({"error": "Account is required"}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        # Verify account belongs to user
        cursor.execute("SELECT id FROM accounts WHERE id = ? AND user_id = ?;", (account_id, g.user_id))
        if not cursor.fetchone():
            return jsonify({"error": "Source account does not exist or does not belong to you"}), 404

        if txn_type == "transfer":
            if not to_account_id:
                return jsonify({"error": "Destination account is required for transfers"}), 400
            if int(to_account_id) == int(account_id):
                return jsonify({"error": "Cannot transfer to the same account"}), 400
            cursor.execute("SELECT id FROM accounts WHERE id = ? AND user_id = ?;", (to_account_id, g.user_id))
            if not cursor.fetchone():
                return jsonify({"error": "Destination account does not exist or does not belong to you"}), 404
        else:
            to_account_id = None

        cursor.execute("""
            INSERT INTO transactions (user_id, account_id, to_account_id, category_id, type, amount, date, description, notes, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (g.user_id, account_id, to_account_id, category_id, txn_type, amount, date_val, description, notes, tags))
        txn_id = cursor.lastrowid

        # Recalculate balances
        recalculate_account_balance(cursor, account_id)
        if to_account_id:
            recalculate_account_balance(cursor, to_account_id)

        # Retrieve newly created transaction with metadata
        cursor.execute("""
            SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon,
                   src.name as account_name, dst.name as to_account_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN accounts src ON t.account_id = src.id
            LEFT JOIN accounts dst ON t.to_account_id = dst.id
            WHERE t.id = ?;
        """, (txn_id,))
        created = cursor.fetchone()

    return jsonify({"message": "Transaction created successfully", "transaction": created}), 201

@transactions_bp.route("/transfer", methods=["POST"])
@login_required
def create_transfer():
    """Convenience endpoint specifically for account transfers."""
    data = request.get_json(silent=True) or {}
    from_account_id = data.get("from_account_id")
    to_account_id = data.get("to_account_id")
    amount = data.get("amount")
    date_val = (data.get("date") or "").strip()
    description = (data.get("description") or "Account Transfer").strip()
    notes = (data.get("notes") or "").strip()

    if not from_account_id or not to_account_id:
        return jsonify({"error": "Both from_account_id and to_account_id are required"}), 400
    if int(from_account_id) == int(to_account_id):
        return jsonify({"error": "Source and destination accounts must be different"}), 400

    try:
        amount = round(float(amount), 2)
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than zero"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount"}), 400

    if not date_val:
        return jsonify({"error": "Date is required"}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM accounts WHERE id = ? AND user_id = ?;", (from_account_id, g.user_id))
        src = cursor.fetchone()
        cursor.execute("SELECT id, name FROM accounts WHERE id = ? AND user_id = ?;", (to_account_id, g.user_id))
        dst = cursor.fetchone()

        if not src or not dst:
            return jsonify({"error": "One or both accounts do not exist"}), 404

        cursor.execute("""
            INSERT INTO transactions (user_id, account_id, to_account_id, type, amount, date, description, notes)
            VALUES (?, ?, ?, 'transfer', ?, ?, ?, ?);
        """, (g.user_id, from_account_id, to_account_id, amount, date_val, description, notes))
        txn_id = cursor.lastrowid

        recalculate_account_balance(cursor, from_account_id)
        recalculate_account_balance(cursor, to_account_id)

        cursor.execute("SELECT * FROM transactions WHERE id = ?;", (txn_id,))
        txn = cursor.fetchone()

    return jsonify({"message": "Transfer completed successfully", "transaction": txn}), 201

@transactions_bp.route("/<int:txn_id>", methods=["GET"])
@login_required
def get_transaction(txn_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon,
                   src.name as account_name, dst.name as to_account_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN accounts src ON t.account_id = src.id
            LEFT JOIN accounts dst ON t.to_account_id = dst.id
            WHERE t.id = ? AND t.user_id = ?;
        """, (txn_id, g.user_id))
        txn = cursor.fetchone()
        if not txn:
            return jsonify({"error": "Transaction not found"}), 404

    return jsonify({"transaction": txn}), 200

@transactions_bp.route("/<int:txn_id>", methods=["PUT"])
@login_required
def update_transaction(txn_id: int):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE id = ? AND user_id = ?;", (txn_id, g.user_id))
        old_txn = cursor.fetchone()
        if not old_txn:
            return jsonify({"error": "Transaction not found"}), 404

        old_acc = old_txn["account_id"]
        old_to_acc = old_txn["to_account_id"]

        new_acc = data.get("account_id", old_acc)
        new_to_acc = data.get("to_account_id", old_to_acc)
        new_cat = data.get("category_id", old_txn["category_id"])
        new_type = data.get("type", old_txn["type"]).strip().lower()
        new_amount = float(data.get("amount", old_txn["amount"]))
        new_date = data.get("date", old_txn["date"])
        new_desc = data.get("description", old_txn["description"])
        new_notes = data.get("notes", old_txn["notes"])
        new_tags = data.get("tags", old_txn["tags"])

        if new_type not in ["income", "expense", "transfer"]:
            return jsonify({"error": "Invalid transaction type"}), 400
        if new_amount <= 0:
            return jsonify({"error": "Amount must be greater than zero"}), 400

        cursor.execute("""
            UPDATE transactions
            SET account_id = ?, to_account_id = ?, category_id = ?, type = ?,
                amount = ?, date = ?, description = ?, notes = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (new_acc, new_to_acc, new_cat, new_type, new_amount, new_date, new_desc, new_notes, new_tags, txn_id))

        # Recalculate all affected accounts
        accounts_to_update = set(filter(None, [old_acc, old_to_acc, new_acc, new_to_acc]))
        for acc in accounts_to_update:
            recalculate_account_balance(cursor, acc)

        cursor.execute("""
            SELECT t.*, c.name as category_name, src.name as account_name, dst.name as to_account_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN accounts src ON t.account_id = src.id
            LEFT JOIN accounts dst ON t.to_account_id = dst.id
            WHERE t.id = ?;
        """, (txn_id,))
        updated = cursor.fetchone()

    return jsonify({"message": "Transaction updated successfully", "transaction": updated}), 200

@transactions_bp.route("/<int:txn_id>", methods=["DELETE"])
@login_required
def delete_transaction(txn_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE id = ? AND user_id = ?;", (txn_id, g.user_id))
        txn = cursor.fetchone()
        if not txn:
            return jsonify({"error": "Transaction not found"}), 404

        acc = txn["account_id"]
        to_acc = txn["to_account_id"]

        cursor.execute("DELETE FROM transactions WHERE id = ?;", (txn_id,))

        recalculate_account_balance(cursor, acc)
        if to_acc:
            recalculate_account_balance(cursor, to_acc)

    return jsonify({"message": "Transaction deleted successfully"}), 200
