import functools
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from config import JWT_EXPIRY_HOURS, JWT_SECRET, MIN_PASSWORD_LENGTH
from database import create_user, get_connection, get_user_by_email, get_user_by_id

ui_bp = Blueprint("ui", __name__)


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("ui.login"))
        return view(*args, **kwargs)

    return wrapped


def _current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_user_by_id(user_id)


def _generate_order_number() -> str:
    return f"ORD-{uuid.uuid4().hex[:8].upper()}"


@ui_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("ui.dashboard"))
    return redirect(url_for("ui.login"))


@ui_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_email"] = user["email"]
            return redirect(url_for("ui.dashboard"))

        flash("Invalid email or password.", "error")
        return render_template("login.html", email=email, error="Invalid email or password.")

    return render_template("login.html", email="")


@ui_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not name or not email:
            error = "Name and email are required."
            return render_template("register.html", name=name, email=email, error=error)

        if len(password) < MIN_PASSWORD_LENGTH:
            error = f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            return render_template("register.html", name=name, email=email, error=error)

        if password != password_confirm:
            error = "Passwords do not match."
            return render_template("register.html", name=name, email=email, error=error)

        try:
            create_user(email, password, name)
        except ValueError as exc:
            if str(exc) == "email_taken":
                error = "This email is already registered."
            else:
                error = "Registration failed. Please check your input."
            return render_template("register.html", name=name, email=email, error=error)

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("ui.login"))

    return render_template("register.html", name="", email="")


@ui_bp.route("/dashboard")
@login_required
def dashboard():
    with get_connection() as conn:
        products = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    return render_template("dashboard.html", products=products, user=_current_user())


@ui_bp.route("/items/<int:item_id>")
@login_required
def item_detail(item_id):
    with get_connection() as conn:
        product = conn.execute("SELECT * FROM products WHERE id = ?", (item_id,)).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("ui.dashboard"))
    return render_template("item_detail.html", product=product, user=_current_user())


@ui_bp.route("/items/<int:item_id>/add-to-cart", methods=["POST"])
@login_required
def add_to_cart(item_id):
    user_id = session["user_id"]
    quantity = max(1, int(request.form.get("quantity", 1)))

    with get_connection() as conn:
        product = conn.execute("SELECT id FROM products WHERE id = ?", (item_id,)).fetchone()
        if not product:
            flash("Product not found.", "error")
            return redirect(url_for("ui.dashboard"))

        existing = conn.execute(
            "SELECT id, quantity FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user_id, item_id),
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE cart_items SET quantity = quantity + ? WHERE id = ?",
                (quantity, existing["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)",
                (user_id, item_id, quantity),
            )

    return redirect(url_for("ui.cart"))


@ui_bp.route("/cart")
@login_required
def cart():
    user_id = session["user_id"]
    with get_connection() as conn:
        items = conn.execute(
            """
            SELECT ci.id AS cart_id, ci.quantity, p.id, p.name, p.price, p.description
            FROM cart_items ci
            JOIN products p ON p.id = ci.product_id
            WHERE ci.user_id = ?
            ORDER BY ci.id
            """,
            (user_id,),
        ).fetchall()

    total = sum(row["price"] * row["quantity"] for row in items)
    return render_template("cart.html", items=items, total=total, user=_current_user())


@ui_bp.route("/cart/<int:cart_id>/update", methods=["POST"])
@login_required
def update_cart_item(cart_id):
    user_id = session["user_id"]
    quantity = int(request.form.get("quantity", 1))

    with get_connection() as conn:
        item = conn.execute(
            "SELECT id FROM cart_items WHERE id = ? AND user_id = ?",
            (cart_id, user_id),
        ).fetchone()
        if not item:
            flash("Cart item not found.", "error")
            return redirect(url_for("ui.cart"))

        if quantity <= 0:
            conn.execute("DELETE FROM cart_items WHERE id = ?", (cart_id,))
        else:
            conn.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (quantity, cart_id))

    return redirect(url_for("ui.cart"))


@ui_bp.route("/cart/<int:cart_id>/remove", methods=["POST"])
@login_required
def remove_cart_item(cart_id):
    user_id = session["user_id"]
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM cart_items WHERE id = ? AND user_id = ?",
            (cart_id, user_id),
        )
    return redirect(url_for("ui.cart"))


@ui_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    user_id = session["user_id"]

    with get_connection() as conn:
        items = conn.execute(
            """
            SELECT ci.quantity, p.id AS product_id, p.name, p.price
            FROM cart_items ci
            JOIN products p ON p.id = ci.product_id
            WHERE ci.user_id = ?
            """,
            (user_id,),
        ).fetchall()

        if request.method == "GET":
            if not items:
                flash("Your cart is empty.", "error")
                return redirect(url_for("ui.cart"))
            total = sum(row["price"] * row["quantity"] for row in items)
            return render_template("checkout.html", items=items, total=total, user=_current_user())

        if not items:
            flash("Your cart is empty.", "error")
            return redirect(url_for("ui.cart"))

        order_number = _generate_order_number()
        total = sum(row["price"] * row["quantity"] for row in items)

        cursor = conn.execute(
            "INSERT INTO orders (user_id, order_number, total) VALUES (?, ?, ?)",
            (user_id, order_number, total),
        )
        order_id = cursor.lastrowid

        for row in items:
            conn.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                (order_id, row["product_id"], row["quantity"], row["price"]),
            )

        conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))

    return redirect(url_for("ui.success", order_number=order_number))


@ui_bp.route("/success")
@login_required
def success():
    order_number = request.args.get("order_number", "")
    if not order_number:
        return redirect(url_for("ui.dashboard"))
    return render_template("success.html", order_number=order_number, user=_current_user())


@ui_bp.route("/profile")
@login_required
def profile():
    user = _current_user()
    with get_connection() as conn:
        order_count = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE user_id = ?", (user["id"],)
        ).fetchone()[0]
    return render_template("profile.html", user=user, order_count=order_count)


@ui_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("ui.login"))


def create_api_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
