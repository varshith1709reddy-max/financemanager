from flask import Blueprint, request, jsonify, g
from backend.database import get_db
from backend.auth import login_required

accounts_bp = Blueprint("accounts", __name__, url_prefix="/api/accounts")

def recalculate_account_balance(cursor, account_id: int):
    """Calculates balance from initial_balance + income - expense - outgoing transfers + incoming transfers."""
    cursor.execute("SELECT initial_balance FROM accounts WHERE id = ?;", (account_id,))
    acc = cursor.fetchone()
    if not acc:
        return 0.0

    initial_balance = float(acc["initial_balance"] or 0.0)

    # 1. Income transactions on this account
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE account_id = ? AND type = 'income';",
        (account_id,)
    )
    income = float(cursor.fetchone()["total"] or 0.0)

    # 2. Expense transactions on this account
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE account_id = ? AND type = 'expense';",
        (account_id,)
    )
    expense = float(cursor.fetchone()["total"] or 0.0)

    # 3. Outgoing transfers from this account
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE account_id = ? AND type = 'transfer';",
        (account_id,)
    )
    transfers_out = float(cursor.fetchone()["total"] or 0.0)

    # 4. Incoming transfers into this account
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE to_account_id = ? AND type = 'transfer';",
        (account_id,)
    )
    transfers_in = float(cursor.fetchone()["total"] or 0.0)

    new_balance = round(initial_balance + income - expense - transfers_out + transfers_in, 2)
    cursor.execute("UPDATE accounts SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (new_balance, account_id))
    return new_balance

@accounts_bp.route("", methods=["GET"])
@login_required
def list_accounts():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM accounts WHERE user_id = ? AND is_active = 1;", (g.user_id,))
        acc_ids = [row["id"] for row in cursor.fetchall()]

        # Recalculate to ensure accurate synchronization
        for acc_id in acc_ids:
            recalculate_account_balance(cursor, acc_id)

        cursor.execute("""
            SELECT a.*, 
                   (SELECT COUNT(*) FROM transactions t WHERE t.account_id = a.id OR t.to_account_id = a.id) as transaction_count
            FROM accounts a
            WHERE a.user_id = ? AND a.is_active = 1
            ORDER BY a.name ASC;
        """, (g.user_id,))
        accounts = cursor.fetchall()

    return jsonify({"accounts": accounts}), 200

@accounts_bp.route("", methods=["POST"])
@login_required
def create_account():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    acc_type = (data.get("type") or "checking").strip().lower()
    initial_balance = float(data.get("initial_balance") or 0.0)
    currency = (data.get("currency") or g.user.get("currency") or "USD").strip().upper()
    account_number = (data.get("account_number") or "").strip()

    valid_types = ["checking", "savings", "credit_card", "investment", "cash"]
    if not name:
        return jsonify({"error": "Account name is required"}), 400
    if acc_type not in valid_types:
        return jsonify({"error": f"Invalid account type. Must be one of {valid_types}"}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO accounts (user_id, name, type, balance, initial_balance, currency, account_number)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (g.user_id, name, acc_type, initial_balance, initial_balance, currency, account_number))
        account_id = cursor.lastrowid
        cursor.execute("SELECT * FROM accounts WHERE id = ?;", (account_id,))
        new_account = cursor.fetchone()

    return jsonify({"message": "Account created successfully", "account": new_account}), 201

@accounts_bp.route("/<int:account_id>", methods=["GET"])
@login_required
def get_account(account_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        recalculate_account_balance(cursor, account_id)
        cursor.execute("SELECT * FROM accounts WHERE id = ? AND user_id = ?;", (account_id, g.user_id))
        account = cursor.fetchone()
        if not account:
            return jsonify({"error": "Account not found"}), 404

        # Fetch recent transactions for this account
        cursor.execute("""
            SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon,
                   src.name as source_account_name, dst.name as dest_account_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN accounts src ON t.account_id = src.id
            LEFT JOIN accounts dst ON t.to_account_id = dst.id
            WHERE (t.account_id = ? OR t.to_account_id = ?) AND t.user_id = ?
            ORDER BY t.date DESC, t.id DESC
            LIMIT 25;
        """, (account_id, account_id, g.user_id))
        transactions = cursor.fetchall()

    return jsonify({"account": account, "recent_transactions": transactions}), 200

@accounts_bp.route("/<int:account_id>", methods=["PUT"])
@login_required
def update_account(account_id: int):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    acc_type = (data.get("type") or "").strip().lower()
    initial_balance = data.get("initial_balance")
    currency = (data.get("currency") or "").strip().upper()
    account_number = data.get("account_number")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE id = ? AND user_id = ?;", (account_id, g.user_id))
        account = cursor.fetchone()
        if not account:
            return jsonify({"error": "Account not found"}), 404

        new_name = name or account["name"]
        new_type = acc_type or account["type"]
        new_currency = currency or account["currency"]
        new_acc_num = account_number if account_number is not None else account["account_number"]
        new_initial = float(initial_balance) if initial_balance is not None else account["initial_balance"]

        cursor.execute("""
            UPDATE accounts
            SET name = ?, type = ?, initial_balance = ?, currency = ?, account_number = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (new_name, new_type, new_initial, new_currency, new_acc_num, account_id))

        recalculate_account_balance(cursor, account_id)
        cursor.execute("SELECT * FROM accounts WHERE id = ?;", (account_id,))
        updated = cursor.fetchone()

    return jsonify({"message": "Account updated successfully", "account": updated}), 200

@accounts_bp.route("/<int:account_id>", methods=["DELETE"])
@login_required
def delete_account(account_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM accounts WHERE id = ? AND user_id = ?;", (account_id, g.user_id))
        if not cursor.fetchone():
            return jsonify({"error": "Account not found"}), 404

        # Delete related transactions and account
        cursor.execute("DELETE FROM transactions WHERE account_id = ? OR to_account_id = ?;", (account_id, account_id))
        cursor.execute("DELETE FROM accounts WHERE id = ?;", (account_id,))

    return jsonify({"message": "Account and associated transactions deleted successfully"}), 200
