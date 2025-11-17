import os
import MySQLdb
from dotenv import load_dotenv

# טוען את .env (כמו ב-app.py)
load_dotenv()

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

# ===== יצירת טבלת users =====
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
""")

# ===== יצירת טבלת products =====
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(255) DEFAULT 'כללי',
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
""")

# ===== יצירת טבלת leads =====
cursor.execute("""
CREATE TABLE IF NOT EXISTS leads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
""")

db.commit()
db.close()

print("✅ Tables users, products, leads created (or already existed).")
