from flask import Flask, jsonify, request
from flask_cors import CORS
import MySQLdb
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt
)

# ===== טעינת קובץ הסביבה =====
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ===== JWT Secret =====
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET", "CHANGE_ME_PLEASE")
jwt = JWTManager(app)

# ===== חיבור ל-MySQL =====
db = MySQLdb.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    passwd=os.getenv("MYSQL_PASSWORD"),
    db=os.getenv("MYSQL_DB"),
    port=int(os.getenv("MYSQL_PORT", "3306")),
    charset="utf8mb4",
    use_unicode=True,
)
cursor = db.cursor()

# ===== Helper: בדיקת תפקיד מנהל =====


def require_admin():
    claims = get_jwt()
    role = claims.get("role")
    return role == "admin"

# ---------------------------
#      AUTH (Login / Users)
# ---------------------------


@app.route("/api/auth/register", methods=["POST"])
def register_user():
    """רישום משתמש רגיל (role=user)."""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email & password required"}), 400

    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        return jsonify({"error": "user already exists"}), 409

    password_hash = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s)",
        (email, password_hash, "user"),
    )
    db.commit()
    return jsonify({"message": "user created"}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email & password required"}), 400

    cursor.execute(
        "SELECT id, password_hash, role FROM users WHERE email=%s", (email,))
    row = cursor.fetchone()
    if not row:
        return jsonify({"error": "wrong email or password"}), 401

    user_id, password_hash, role = row[0], row[1], row[2]
    if not check_password_hash(password_hash, password):
        return jsonify({"error": "wrong email or password"}), 401

    token = create_access_token(identity=str(
        user_id), additional_claims={"role": role})
    return jsonify({"access_token": token, "role": role}), 200


# ---------------------------
#        PRODUCTS API
# ---------------------------

@app.route("/api/products", methods=["GET"])
def get_products():
    cursor.execute("SELECT id, name, description, price, category, image_url FROM products")
    products = cursor.fetchall()
    result = []
    for p in products:
        result.append({
            "id": p[0],
            "name": p[1],
            "description": p[2],
            "price": float(p[3]),
            "category": p[4],
            "image_url": p[5],  # יכול להיות None
        })
    return jsonify(result), 200

@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """
    מחזיר מוצר בודד לפי מזהה (ID).
    דוגמה: GET /api/products/3
    אם אין מוצר כזה -> 404.
    """
    # שאילתא בטוחה עם פרמטרים (מונעת SQL Injection)
    cursor.execute(
        "SELECT id, name, description, price, category, image_url FROM products WHERE id=%s",
        (product_id,),
    )
    row = cursor.fetchone()

    if not row:
        return jsonify({"error": "Product not found"}), 404

    product = {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "price": float(row[3]),
        "category": row[4],
        "image_url": row[5],
    }
    return jsonify(product), 200


@app.route("/api/products", methods=["POST"])
@jwt_required()
def add_product():
    if not require_admin():
        return jsonify({"error": "admin only"}), 403

    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    price = data.get("price")
    category = data.get("category", "כללי")
    image_url = data.get("image_url")  # אופציונלי

    if not name or not description or price is None:
        return jsonify({"error": "Missing required fields"}), 400

    cursor.execute(
        "INSERT INTO products (name, description, price, category, image_url) VALUES (%s, %s, %s, %s, %s)",
        (name, description, price, category, image_url),
    )
    db.commit()
    return jsonify({"message": "Product added successfully"}), 201

@app.route("/api/products/<int:product_id>", methods=["PUT"])
@jwt_required()
def update_product(product_id):
    if not require_admin():
        return jsonify({"error": "admin only"}), 403

    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    price = data.get("price")
    category = data.get("category", "כללי")
    image_url = data.get("image_url")  # אופציונלי

    if not name or not description or price is None:
        return jsonify({"error": "Missing required fields"}), 400

    cursor.execute(
        "UPDATE products SET name=%s, description=%s, price=%s, category=%s, image_url=%s WHERE id=%s",
        (name, description, price, category, image_url, product_id),
    )
    db.commit()
    return jsonify({"message": "Product updated successfully"}), 200

@app.route("/api/products/<int:product_id>", methods=["DELETE"])
@jwt_required()
def delete_product(product_id):
    if not require_admin():
        return jsonify({"error": "admin only"}), 403

    try:
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        db.commit()
        return jsonify({"message": "Product deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------
#          LEADS API
# ---------------------------

@app.route("/api/leads", methods=["POST"])
def add_lead():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    if not name or not email:
        return jsonify({"error": "name & email required"}), 400

    cursor.execute(
        "INSERT INTO leads (name, email, message) VALUES (%s, %s, %s)",
        (name, email, message),
    )
    db.commit()
    return jsonify({"message": "Lead added successfully"}), 201


@app.route("/api/admin/leads", methods=["GET"])
@jwt_required()
def admin_get_leads():
    if not require_admin():
        return jsonify({"error": "admin only"}), 403

    cursor.execute(
        "SELECT id, name, email, message, created_at FROM leads ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    leads = []
    for r in rows:
        leads.append({
            "id": r[0],
            "name": r[1],
            "email": r[2],
            "message": r[3],
            "created_at": r[4].strftime("%Y-%m-%d %H:%M:%S"),
        })
    return jsonify(leads), 200



# ---------------------------
#        RUN SERVER
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

