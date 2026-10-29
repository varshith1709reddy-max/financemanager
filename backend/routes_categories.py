from flask import Blueprint, request, jsonify, g
from backend.database import get_db
from backend.auth import login_required

categories_bp = Blueprint("categories", __name__, url_prefix="/api/categories")

@categories_bp.route("", methods=["GET"])
@login_required
def list_categories():
    cat_type = request.args.get("type")
    with get_db() as conn:
        cursor = conn.cursor()
        if cat_type:
            cursor.execute("""
                SELECT * FROM categories
                WHERE (user_id IS NULL OR user_id = ?) AND type = ?
                ORDER BY name ASC;
            """, (g.user_id, cat_type.lower()))
        else:
            cursor.execute("""
                SELECT * FROM categories
                WHERE user_id IS NULL OR user_id = ?
                ORDER BY type DESC, name ASC;
            """, (g.user_id,))
        categories = cursor.fetchall()

    return jsonify({"categories": categories}), 200

@categories_bp.route("", methods=["POST"])
@login_required
def create_category():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    cat_type = (data.get("type") or "expense").strip().lower()
    color = (data.get("color") or "#3B82F6").strip()
    icon = (data.get("icon") or "tag").strip()

    if not name:
        return jsonify({"error": "Category name is required"}), 400
    if cat_type not in ["income", "expense"]:
        return jsonify({"error": "Category type must be 'income' or 'expense'"}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO categories (user_id, name, type, color, icon)
            VALUES (?, ?, ?, ?, ?);
        """, (g.user_id, name, cat_type, color, icon))
        cat_id = cursor.lastrowid
        cursor.execute("SELECT * FROM categories WHERE id = ?;", (cat_id,))
        cat = cursor.fetchone()

    return jsonify({"message": "Category created successfully", "category": cat}), 201

@categories_bp.route("/<int:cat_id>", methods=["DELETE"])
@login_required
def delete_category(cat_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id FROM categories WHERE id = ?;", (cat_id,))
        cat = cursor.fetchone()
        if not cat:
            return jsonify({"error": "Category not found"}), 404
        if cat["user_id"] is None:
            return jsonify({"error": "Cannot delete standard system category"}), 403
        if cat["user_id"] != g.user_id:
            return jsonify({"error": "Unauthorized"}), 403

        cursor.execute("DELETE FROM categories WHERE id = ?;", (cat_id,))

    return jsonify({"message": "Category deleted successfully"}), 200
