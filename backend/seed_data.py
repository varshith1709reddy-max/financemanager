from backend.database import get_db
from backend.auth import hash_password
from backend.populate_jan_to_oct import populate_database

def seed_demo_user():
    username = "demo"
    email = "demo@student.college.edu"
    password = "password123"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?;", (username,))
        existing = cursor.fetchone()
        if existing:
            return existing["id"]

        pw_hash, salt = hash_password(password)
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, salt, full_name, currency)
            VALUES (?, ?, ?, ?, 'Rahul Sharma (Student)', 'INR');
        """, (username, email, pw_hash, salt))
        user_id = cursor.lastrowid
        conn.commit()

    populate_database()
    return user_id
