import csv
import hashlib
import io
import secrets
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

from flask import (
    Flask,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database.db"
SECRET_FILE = BASE_DIR / ".secret_key"
ADMIN_ROLE = "admin"
KITCHEN_ROLES = {ADMIN_ROLE, "kitchen_staff"}
ORDER_STATUSES = {"Pending", "Preparing", "Ready", "Served", "Cancelled"}
CATEGORIES = [
    "Breakfast",
    "Combos",
    "Meat",
    "Main Food",
    "Sweet Categories",
    "Drinks",
    "Add-ons",
]

app = Flask(__name__)


def load_secret_key():
    if SECRET_FILE.exists():
        return SECRET_FILE.read_text(encoding="utf-8").strip()

    key = secrets.token_hex(32)
    SECRET_FILE.write_text(key, encoding="utf-8")
    return key


def db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_one(query, params=()):
    with closing(db()) as conn:
        return conn.execute(query, params).fetchone()


def fetch_all(query, params=()):
    with closing(db()) as conn:
        return conn.execute(query, params).fetchall()


def set_user_session(user):
    session.update(
        {
            "user_id": user["id"],
            "username": user["username"],
            "role": user["role"],
        }
    )


def require_admin():
    if session.get("role") != ADMIN_ROLE:
        return redirect(url_for("admin_login"))


def require_kitchen():
    if session.get("role") not in KITCHEN_ROLES:
        return redirect(url_for("kitchen_login"))


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
    return f"pbkdf2:{salt}:{digest.hex()}"


def check_password(stored_password, provided_password):
    try:
        _, salt, digest = stored_password.split(":", 2)
    except (AttributeError, ValueError):
        return False

    check = hashlib.pbkdf2_hmac(
        "sha256",
        provided_password.encode(),
        salt.encode(),
        260000,
    )
    return check.hex() == digest


def get_user(username):
    return fetch_one("SELECT * FROM users WHERE username = ?", (username,))


def get_cart_items(cart=None):
    cart = cart if cart is not None else session.get("cart", {})
    if not cart:
        return [], 0

    ids = [int(food_id) for food_id in cart if str(food_id).isdigit()]
    if not ids:
        return [], 0

    placeholders = ",".join("?" for _ in ids)
    rows = fetch_all(
        f"SELECT * FROM food_items WHERE id IN ({placeholders})",
        ids,
    )
    items_by_id = {str(item["id"]): item for item in rows}

    items = []
    total = 0
    for food_id, qty in cart.items():
        item = items_by_id.get(str(food_id))
        if not item:
            continue

        subtotal = item["price"] * qty
        total += subtotal
        items.append(
            {
                "id": str(item["id"]),
                "name": item["name"],
                "price": item["price"],
                "qty": qty,
                "subtotal": subtotal,
            }
        )

    return items, total


def init_db():
    with closing(db()) as conn:
        conn.executescript((BASE_DIR / "schema.sql").read_text(encoding="utf-8"))

        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                [
                    ("admin", hash_password("admin123"), ADMIN_ROLE),
                    ("kitchen", hash_password("kitchen123"), "kitchen_staff"),
                ],
            )

        if conn.execute("SELECT COUNT(*) FROM food_items").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO food_items (name, category, price) VALUES (?, ?, ?)",
                [
                    ("Chapati", "Breakfast", 30),
                    ("Mandazi", "Breakfast", 20),
                    ("Uji", "Breakfast", 40),
                    ("Boiled Eggs", "Breakfast", 30),
                    ("Chapati + Tea", "Combos", 60),
                    ("Rice + Stew Combo", "Combos", 150),
                    ("Ugali + Sukuma Combo", "Combos", 100),
                    ("Beef Stew", "Meat", 150),
                    ("Chicken", "Meat", 200),
                    ("Fried Fish", "Meat", 180),
                    ("Nyama Choma", "Meat", 250),
                    ("Rice", "Main Food", 80),
                    ("Ugali", "Main Food", 60),
                    ("Pilau", "Main Food", 120),
                    ("Githeri", "Main Food", 80),
                    ("Cake Slice", "Sweet Categories", 80),
                    ("Doughnut", "Sweet Categories", 30),
                    ("Maandazi Tamu", "Sweet Categories", 25),
                    ("Mango Milkshake", "Drinks", 100),
                    ("Tea", "Drinks", 30),
                    ("Soda", "Drinks", 60),
                    ("Water", "Drinks", 30),
                    ("Extra Sauce", "Add-ons", 20),
                    ("Kachumbari", "Add-ons", 30),
                    ("Avocado", "Add-ons", 40),
                ],
            )

        conn.commit()


app.secret_key = load_secret_key()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/landing")
def landing():
    return render_template("landing.html")


@app.route("/menu")
def menu():
    items = fetch_all("SELECT * FROM food_items ORDER BY category, name")
    cart = session.get("cart", {})
    _, cart_total = get_cart_items(cart)
    return render_template(
        "menu.html",
        items=items,
        categories=CATEGORIES,
        cart_count=sum(cart.values()),
        cart_total=cart_total,
    )


@app.route("/cart")
def cart():
    cart_items, total = get_cart_items()
    return render_template("cart.html", cart_items=cart_items, total=total)


@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    food_id = str(request.form.get("food_id"))
    cart = session.get("cart", {})
    cart[food_id] = cart.get(food_id, 0) + 1
    session["cart"] = cart
    session.modified = True
    return jsonify({"success": True, "cart_count": sum(cart.values())})


@app.route("/update-cart", methods=["POST"])
def update_cart():
    food_id = str(request.form.get("food_id"))
    action = request.form.get("action")
    cart = session.get("cart", {})

    if action == "increase":
        cart[food_id] = cart.get(food_id, 0) + 1
    elif action == "decrease":
        if cart.get(food_id, 0) > 1:
            cart[food_id] -= 1
        else:
            cart.pop(food_id, None)
    elif action == "remove":
        cart.pop(food_id, None)

    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))


@app.route("/checkout")
def checkout():
    if not session.get("cart"):
        return redirect(url_for("menu"))

    cart_items, total = get_cart_items()
    return render_template("checkout.html", cart_items=cart_items, total=total)


@app.route("/place-order", methods=["POST"])
def place_order():
    customer_name = request.form.get("customer_name", "").strip()
    phone_number = request.form.get("phone_number", "").strip()
    table_number = request.form.get("table_number", "").strip()

    if not (customer_name and phone_number and table_number):
        return redirect(url_for("payment_failed"))

    cart_items, total = get_cart_items()
    if not cart_items:
        return redirect(url_for("menu"))

    try:
        with closing(db()) as conn:
            cursor = conn.execute(
                """
                INSERT INTO orders (customer_name, phone_number, table_number, total_amount)
                VALUES (?, ?, ?, ?)
                """,
                (customer_name, phone_number, table_number, total),
            )
            order_id = cursor.lastrowid
            conn.executemany(
                "INSERT INTO order_items (order_id, food_id, quantity) VALUES (?, ?, ?)",
                [(order_id, int(item["id"]), item["qty"]) for item in cart_items],
            )
            conn.commit()
    except Exception as exc:
        print(f"Order error: {exc}")
        return redirect(url_for("payment_failed"))

    session.pop("cart", None)
    session.modified = True
    return redirect(url_for("payment_success", order_id=order_id))


@app.route("/payment-success/<int:order_id>")
def payment_success(order_id):
    order = fetch_one("SELECT * FROM orders WHERE id = ?", (order_id,))
    if not order:
        return redirect(url_for("index"))
    return render_template("payment_success.html", order=order)


@app.route("/payment-failed")
def payment_failed():
    return render_template("payments_not_successful.html")


@app.route("/my-orders")
def my_orders():
    return render_template("my_orders.html")


@app.route("/feedback")
def feedback():
    return render_template("feedback.html")


@app.route("/submit-feedback", methods=["POST"])
def submit_feedback():
    rating = request.form.get("rating")
    comment = request.form.get("comment", "").strip()
    if not rating:
        flash("Please select a rating.", "error")
        return redirect(url_for("feedback"))

    with closing(db()) as conn:
        conn.execute(
            "INSERT INTO feedback (rating, comment) VALUES (?, ?)",
            (int(rating), comment or None),
        )
        conn.commit()

    flash("Thank you for your feedback! 🌟", "success")
    return redirect(url_for("landing"))


@app.route("/kitchen-login", methods=["GET", "POST"])
def kitchen_login():
    if request.method == "POST":
        user = get_user(request.form.get("username", "").strip())
        password = request.form.get("password", "")
        if user and check_password(user["password"], password) and user["role"] in KITCHEN_ROLES:
            set_user_session(user)
            return redirect(url_for("kitchen"))
        flash("Invalid credentials", "error")

    return render_template("kitchen_login.html")


@app.route("/kitchen")
def kitchen():
    guard = require_kitchen()
    if guard:
        return guard
    return render_template("kitchen.html", username=session.get("username"))


@app.route("/update-order-status", methods=["POST"])
def update_order_status():
    if session.get("role") not in KITCHEN_ROLES:
        return jsonify({"error": "Unauthorized"}), 401

    order_id = request.form.get("order_id")
    status = request.form.get("status")
    if status not in ORDER_STATUSES:
        return jsonify({"error": "Invalid"}), 400

    with closing(db()) as conn:
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        conn.commit()

    return jsonify({"success": True})


@app.route("/kitchen-logout")
def kitchen_logout():
    session.clear()
    return redirect(url_for("kitchen_login"))


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        user = get_user(request.form.get("username", "").strip())
        password = request.form.get("password", "")
        if user and check_password(user["password"], password) and user["role"] == ADMIN_ROLE:
            set_user_session(user)
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials", "error")

    return render_template("admin_login.html")


@app.route("/admin-dashboard")
def admin_dashboard():
    guard = require_admin()
    if guard:
        return guard

    today = date.today().isoformat()
    with closing(db()) as conn:
        today_sales = conn.execute(
            "SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE DATE(created_at) = ? AND status = 'Served'",
            (today,),
        ).fetchone()[0]
        today_orders = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE DATE(created_at) = ?",
            (today,),
        ).fetchone()[0]
        active_kitchen = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status IN ('Preparing', 'Ready') AND payment_status = 'Paid'"
        ).fetchone()[0]
        pending_payments = conn.execute(
            "SELECT * FROM orders WHERE payment_status = 'Unpaid' ORDER BY created_at DESC"
        ).fetchall()
        recent_served = conn.execute(
            "SELECT * FROM orders WHERE status = 'Served' ORDER BY created_at DESC LIMIT 10"
        ).fetchall()

    return render_template(
        "admin_dashboard.html",
        today_sales=today_sales,
        today_orders=today_orders,
        active_kitchen=active_kitchen,
        pending_payments=pending_payments,
        recent_served=recent_served,
        username=session.get("username"),
    )


@app.route("/admin-food")
def admin_food():
    guard = require_admin()
    if guard:
        return guard

    items = fetch_all("SELECT * FROM food_items ORDER BY category, name")
    return render_template(
        "admin_food.html",
        items=items,
        categories=CATEGORIES,
        username=session.get("username"),
    )


@app.route("/admin-food/add", methods=["POST"])
def admin_food_add():
    guard = require_admin()
    if guard:
        return guard

    name = request.form.get("name", "").strip()
    category = request.form.get("category")
    price = request.form.get("price")
    available = 1 if request.form.get("available") == "1" else 0

    if name and category and price:
        with closing(db()) as conn:
            conn.execute(
                "INSERT INTO food_items (name, category, price, available) VALUES (?, ?, ?, ?)",
                (name, category, float(price), available),
            )
            conn.commit()
        flash("Food item added!", "success")

    return redirect(url_for("admin_food"))


@app.route("/admin-food/edit/<int:item_id>", methods=["POST"])
def admin_food_edit(item_id):
    guard = require_admin()
    if guard:
        return guard

    with closing(db()) as conn:
        conn.execute(
            "UPDATE food_items SET name = ?, category = ?, price = ?, available = ? WHERE id = ?",
            (
                request.form.get("name", "").strip(),
                request.form.get("category"),
                float(request.form.get("price")),
                1 if request.form.get("available") == "1" else 0,
                item_id,
            ),
        )
        conn.commit()

    flash("Food item updated!", "success")
    return redirect(url_for("admin_food"))


@app.route("/admin-food/delete/<int:item_id>", methods=["POST"])
def admin_food_delete(item_id):
    guard = require_admin()
    if guard:
        return guard

    with closing(db()) as conn:
        conn.execute("DELETE FROM food_items WHERE id = ?", (item_id,))
        conn.commit()

    flash("Food item deleted.", "success")
    return redirect(url_for("admin_food"))


@app.route("/admin-food/toggle/<int:item_id>", methods=["POST"])
def admin_food_toggle(item_id):
    if session.get("role") != ADMIN_ROLE:
        return jsonify({"error": "Unauthorized"}), 401

    with closing(db()) as conn:
        item = conn.execute(
            "SELECT available FROM food_items WHERE id = ?",
            (item_id,),
        ).fetchone()
        if not item:
            return jsonify({"error": "Not found"}), 404

        available = 0 if item["available"] else 1
        conn.execute(
            "UPDATE food_items SET available = ? WHERE id = ?",
            (available, item_id),
        )
        conn.commit()

    return jsonify({"success": True, "available": available})


@app.route("/admin-sales")
def admin_sales():
    guard = require_admin()
    if guard:
        return guard

    with closing(db()) as conn:
        orders = conn.execute(
            """
            SELECT o.*, GROUP_CONCAT(f.name || ' x' || oi.quantity, ', ') AS items
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN food_items f ON oi.food_id = f.id
            WHERE o.status = 'Served'
            GROUP BY o.id
            ORDER BY o.created_at DESC
            """
        ).fetchall()
        total_revenue = conn.execute(
            "SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status = 'Served'"
        ).fetchone()[0]

    return render_template(
        "admin_sales.html",
        orders=orders,
        total_revenue=total_revenue,
        username=session.get("username"),
    )


@app.route("/admin-sales/export-csv")
def export_csv():
    guard = require_admin()
    if guard:
        return guard

    orders = fetch_all(
        """
        SELECT o.id, o.customer_name, o.table_number, o.total_amount, o.created_at,
               GROUP_CONCAT(f.name || ' x' || oi.quantity, ', ') AS items
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        LEFT JOIN food_items f ON oi.food_id = f.id
        WHERE o.status = 'Served'
        GROUP BY o.id
        ORDER BY o.created_at DESC
        """
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Order #", "Customer", "Table", "Items", "Amount (KES)"])
    for order in orders:
        writer.writerow(
            [
                order["created_at"],
                order["id"],
                order["customer_name"],
                order["table_number"],
                order["items"],
                order["total_amount"],
            ]
        )

    response = make_response(buffer.getvalue())
    response.headers["Content-Disposition"] = (
        f"attachment; filename=nova_eatery_sales_{date.today().isoformat()}.csv"
    )
    response.headers["Content-Type"] = "text/csv"
    return response


@app.route("/admin-payment-confirmation")
def admin_payment_confirmation():
    guard = require_admin()
    if guard:
        return guard

    today = date.today().isoformat()
    with closing(db()) as conn:
        pending = conn.execute(
            "SELECT * FROM orders WHERE payment_status = 'Unpaid' ORDER BY created_at DESC"
        ).fetchall()
        confirmed = conn.execute(
            """
            SELECT o.*, p.confirmed_at
            FROM orders o
            JOIN payments p ON o.id = p.order_id
            WHERE DATE(p.confirmed_at) = ?
            ORDER BY p.confirmed_at DESC
            """,
            (today,),
        ).fetchall()

    return render_template(
        "admin_payment_confirmation.html",
        pending=pending,
        confirmed=confirmed,
        username=session.get("username"),
    )


@app.route("/admin-feedbacks")
def admin_feedbacks():
    guard = require_admin()
    if guard:
        return guard

    feedbacks = fetch_all(
        "SELECT feedbackid, rating, comment, created_at FROM feedback ORDER BY created_at DESC"
    )
    total_feedbacks = len(feedbacks)
    avg_rating = round(sum(item["rating"] for item in feedbacks) / total_feedbacks, 1) if total_feedbacks else 0
    rating_distribution = {rating: 0 for rating in range(1, 6)}
    for item in feedbacks:
        rating_distribution[item["rating"]] += 1

    return render_template(
        "admin_feedbacks.html",
        feedbacks=feedbacks,
        total_feedbacks=total_feedbacks,
        avg_rating=avg_rating,
        rating_distribution=rating_distribution,
        username=session.get("username"),
    )


@app.route("/confirm-payment/<int:order_id>", methods=["POST"])
def confirm_payment(order_id):
    guard = require_admin()
    if guard:
        return guard

    with closing(db()) as conn:
        conn.execute("UPDATE orders SET payment_status = 'Paid' WHERE id = ?", (order_id,))
        conn.execute(
            "INSERT INTO payments (order_id, confirmed_by, confirmed_at) VALUES (?, ?, datetime('now'))",
            (order_id, session.get("user_id")),
        )
        conn.commit()

    flash("Payment confirmed! Order sent to kitchen. ✅", "success")
    return redirect(request.referrer or url_for("admin_dashboard"))


@app.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/api/orders")
def api_orders():
    if session.get("role") not in KITCHEN_ROLES:
        return jsonify({"error": "Unauthorized"}), 401

    with closing(db()) as conn:
        orders = conn.execute(
            """
            SELECT id, customer_name, phone_number, table_number, total_amount, status, created_at
            FROM orders
            WHERE payment_status = 'Paid' AND status NOT IN ('Served', 'Cancelled')
            ORDER BY created_at DESC
            """
        ).fetchall()

        data = []
        for order in orders:
            items = conn.execute(
                """
                SELECT f.name, oi.quantity AS qty
                FROM order_items oi
                JOIN food_items f ON oi.food_id = f.id
                WHERE oi.order_id = ?
                """,
                (order["id"],),
            ).fetchall()
            data.append(
                {
                    "id": order["id"],
                    "customer_name": order["customer_name"],
                    "phone_number": order["phone_number"],
                    "table_number": order["table_number"],
                    "total_amount": order["total_amount"],
                    "status": order["status"],
                    "created_at": order["created_at"],
                    "items": [{"name": item["name"], "qty": item["qty"]} for item in items],
                }
            )

    return jsonify(data)


@app.route("/api/order-status/<int:order_id>")
def api_order_status(order_id):
    order = fetch_one(
        "SELECT id, status, payment_status FROM orders WHERE id = ?",
        (order_id,),
    )
    if not order:
        return jsonify({"error": "Not found"}), 404

    return jsonify(
        {
            "id": order["id"],
            "status": order["status"],
            "payment_status": order["payment_status"],
        }
    )


@app.route("/api/my-orders")
def api_my_orders():
    phone = request.args.get("phone", "").strip()
    if not phone:
        return jsonify([])

    orders = fetch_all(
        "SELECT * FROM orders WHERE phone_number = ? ORDER BY created_at DESC",
        (phone,),
    )
    return jsonify(
        [
            {
                "id": order["id"],
                "table_number": order["table_number"],
                "total_amount": order["total_amount"],
                "status": order["status"],
                "created_at": order["created_at"],
            }
            for order in orders
        ]
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
