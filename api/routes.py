import functools
import time
from collections import defaultdict

import jwt
from flask import Blueprint, g, jsonify, request

from config import DEFAULT_PAGE_SIZE, JWT_SECRET, MAX_PAGE_SIZE, RATE_LIMIT_PER_MINUTE
from database import create_user, get_connection, get_user_by_email, get_user_by_id
from ui.routes import create_api_token
from werkzeug.security import check_password_hash

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")

_rate_limit_store: dict[str, list[float]] = defaultdict(list)


def _error_response(message: str, code: str, status: int):
    return jsonify({"error": message, "code": code}), status


def _get_bearer_token() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def token_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        token = _get_bearer_token()
        if not token:
            return _error_response("Authentication required.", "unauthorized", 401)

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user = get_user_by_id(int(payload["sub"]))
            if not user:
                return _error_response("Invalid token.", "invalid_token", 401)
            g.current_user = user
        except jwt.ExpiredSignatureError:
            return _error_response("Token has expired.", "token_expired", 401)
        except jwt.InvalidTokenError:
            return _error_response("Invalid token.", "invalid_token", 401)

        return view(*args, **kwargs)

    return wrapped


@api_bp.route("/auth/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip()

    if not email or not password or not name:
        return _error_response("Email, password, and name are required.", "validation_error", 422)

    try:
        user_id = create_user(email, password, name)
    except ValueError as exc:
        if str(exc) == "email_taken":
            return _error_response("Email is already registered.", "email_taken", 400)
        if str(exc) == "password_too_short":
            return _error_response("Password is too short.", "password_too_short", 422)
        return _error_response("Invalid registration data.", "validation_error", 422)

    user = get_user_by_id(user_id)
    return jsonify({"id": user["id"], "email": user["email"], "name": user["name"]}), 201


@api_bp.route("/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    user = get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return _error_response("Invalid email or password.", "invalid_credentials", 401)

    token = create_api_token(user["id"], user["email"])
    return jsonify({"access_token": token, "token_type": "Bearer"})


@api_bp.route("/items", methods=["GET"])
def list_items():
    page = max(1, int(request.args.get("page", 1)))
    limit = min(MAX_PAGE_SIZE, max(1, int(request.args.get("limit", DEFAULT_PAGE_SIZE))))
    category = request.args.get("category", "").strip()
    offset = (page - 1) * limit

    query = "SELECT id, title, description, category, owner_id, created_at FROM api_items"
    count_query = "SELECT COUNT(*) FROM api_items"
    params: list = []

    if category:
        query += " WHERE category = ?"
        count_query += " WHERE category = ?"
        params.append(category)

    query += " ORDER BY id LIMIT ? OFFSET ?"

    with get_connection() as conn:
        total = conn.execute(count_query, params).fetchone()[0]
        rows = conn.execute(query, params + [limit, offset]).fetchall()

    items = [dict(row) for row in rows]
    total_pages = max(1, (total + limit - 1) // limit)

    return jsonify(
        {
            "items": items,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
        }
    )


@api_bp.route("/items", methods=["POST"])
@token_required
def create_item():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    category = (data.get("category") or "general").strip()

    if not title:
        return _error_response("Title is required.", "validation_error", 422)

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO api_items (title, description, category, owner_id) VALUES (?, ?, ?, ?)",
            (title, description, category, g.current_user["id"]),
        )
        item_id = cursor.lastrowid
        item = conn.execute(
            "SELECT id, title, description, category, owner_id, created_at FROM api_items WHERE id = ?",
            (item_id,),
        ).fetchone()

    return jsonify(dict(item)), 201


@api_bp.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    with get_connection() as conn:
        item = conn.execute(
            "SELECT id, title, description, category, owner_id, created_at FROM api_items WHERE id = ?",
            (item_id,),
        ).fetchone()

    if not item:
        return _error_response("Item not found.", "not_found", 404)

    return jsonify(dict(item))


@api_bp.route("/items/<int:item_id>", methods=["PUT"])
@token_required
def update_item(item_id):
    with get_connection() as conn:
        item = conn.execute("SELECT * FROM api_items WHERE id = ?", (item_id,)).fetchone()
        if not item:
            return _error_response("Item not found.", "not_found", 404)

        if item["owner_id"] != g.current_user["id"]:
            return _error_response("You can only update your own items.", "forbidden", 403)

        data = request.get_json(silent=True) or {}
        title = (data.get("title") or item["title"]).strip()
        description = data.get("description", item["description"])
        category = (data.get("category") or item["category"]).strip()

        if not title:
            return _error_response("Title is required.", "validation_error", 422)

        conn.execute(
            "UPDATE api_items SET title = ?, description = ?, category = ? WHERE id = ?",
            (title, description, category, item_id),
        )
        updated = conn.execute(
            "SELECT id, title, description, category, owner_id, created_at FROM api_items WHERE id = ?",
            (item_id,),
        ).fetchone()

    return jsonify(dict(updated))


@api_bp.route("/items/<int:item_id>", methods=["DELETE"])
@token_required
def delete_item(item_id):
    with get_connection() as conn:
        item = conn.execute("SELECT * FROM api_items WHERE id = ?", (item_id,)).fetchone()
        if not item:
            return _error_response("Item not found.", "not_found", 404)

        if item["owner_id"] != g.current_user["id"]:
            return _error_response("You can only delete your own items.", "forbidden", 403)

        conn.execute("DELETE FROM api_items WHERE id = ?", (item_id,))

    return "", 204


@api_bp.route("/items/trigger-error", methods=["POST"])
def trigger_error():
    """Edge-case endpoint for practicing error handling in tests."""
    data = request.get_json(silent=True) or {}
    payload = data.get("payload", "")

    if payload == "server_error":
        return _error_response("Simulated internal server error.", "server_error", 500)

    client_ip = request.remote_addr or "unknown"
    now = time.time()
    window_start = now - 60

    _rate_limit_store[client_ip] = [
        ts for ts in _rate_limit_store[client_ip] if ts > window_start
    ]

    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_PER_MINUTE:
        return _error_response(
            "Rate limit exceeded. Try again later.",
            "rate_limit_exceeded",
            429,
        )

    _rate_limit_store[client_ip].append(now)
    return jsonify({"status": "ok", "message": "Request accepted."})


@api_bp.route("/admin/reset", methods=["POST"])
def admin_reset():
    """Reset database to initial seed state (for test automation)."""
    from database import reset_db

    reset_db()
    return jsonify({"status": "ok", "message": "Database has been reset to initial state."})
