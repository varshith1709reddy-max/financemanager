import os
from app import create_app
from backend.seed_data import seed_demo_user

app = create_app()
# Seed initial demo profile if needed
seed_demo_user()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Starting production WSGI server (Waitress) on http://{host}:{port}")
    try:
        from waitress import serve
        serve(app, host=host, port=port, threads=8)
    except ImportError:
        print("Waitress not found, falling back to standard server")
        app.run(host=host, port=port)
