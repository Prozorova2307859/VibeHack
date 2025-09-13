import uuid
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
import bcrypt
from http import HTTPStatus

# --- Configuration ---
app = Flask(__name__, static_folder=".", static_url_path="")
app.config["JWT_SECRET_KEY"] = "replace-with-strong-secret"  # Replace with secure secret (env var)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)

jwt = JWTManager(app)

# --- Models ---
class User:
    def __init__(self, id, email, password_hash, rating=0.0, checked_in=False):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.rating = rating
        self.checked_in = checked_in

# --- In-memory store ---
class Store:
    def __init__(self):
        self._lock = threading.RLock()
        self._users = {}  # key: email
        self._count_current_visitors = 0

    def get_by_email(self, email):
        with self._lock:
            return self._users.get(email), email in self._users

    def save_user(self, user):
        with self._lock:
            self._users[user.email] = user

    def inc_visitors(self):
        with self._lock:
            self._count_current_visitors += 1

    def dec_visitors(self):
        with self._lock:
            if self._count_current_visitors > 0:
                self._count_current_visitors -= 1

    def visitors(self):
        with self._lock:
            return self._count_current_visitors

# --- Global store ---
store = Store()

# --- Helper functions ---
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def check_password(hash, password):
    return bcrypt.checkpw(password.encode("utf-8"), hash)

# --- Handlers ---
@app.route("/auth/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
    except Exception:
        return jsonify({"error": "invalid request body"}), HTTPStatus.BAD_REQUEST

    user, exists = store.get_by_email(email)
    if not exists:
        return jsonify({"error": "invalid email or password"}), HTTPStatus.UNAUTHORIZED

    if not check_password(user.password_hash, password):
        return jsonify({"error": "invalid email or password"}), HTTPStatus.UNAUTHORIZED

    expires = datetime.utcnow() + app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    access_token = create_access_token(identity=user.id)
    return jsonify({"token": access_token, "expires_at": expires.isoformat()})

@app.route("/status", methods=["GET"])
@jwt_required()
def status():
    user_id = get_jwt_identity()
    user = None
    with store._lock:
        for u in store._users.values():
            if u.id == user_id:
                user = u
                break

    if user is None:
        return jsonify({"error": "user not found"}), HTTPStatus.UNAUTHORIZED

    return jsonify({
        "current_visitors": store.visitors(),
        "user": {
            "id": user.id,
            "email": user.email,
            "rating": user.rating,
            "checked_in": user.checked_in,
        },
    })

@app.route("/booking", methods=["POST"])
@jwt_required()
def booking():
    user_id = get_jwt_identity()
    user = None
    with store._lock:
        for u in store._users.values():
            if u.id == user_id:
                user = u
                break

    if user is None:
        return jsonify({"error": "user not found"}), HTTPStatus.UNAUTHORIZED

    RATING_THRESHOLD = 10.0
    if user.rating < RATING_THRESHOLD:
        return (
            jsonify({
                "error": "Insufficient rating for booking. Increase your rating by visiting the coworking space."
            }),
            HTTPStatus.FORBIDDEN,
        )

    return jsonify({"status": "ok", "message": "booking access granted"})

@app.route("/checkin", methods=["POST"])
@jwt_required()
def checkin():
    user_id = get_jwt_identity()
    user = None
    with store._lock:
        for u in store._users.values():
            if u.id == user_id:
                user = u
                break

    if user is None:
        return jsonify({"error": "user not found"}), HTTPStatus.UNAUTHORIZED

    with store._lock:
        if not user.checked_in:
            user.checked_in = True
            store.inc_visitors()
        else:
            user.checked_in = False
            store.dec_visitors()
            user.rating += 1.0

    return jsonify({
        "checked_in": user.checked_in,
        "visitors": store.visitors(),
        "rating": user.rating,
    })

# --- Static file serving ---
@app.route("/css/<path:path>")
def serve_css(path):
    return send_from_directory("css", path)

@app.route("/js/<path:path>")
def serve_js(path):
    return send_from_directory("js", path)

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

# --- Main ---
if __name__ == "__main__":
    # Test user
    pw_hash = hash_password("password123")
    u = User(id=str(uuid.uuid4()), email="test@example.com", password_hash=pw_hash, rating=5.0)
    store.save_user(u)

    print("Server started at http://localhost:8080")
    app.run(host="0.0.0.0", port=8080, debug=False)