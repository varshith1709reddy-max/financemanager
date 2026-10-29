import hashlib
import secrets
import time
from functools import wraps
from flask import Blueprint, request, jsonify, session, g
from backend.database import get_db

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# In-memory token store for Bearer token auth: token -> {"user_id": int, "expires_at": float}
_TOKENS = {}

def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        100000
    ).hex()
    return hashed, salt

def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    hashed, _ = hash_password(password, salt)
    return secrets.compare_digest(hashed, expected_hash)

def generate_auth_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    # Token valid for 7 days
    _TOKENS[token] = {
        "user_id": user_id,
        "expires_at": time.time() + (7 * 24 * 3600)
    }
    return token

def get_current_user_id() -> int | None:
    # 1. Check Bearer token in Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        token_data = _TOKENS.get(token)
        if token_data:
            if token_data["expires_at"] > time.time():
                return token_data["user_id"]
            else:
                del _TOKENS[token]
                return None

    # 2. Check Flask session cookie
    if "user_id" in session:
        return session["user_id"]

    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Authentication required", "code": "UNAUTHORIZED"}), 401
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email, full_name, currency, created_at FROM users WHERE id = ?;", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "User no longer exists", "code": "USER_NOT_FOUND"}), 401
            g.user = user
            g.user_id = user_id
            
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    full_name = (data.get("full_name") or "").strip() or username
    currency = (data.get("currency") or "USD").strip().upper()

    if not username:
        return jsonify({"error": "Username is required"}), 400
    if not email or "@" not in email:
        return jsonify({"error": "A valid email address is required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    password_hash, salt = hash_password(password)

    with get_db() as conn:
        cursor = conn.cursor()
        # Check if username or email already exists
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?;", (username, email))
        existing = cursor.fetchone()
        if existing:
            return jsonify({"error": "Username or email is already registered"}), 409

        cursor.execute(
            """INSERT INTO users (username, email, password_hash, salt, full_name, currency)
               VALUES (?, ?, ?, ?, ?, ?);""",
            (username, email, password_hash, salt, full_name, currency)
        )
        user_id = cursor.lastrowid

        # Also create default primary accounts for new user: Checking & Savings
        cursor.execute(
            """INSERT INTO accounts (user_id, name, type, balance, initial_balance, currency)
               VALUES (?, ?, ?, 0.0, 0.0, ?);""",
            (user_id, "Main Checking", "checking", currency)
        )
        cursor.execute(
            """INSERT INTO accounts (user_id, name, type, balance, initial_balance, currency)
               VALUES (?, ?, ?, 0.0, 0.0, ?);""",
            (user_id, "Emergency Savings", "savings", currency)
        )

        cursor.execute("SELECT id, username, email, full_name, currency, created_at FROM users WHERE id = ?;", (user_id,))
        user = cursor.fetchone()

    token = generate_auth_token(user_id)
    session["user_id"] = user_id

    return jsonify({
        "message": "User registered successfully",
        "token": token,
        "user": user
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    identifier = (data.get("username") or data.get("email") or "").strip()
    password = data.get("password") or ""

    if not identifier or not password:
        return jsonify({"error": "Username/email and password are required"}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, password_hash, salt, full_name, currency, created_at FROM users WHERE username = ? OR email = ?;",
            (identifier, identifier.lower())
        )
        user = cursor.fetchone()

    if not user or not verify_password(password, user["salt"], user["password_hash"]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_auth_token(user["id"])
    session["user_id"] = user["id"]

    safe_user = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "full_name": user["full_name"],
        "currency": user["currency"],
        "created_at": user["created_at"]
    }

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": safe_user
    }), 200

@auth_bp.route("/logout", methods=["POST"])
def logout():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token in _TOKENS:
            del _TOKENS[token]
    session.pop("user_id", None)
    return jsonify({"message": "Logged out successfully"}), 200

@auth_bp.route("/me", methods=["GET"])
@login_required
def get_me():
    return jsonify({"user": g.user}), 200

@auth_bp.route("/profile", methods=["PUT"])
@login_required
def update_profile():
    data = request.get_json(silent=True) or {}
    full_name = (data.get("full_name") or "").strip() or g.user["full_name"]
    email = (data.get("email") or "").strip().lower() or g.user["email"]
    currency = (data.get("currency") or "").strip().upper() or g.user["currency"]
    new_password = data.get("new_password")

    with get_db() as conn:
        cursor = conn.cursor()
        # Verify email uniqueness if changed
        if email != g.user["email"]:
            cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?;", (email, g.user_id))
            if cursor.fetchone():
                return jsonify({"error": "Email is already taken"}), 409

        if new_password:
            if len(new_password) < 6:
                return jsonify({"error": "Password must be at least 6 characters"}), 400
            pw_hash, salt = hash_password(new_password)
            cursor.execute(
                """UPDATE users SET full_name = ?, email = ?, currency = ?, password_hash = ?, salt = ?
                   WHERE id = ?;""",
                (full_name, email, currency, pw_hash, salt, g.user_id)
            )
        else:
            cursor.execute(
                "UPDATE users SET full_name = ?, email = ?, currency = ? WHERE id = ?;",
                (full_name, email, currency, g.user_id)
            )

        cursor.execute("SELECT id, username, email, full_name, currency, created_at FROM users WHERE id = ?;", (g.user_id,))
        updated_user = cursor.fetchone()

    return jsonify({"message": "Profile updated", "user": updated_user}), 200
