"""
Database module untuk Aplikasi Kasir Depo Air
Mengelola semua operasi database SQLite
"""

import sqlite3
import hashlib
import os
from datetime import datetime, timedelta


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "depo_air.db")


def get_connection():
    """Mendapatkan koneksi database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password):
    """Hash password dengan SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def init_database():
    """Inisialisasi database dan tabel-tabel"""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabel Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('owner', 'kasir')),
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabel Products
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'Galon',
            buy_price REAL DEFAULT 0,
            sell_price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            unit TEXT DEFAULT 'pcs',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabel Customers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            debt_amount REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabel Transactions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            customer_id INTEGER,
            user_id INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            discount REAL DEFAULT 0,
            total REAL NOT NULL,
            paid_amount REAL DEFAULT 0,
            change_amount REAL DEFAULT 0,
            payment_method TEXT DEFAULT 'cash' CHECK(payment_method IN ('cash', 'hutang')),
            status TEXT DEFAULT 'completed' CHECK(status IN ('completed', 'pending', 'cancelled')),
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Tabel Transaction Items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaction_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # Tabel Expenses
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL CHECK(category IN ('supplier', 'peralatan', 'lainnya')),
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            expense_date DATE NOT NULL,
            user_id INTEGER NOT NULL,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Tabel Debt Payments (Pembayaran Hutang)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS debt_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Tabel Delivery Fees (Biaya Antar Kurir)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS delivery_fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            courier_name TEXT NOT NULL DEFAULT 'Kurir',
            customer_name TEXT DEFAULT '',
            delivery_fee REAL NOT NULL DEFAULT 2000,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'collected', 'settled')),
            collected_at TIMESTAMP,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE
        )
    """)

    # Tabel Courier Settlements (Serah Terima Uang Kurir)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courier_settlements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            courier_name TEXT NOT NULL,
            total_deliveries INTEGER NOT NULL DEFAULT 0,
            total_amount REAL NOT NULL DEFAULT 0,
            settlement_date DATE NOT NULL,
            user_id INTEGER NOT NULL,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Tabel Water Meters (Pencatatan Kilometer Air / Flow Meter)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_meters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_date DATE NOT NULL,
            shift_name TEXT NOT NULL DEFAULT 'Harian',
            user_id INTEGER,
            user_name TEXT DEFAULT '',
            bio_meter_start REAL NOT NULL DEFAULT 0,
            bio_meter_end REAL NOT NULL DEFAULT 0,
            bio_liters REAL NOT NULL DEFAULT 0,
            bio_liters_per_gallon REAL NOT NULL DEFAULT 21.5,
            bio_gallons REAL NOT NULL DEFAULT 0,
            bio_price_per_gallon REAL NOT NULL DEFAULT 5000,
            bio_revenue REAL NOT NULL DEFAULT 0,
            ro_meter_start REAL NOT NULL DEFAULT 0,
            ro_meter_end REAL NOT NULL DEFAULT 0,
            ro_liters REAL NOT NULL DEFAULT 0,
            ro_liters_per_gallon REAL NOT NULL DEFAULT 20.5,
            ro_gallons REAL NOT NULL DEFAULT 0,
            ro_price_per_gallon REAL NOT NULL DEFAULT 10000,
            ro_revenue REAL NOT NULL DEFAULT 0,
            total_liters REAL NOT NULL DEFAULT 0,
            total_gallons REAL NOT NULL DEFAULT 0,
            total_revenue REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'closed' CHECK(status IN ('open', 'closed')),
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Tambahkan kolom delivery_fee ke tabel transactions jika belum ada
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN delivery_fee REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Kolom sudah ada

    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN is_delivery INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Kolom sudah ada

    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN courier_name TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # Kolom sudah ada

    # Insert default users jika belum ada
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            ("owner", hash_password("owner123"), "Pemilik Depo", "owner")
        )
        cursor.execute(
            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            ("kasir", hash_password("kasir123"), "Kasir Depo", "kasir")
        )

    # Insert sample products jika belum ada
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ("Isi Ulang Air Bio Energi", "Galon", 1000, 5000, 999, "galon"),
            ("Isi Ulang Air RO (Reverse Osmosis)", "Galon", 2000, 10000, 999, "galon"),
            ("Galon Aqua", "Galon", 15000, 20000, 50, "galon"),
            ("Galon Le Minerale", "Galon", 14000, 18000, 40, "galon"),
            ("Galon Vit", "Galon", 13000, 17000, 30, "galon"),
            ("Galon Club", "Galon", 12000, 16000, 35, "galon"),
            ("Galon Cleo", "Galon", 14000, 19000, 25, "galon"),
            ("Air Minum 600ml", "Botol", 2000, 3000, 100, "botol"),
            ("Air Minum 1500ml", "Botol", 3000, 5000, 80, "botol"),
        ]
        cursor.executemany(
            "INSERT INTO products (name, category, buy_price, sell_price, stock, unit) VALUES (?, ?, ?, ?, ?, ?)",
            sample_products
        )
    else:
        # Pastikan produk Air Bio dan Air RO selalu tersedia
        cursor.execute("SELECT id FROM products WHERE name LIKE '%Bio%'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO products (name, category, buy_price, sell_price, stock, unit) VALUES (?, ?, ?, ?, ?, ?)",
                ("Isi Ulang Air Bio Energi", "Galon", 1000, 5000, 999, "galon")
            )
        cursor.execute("SELECT id FROM products WHERE name LIKE '%RO%' OR name LIKE '%Reverse Osmosis%'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO products (name, category, buy_price, sell_price, stock, unit) VALUES (?, ?, ?, ?, ?, ?)",
                ("Isi Ulang Air RO (Reverse Osmosis)", "Galon", 2000, 10000, 999, "galon")
            )

    # Insert sample water meter records jika tabel masih kosong (dari data riil catatan Excel user)
    cursor.execute("SELECT COUNT(*) FROM water_meters")
    if cursor.fetchone()[0] == 0:
        sample_meters = [
            ('2026-10-07', 'Harian', 1, 'Kasir Depo', 9252.2, 12975.8, 3723.6, 21.5, 173.19, 5000, 865950, 9006.5, 9673.7, 667.2, 20.5, 32.55, 10000, 325500, 4390.8, 205.74, 1191450, 'closed', 'Catatan Excel Rabu'),
            ('2026-10-08', 'Harian', 1, 'Kasir Depo', 2975.8, 5172.1, 2196.3, 21.5, 102.15, 5000, 510750, 9673.7, 10301.76, 628.06, 20.5, 30.64, 10000, 306400, 2824.36, 132.79, 817150, 'closed', 'Catatan Excel Kamis'),
            ('2026-10-09', 'Harian', 1, 'Kasir Depo', 5172.1, 8414.2, 3242.1, 21.5, 150.79, 5000, 753950, 301.76, 810.25, 508.49, 20.5, 24.80, 10000, 248000, 3750.59, 175.59, 1001950, 'closed', 'Catatan Excel Jumat'),
            ('2026-10-10', 'Harian', 1, 'Kasir Depo', 8414.2, 10804.2, 2390.0, 21.5, 111.16, 5000, 555800, 810.25, 1523.6, 713.35, 20.5, 34.80, 10000, 348000, 3103.35, 145.96, 903800, 'closed', 'Catatan Excel Sabtu'),
            ('2026-10-11', 'Harian', 1, 'Kasir Depo', 804.2, 3855.7, 3051.5, 21.5, 141.93, 5000, 709650, 1523.6, 2196.8, 673.2, 20.5, 32.84, 10000, 328400, 3724.7, 174.77, 1038050, 'closed', 'Catatan Excel Minggu'),
            ('2026-10-12', 'Harian', 1, 'Kasir Depo', 3855.7, 7233.6, 3377.9, 21.5, 157.11, 5000, 785550, 2196.8, 2744.5, 547.7, 20.5, 26.72, 10000, 267200, 3925.6, 183.83, 1052750, 'closed', 'Catatan Excel Senin'),
        ]
        cursor.executemany("""
            INSERT INTO water_meters (
                record_date, shift_name, user_id, user_name,
                bio_meter_start, bio_meter_end, bio_liters, bio_liters_per_gallon, bio_gallons, bio_price_per_gallon, bio_revenue,
                ro_meter_start, ro_meter_end, ro_liters, ro_liters_per_gallon, ro_gallons, ro_price_per_gallon, ro_revenue,
                total_liters, total_gallons, total_revenue, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_meters)

    conn.commit()
    conn.close()


# ==================== USER OPERATIONS ====================

def authenticate_user(username, password):
    """Autentikasi user, mengembalikan dict user atau None"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password_hash = ? AND is_active = 1",
        (username, hash_password(password))
    )
    user = cursor.fetchone()
    conn.close()
    if user:
        return dict(user)
    return None


def get_all_users(role=None):
    """Mengambil semua user, opsional filter berdasarkan role"""
    conn = get_connection()
    cursor = conn.cursor()
    if role:
        cursor.execute("SELECT * FROM users WHERE role = ? ORDER BY full_name", (role,))
    else:
        cursor.execute("SELECT * FROM users ORDER BY role, full_name")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users


def get_user_by_id(user_id):
    """Mengambil user berdasarkan ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def add_user(username, password, full_name, role='kasir'):
    """Menambah user baru (registrasi kasir)"""
    conn = get_connection()
    cursor = conn.cursor()
    # Cek username unik
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return None, "Username sudah digunakan!"
    cursor.execute(
        "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
        (username, hash_password(password), full_name, role)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id, "Berhasil"


def update_user(user_id, full_name, username):
    """Update data user"""
    conn = get_connection()
    cursor = conn.cursor()
    # Cek username unik (selain dirinya sendiri)
    cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (username, user_id))
    if cursor.fetchone():
        conn.close()
        return False, "Username sudah digunakan!"
    cursor.execute(
        "UPDATE users SET full_name = ?, username = ? WHERE id = ?",
        (full_name, username, user_id)
    )
    conn.commit()
    conn.close()
    return True, "Berhasil"


def update_user_password(user_id, new_password):
    """Update password user"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(new_password), user_id)
    )
    conn.commit()
    conn.close()


def toggle_user_active(user_id):
    """Aktifkan/nonaktifkan user"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_active FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        new_status = 0 if row['is_active'] else 1
        cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
        conn.commit()
    conn.close()


# ==================== PRODUCT OPERATIONS ====================

def get_all_products(active_only=True):
    """Mengambil semua produk"""
    conn = get_connection()
    cursor = conn.cursor()
    if active_only:
        cursor.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY name")
    else:
        cursor.execute("SELECT * FROM products ORDER BY name")
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products


def get_product_by_id(product_id):
    """Mengambil produk berdasarkan ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return dict(product) if product else None


def add_product(name, category, buy_price, sell_price, stock, unit):
    """Menambah produk baru"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, category, buy_price, sell_price, stock, unit) VALUES (?, ?, ?, ?, ?, ?)",
        (name, category, buy_price, sell_price, stock, unit)
    )
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    return product_id


def update_product(product_id, name, category, buy_price, sell_price, stock, unit):
    """Update produk"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE products SET name=?, category=?, buy_price=?, sell_price=?, stock=?, unit=?,
           updated_at=CURRENT_TIMESTAMP WHERE id=?""",
        (name, category, buy_price, sell_price, stock, unit, product_id)
    )
    conn.commit()
    conn.close()


def delete_product(product_id):
    """Soft delete produk"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


def update_stock(product_id, quantity_change):
    """Update stok produk (positif = tambah, negatif = kurang)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE products SET stock = stock + ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (quantity_change, product_id)
    )
    conn.commit()
    conn.close()


# ==================== CUSTOMER OPERATIONS ====================

def get_all_customers(active_only=True):
    """Mengambil semua pelanggan"""
    conn = get_connection()
    cursor = conn.cursor()
    if active_only:
        cursor.execute("SELECT * FROM customers WHERE is_active = 1 ORDER BY name")
    else:
        cursor.execute("SELECT * FROM customers ORDER BY name")
    customers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return customers


def get_customer_by_id(customer_id):
    """Mengambil pelanggan berdasarkan ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    customer = cursor.fetchone()
    conn.close()
    return dict(customer) if customer else None


def add_customer(name, phone, address):
    """Menambah pelanggan baru"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)",
        (name, phone, address)
    )
    conn.commit()
    customer_id = cursor.lastrowid
    conn.close()
    return customer_id


def update_customer(customer_id, name, phone, address):
    """Update pelanggan"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE customers SET name=?, phone=?, address=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (name, phone, address, customer_id)
    )
    conn.commit()
    conn.close()


def delete_customer(customer_id):
    """Soft delete pelanggan"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE customers SET is_active = 0 WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()


def update_customer_debt(customer_id, amount_change):
    """Update hutang pelanggan (positif = tambah hutang, negatif = bayar hutang)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE customers SET debt_amount = debt_amount + ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (amount_change, customer_id)
    )
    conn.commit()
    conn.close()


def add_debt_payment(customer_id, amount, user_id, notes=""):
    """Catat pembayaran hutang"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO debt_payments (customer_id, amount, user_id, notes) VALUES (?, ?, ?, ?)",
        (customer_id, amount, user_id, notes)
    )
    update_customer_debt(customer_id, -amount)
    conn.commit()
    conn.close()


def get_debt_payments(customer_id):
    """Mengambil riwayat pembayaran hutang pelanggan"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT dp.*, u.full_name as user_name
           FROM debt_payments dp
           JOIN users u ON dp.user_id = u.id
           WHERE dp.customer_id = ?
           ORDER BY dp.created_at DESC""",
        (customer_id,)
    )
    payments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return payments


# ==================== TRANSACTION OPERATIONS ====================

def generate_invoice_number():
    """Generate nomor invoice unik"""
    now = datetime.now()
    prefix = now.strftime("INV%Y%m%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM transactions WHERE invoice_number LIKE ?",
        (f"{prefix}%",)
    )
    count = cursor.fetchone()[0] + 1
    conn.close()
    return f"{prefix}{count:04d}"


def create_transaction(customer_id, user_id, items, payment_method, paid_amount, discount=0, notes="",
                       is_delivery=False, courier_name="", delivery_fee=2000):
    """
    Buat transaksi baru
    items: list of dict {'product_id', 'quantity', 'unit_price'}
    is_delivery: True jika pesanan diantar
    courier_name: nama kurir pengantar
    delivery_fee: biaya antar (default Rp 2.000)
    """
    conn = get_connection()
    cursor = conn.cursor()

    invoice = generate_invoice_number()
    subtotal = sum(item['quantity'] * item['unit_price'] for item in items)
    actual_delivery_fee = delivery_fee if is_delivery else 0
    total = subtotal - discount + actual_delivery_fee
    change_amount = max(0, paid_amount - total) if payment_method == 'cash' else 0

    cursor.execute(
        """INSERT INTO transactions
           (invoice_number, customer_id, user_id, subtotal, discount, total,
            paid_amount, change_amount, payment_method, status, notes,
            delivery_fee, is_delivery, courier_name)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?, ?, ?, ?)""",
        (invoice, customer_id, user_id, subtotal, discount, total,
         paid_amount, change_amount, payment_method, notes,
         actual_delivery_fee, 1 if is_delivery else 0, courier_name)
    )
    transaction_id = cursor.lastrowid

    for item in items:
        product = get_product_by_id(item['product_id'])
        cursor.execute(
            """INSERT INTO transaction_items
               (transaction_id, product_id, product_name, quantity, unit_price, subtotal)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (transaction_id, item['product_id'], product['name'],
             item['quantity'], item['unit_price'],
             item['quantity'] * item['unit_price'])
        )
        # Kurangi stok
        cursor.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ?",
            (item['quantity'], item['product_id'])
        )

    # Jika hutang, tambahkan ke hutang pelanggan (termasuk delivery fee)
    if payment_method == 'hutang' and customer_id:
        cursor.execute(
            "UPDATE customers SET debt_amount = debt_amount + ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (total, customer_id)
        )

    # Catat delivery fee untuk kurir
    if is_delivery and courier_name:
        customer = get_customer_by_id(customer_id) if customer_id else None
        cust_name = customer['name'] if customer else 'Umum'
        cursor.execute(
            """INSERT INTO delivery_fees
               (transaction_id, courier_name, customer_name, delivery_fee, status)
               VALUES (?, ?, ?, ?, 'pending')""",
            (transaction_id, courier_name, cust_name, actual_delivery_fee)
        )

    conn.commit()
    conn.close()
    return transaction_id, invoice


def get_transactions(start_date=None, end_date=None, limit=100):
    """Mengambil daftar transaksi"""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT t.*, u.full_name as kasir_name,
               COALESCE(c.name, 'Umum') as customer_name
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        LEFT JOIN customers c ON t.customer_id = c.id
        WHERE 1=1
    """
    params = []

    if start_date:
        query += " AND DATE(t.created_at) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND DATE(t.created_at) <= ?"
        params.append(end_date)

    query += " ORDER BY t.created_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    transactions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return transactions


def get_transaction_items(transaction_id):
    """Mengambil item-item transaksi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transaction_items WHERE transaction_id = ?",
        (transaction_id,)
    )
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return items


def get_transaction_by_invoice(invoice_number):
    """Mengambil transaksi berdasarkan nomor invoice beserta items"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT t.*, u.full_name as kasir_name,
                  COALESCE(c.name, 'Umum') as customer_name
           FROM transactions t
           JOIN users u ON t.user_id = u.id
           LEFT JOIN customers c ON t.customer_id = c.id
           WHERE t.invoice_number = ?""",
        (invoice_number,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    trx = dict(row)
    cursor.execute("SELECT * FROM transaction_items WHERE transaction_id = ?", (trx['id'],))
    trx['items'] = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return trx


# ==================== EXPENSE OPERATIONS ====================

def get_all_expenses(start_date=None, end_date=None):
    """Mengambil semua pengeluaran"""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT e.*, u.full_name as user_name
        FROM expenses e
        JOIN users u ON e.user_id = u.id
        WHERE 1=1
    """
    params = []

    if start_date:
        query += " AND e.expense_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND e.expense_date <= ?"
        params.append(end_date)

    query += " ORDER BY e.expense_date DESC, e.created_at DESC"
    cursor.execute(query, params)
    expenses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return expenses


def add_expense(category, description, amount, expense_date, user_id, notes=""):
    """Menambah pengeluaran"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (category, description, amount, expense_date, user_id, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (category, description, amount, expense_date, user_id, notes)
    )
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    return expense_id


def update_expense(expense_id, category, description, amount, expense_date, notes=""):
    """Update pengeluaran"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE expenses SET category=?, description=?, amount=?, expense_date=?, notes=? WHERE id=?",
        (category, description, amount, expense_date, notes, expense_id)
    )
    conn.commit()
    conn.close()


def delete_expense(expense_id):
    """Hapus pengeluaran"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()


# ==================== REPORT / DASHBOARD OPERATIONS ====================

def get_dashboard_stats():
    """Mengambil statistik untuk dashboard"""
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")

    # Penjualan hari ini
    cursor.execute(
        "SELECT COALESCE(SUM(total), 0) FROM transactions WHERE DATE(created_at) = ? AND status = 'completed'",
        (today,)
    )
    today_sales = cursor.fetchone()[0]

    # Jumlah transaksi hari ini
    cursor.execute(
        "SELECT COUNT(*) FROM transactions WHERE DATE(created_at) = ? AND status = 'completed'",
        (today,)
    )
    today_transactions = cursor.fetchone()[0]

    # Total hutang pelanggan
    cursor.execute("SELECT COALESCE(SUM(debt_amount), 0) FROM customers WHERE is_active = 1")
    total_debt = cursor.fetchone()[0]

    # Pengeluaran hari ini
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE expense_date = ?",
        (today,)
    )
    today_expenses = cursor.fetchone()[0]

    # Total produk
    cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
    total_products = cursor.fetchone()[0]

    # Total pelanggan
    cursor.execute("SELECT COUNT(*) FROM customers WHERE is_active = 1")
    total_customers = cursor.fetchone()[0]

    # Penjualan bulan ini
    month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT COALESCE(SUM(total), 0) FROM transactions WHERE DATE(created_at) >= ? AND status = 'completed'",
        (month_start,)
    )
    month_sales = cursor.fetchone()[0]

    # Pengeluaran bulan ini
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE expense_date >= ?",
        (month_start,)
    )
    month_expenses = cursor.fetchone()[0]

    # Stok rendah (< 10)
    cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1 AND stock < 10")
    low_stock_count = cursor.fetchone()[0]

    conn.close()

    return {
        'today_sales': today_sales,
        'today_transactions': today_transactions,
        'total_debt': total_debt,
        'today_expenses': today_expenses,
        'total_products': total_products,
        'total_customers': total_customers,
        'month_sales': month_sales,
        'month_expenses': month_expenses,
        'low_stock_count': low_stock_count,
    }


def get_sales_report(period='daily', start_date=None, end_date=None):
    """
    Mengambil laporan penjualan berdasarkan periode
    period: 'daily', 'weekly', 'monthly', 'yearly'
    """
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()

    if not start_date:
        if period == 'daily':
            start_date = now.strftime("%Y-%m-%d")
            end_date = start_date
        elif period == 'weekly':
            start_date = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
        elif period == 'monthly':
            start_date = now.replace(day=1).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
        elif period == 'yearly':
            start_date = now.replace(month=1, day=1).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")

    # Total penjualan
    cursor.execute(
        """SELECT COALESCE(SUM(total), 0), COUNT(*)
           FROM transactions
           WHERE DATE(created_at) BETWEEN ? AND ? AND status = 'completed'""",
        (start_date, end_date)
    )
    row = cursor.fetchone()
    total_sales = row[0]
    total_count = row[1]

    # Total pengeluaran
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE expense_date BETWEEN ? AND ?",
        (start_date, end_date)
    )
    total_expenses = cursor.fetchone()[0]

    # Detail transaksi
    cursor.execute(
        """SELECT t.*, u.full_name as kasir_name,
                  COALESCE(c.name, 'Umum') as customer_name
           FROM transactions t
           JOIN users u ON t.user_id = u.id
           LEFT JOIN customers c ON t.customer_id = c.id
           WHERE DATE(t.created_at) BETWEEN ? AND ? AND t.status = 'completed'
           ORDER BY t.created_at DESC""",
        (start_date, end_date)
    )
    transactions = [dict(row) for row in cursor.fetchall()]

    # Penjualan per hari (untuk grafik)
    cursor.execute(
        """SELECT DATE(created_at) as sale_date, SUM(total) as daily_total
           FROM transactions
           WHERE DATE(created_at) BETWEEN ? AND ? AND status = 'completed'
           GROUP BY DATE(created_at)
           ORDER BY sale_date""",
        (start_date, end_date)
    )
    daily_sales = [dict(row) for row in cursor.fetchall()]

    # Produk terlaris
    cursor.execute(
        """SELECT ti.product_name, SUM(ti.quantity) as total_qty, SUM(ti.subtotal) as total_revenue
           FROM transaction_items ti
           JOIN transactions t ON ti.transaction_id = t.id
           WHERE DATE(t.created_at) BETWEEN ? AND ? AND t.status = 'completed'
           GROUP BY ti.product_name
           ORDER BY total_qty DESC
           LIMIT 10""",
        (start_date, end_date)
    )
    top_products = [dict(row) for row in cursor.fetchall()]

    # Detail pengeluaran per kategori
    cursor.execute(
        """SELECT category, SUM(amount) as total
           FROM expenses
           WHERE expense_date BETWEEN ? AND ?
           GROUP BY category""",
        (start_date, end_date)
    )
    expense_by_category = [dict(row) for row in cursor.fetchall()]

    # Detail pengeluaran individual
    cursor.execute(
        """SELECT e.*, u.full_name as user_name
           FROM expenses e
           JOIN users u ON e.user_id = u.id
           WHERE e.expense_date BETWEEN ? AND ?
           ORDER BY e.expense_date DESC, e.created_at DESC""",
        (start_date, end_date)
    )
    expenses = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        'start_date': start_date,
        'end_date': end_date,
        'period': period,
        'total_sales': total_sales,
        'total_count': total_count,
        'total_expenses': total_expenses,
        'net_profit': total_sales - total_expenses,
        'transactions': transactions,
        'daily_sales': daily_sales,
        'top_products': top_products,
        'expense_by_category': expense_by_category,
        'expenses': expenses,
    }


def get_recent_transactions(limit=5):
    """Mengambil transaksi terbaru untuk dashboard"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT t.invoice_number, COALESCE(c.name, 'Umum') as customer_name,
                  t.total, t.payment_method, t.created_at
           FROM transactions t
           LEFT JOIN customers c ON t.customer_id = c.id
           WHERE t.status = 'completed'
           ORDER BY t.created_at DESC LIMIT ?""",
        (limit,)
    )
    transactions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return transactions


def get_low_stock_products(threshold=10):
    """Mengambil produk dengan stok rendah"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM products WHERE is_active = 1 AND stock < ? ORDER BY stock ASC",
        (threshold,)
    )
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products


# ==================== DELIVERY / COURIER OPERATIONS ====================

def get_delivery_fees(courier_name=None, status=None, start_date=None, end_date=None):
    """Mengambil daftar biaya antar kurir"""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT df.*, t.invoice_number, t.created_at as transaction_date
        FROM delivery_fees df
        JOIN transactions t ON df.transaction_id = t.id
        WHERE 1=1
    """
    params = []

    if courier_name:
        query += " AND df.courier_name = ?"
        params.append(courier_name)
    if status:
        query += " AND df.status = ?"
        params.append(status)
    if start_date:
        query += " AND DATE(df.created_at) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND DATE(df.created_at) <= ?"
        params.append(end_date)

    query += " ORDER BY df.created_at DESC"
    cursor.execute(query, params)
    fees = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return fees


def get_courier_summary():
    """Mengambil ringkasan per kurir: total antaran, pending, dan sudah diambil"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT courier_name,
               COUNT(*) as total_deliveries,
               SUM(delivery_fee) as total_fee,
               SUM(CASE WHEN status = 'pending' THEN delivery_fee ELSE 0 END) as pending_amount,
               SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
               SUM(CASE WHEN status = 'collected' THEN delivery_fee ELSE 0 END) as collected_amount,
               SUM(CASE WHEN status = 'collected' THEN 1 ELSE 0 END) as collected_count,
               SUM(CASE WHEN status = 'settled' THEN delivery_fee ELSE 0 END) as settled_amount,
               SUM(CASE WHEN status = 'settled' THEN 1 ELSE 0 END) as settled_count
        FROM delivery_fees
        GROUP BY courier_name
        ORDER BY courier_name
    """)
    summary = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return summary


def mark_delivery_collected(delivery_id):
    """Tandai delivery fee sudah diambil kurir (langsung ambil)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE delivery_fees SET status = 'collected', collected_at = CURRENT_TIMESTAMP WHERE id = ?",
        (delivery_id,)
    )
    conn.commit()
    conn.close()


def mark_delivery_collected_bulk(courier_name):
    """Tandai semua delivery fee pending milik kurir sebagai collected"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE delivery_fees SET status = 'collected', collected_at = CURRENT_TIMESTAMP WHERE courier_name = ? AND status = 'pending'",
        (courier_name,)
    )
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected


def settle_courier(courier_name, user_id, notes=""):
    """
    Selesaikan serah terima uang kurir (kurir menyerahkan semua uang antar yang dikumpulkan).
    Semua fee 'collected' dipindah ke 'settled'.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Hitung total yang collected
    cursor.execute(
        "SELECT COUNT(*) as cnt, COALESCE(SUM(delivery_fee), 0) as total FROM delivery_fees WHERE courier_name = ? AND status = 'collected'",
        (courier_name,)
    )
    row = cursor.fetchone()
    count = row[0]
    total = row[1]

    if count == 0:
        conn.close()
        return 0, 0

    # Update status ke settled
    cursor.execute(
        "UPDATE delivery_fees SET status = 'settled' WHERE courier_name = ? AND status = 'collected'",
        (courier_name,)
    )

    # Catat settlement
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        """INSERT INTO courier_settlements
           (courier_name, total_deliveries, total_amount, settlement_date, user_id, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (courier_name, count, total, today, user_id, notes)
    )

    conn.commit()
    conn.close()
    return count, total


def get_courier_settlements(courier_name=None, limit=50):
    """Mengambil riwayat serah terima uang kurir"""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT cs.*, u.full_name as user_name
        FROM courier_settlements cs
        JOIN users u ON cs.user_id = u.id
        WHERE 1=1
    """
    params = []
    if courier_name:
        query += " AND cs.courier_name = ?"
        params.append(courier_name)
    query += " ORDER BY cs.created_at DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    settlements = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return settlements


def get_all_courier_names():
    """Mengambil semua nama kurir yang pernah tercatat"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT courier_name FROM delivery_fees ORDER BY courier_name")
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return names


def get_delivery_stats():
    """Statistik delivery untuk dashboard"""
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")

    # Total pending semua kurir
    cursor.execute("SELECT COALESCE(SUM(delivery_fee), 0), COUNT(*) FROM delivery_fees WHERE status = 'pending'")
    row = cursor.fetchone()
    pending_total = row[0]
    pending_count = row[1]

    # Total collected (belum diserahkan)
    cursor.execute("SELECT COALESCE(SUM(delivery_fee), 0), COUNT(*) FROM delivery_fees WHERE status = 'collected'")
    row = cursor.fetchone()
    collected_total = row[0]
    collected_count = row[1]

    # Delivery hari ini
    cursor.execute("SELECT COALESCE(SUM(delivery_fee), 0), COUNT(*) FROM delivery_fees WHERE DATE(created_at) = ?", (today,))
    row = cursor.fetchone()
    today_total = row[0]
    today_count = row[1]

    conn.close()
    return {
        'pending_total': pending_total,
        'pending_count': pending_count,
        'collected_total': collected_total,
        'collected_count': collected_count,
        'today_total': today_total,
        'today_count': today_count,
    }


# ==================== WATER METER OPERATIONS (FLOW METER) ====================

def calculate_water_meter_values(bio_meter_start, bio_meter_end, ro_meter_start, ro_meter_end,
                                 bio_lpg=21.5, bio_price=5000.0, ro_lpg=20.5, ro_price=10000.0, status='closed'):
    """Helper untuk menghitung liter, galon, dan omzet air secara akurat"""
    if status == 'open':
        bio_liters = 0.0
        bio_gallons = 0.0
        bio_revenue = 0.0
        ro_liters = 0.0
        ro_gallons = 0.0
        ro_revenue = 0.0
    else:
        bio_liters = max(0.0, round(float(bio_meter_end) - float(bio_meter_start), 2))
        bio_gallons = round(bio_liters / float(bio_lpg), 2) if float(bio_lpg) > 0 else 0.0
        bio_revenue = round(bio_gallons * float(bio_price))

        ro_liters = max(0.0, round(float(ro_meter_end) - float(ro_meter_start), 2))
        ro_gallons = round(ro_liters / float(ro_lpg), 2) if float(ro_lpg) > 0 else 0.0
        ro_revenue = round(ro_gallons * float(ro_price))

    total_liters = round(bio_liters + ro_liters, 2)
    total_gallons = round(bio_gallons + ro_gallons, 2)
    total_revenue = round(bio_revenue + ro_revenue)

    return {
        'bio_liters': bio_liters,
        'bio_gallons': bio_gallons,
        'bio_revenue': bio_revenue,
        'ro_liters': ro_liters,
        'ro_gallons': ro_gallons,
        'ro_revenue': ro_revenue,
        'total_liters': total_liters,
        'total_gallons': total_gallons,
        'total_revenue': total_revenue,
    }


def add_water_meter(record_date, shift_name, user_id, user_name,
                    bio_meter_start, bio_meter_end, ro_meter_start, ro_meter_end,
                    bio_lpg=21.5, bio_price=5000.0, ro_lpg=20.5, ro_price=10000.0,
                    status='closed', notes=''):
    """Menambah catatan flow meter air baru"""
    vals = calculate_water_meter_values(
        bio_meter_start, bio_meter_end, ro_meter_start, ro_meter_end,
        bio_lpg, bio_price, ro_lpg, ro_price, status
    )

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO water_meters (
            record_date, shift_name, user_id, user_name,
            bio_meter_start, bio_meter_end, bio_liters, bio_liters_per_gallon, bio_gallons, bio_price_per_gallon, bio_revenue,
            ro_meter_start, ro_meter_end, ro_liters, ro_liters_per_gallon, ro_gallons, ro_price_per_gallon, ro_revenue,
            total_liters, total_gallons, total_revenue, status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record_date, shift_name, user_id, user_name,
        float(bio_meter_start), float(bio_meter_end), vals['bio_liters'], float(bio_lpg), vals['bio_gallons'], float(bio_price), vals['bio_revenue'],
        float(ro_meter_start), float(ro_meter_end), vals['ro_liters'], float(ro_lpg), vals['ro_gallons'], float(ro_price), vals['ro_revenue'],
        vals['total_liters'], vals['total_gallons'], vals['total_revenue'], status, notes
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_water_meter(meter_id, record_date, shift_name, user_name,
                       bio_meter_start, bio_meter_end, ro_meter_start, ro_meter_end,
                       bio_lpg=21.5, bio_price=5000.0, ro_lpg=20.5, ro_price=10000.0,
                       status='closed', notes=''):
    """Update catatan flow meter air"""
    vals = calculate_water_meter_values(
        bio_meter_start, bio_meter_end, ro_meter_start, ro_meter_end,
        bio_lpg, bio_price, ro_lpg, ro_price, status
    )

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE water_meters SET
            record_date = ?, shift_name = ?, user_name = ?,
            bio_meter_start = ?, bio_meter_end = ?, bio_liters = ?, bio_liters_per_gallon = ?, bio_gallons = ?, bio_price_per_gallon = ?, bio_revenue = ?,
            ro_meter_start = ?, ro_meter_end = ?, ro_liters = ?, ro_liters_per_gallon = ?, ro_gallons = ?, ro_price_per_gallon = ?, ro_revenue = ?,
            total_liters = ?, total_gallons = ?, total_revenue = ?, status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        record_date, shift_name, user_name,
        float(bio_meter_start), float(bio_meter_end), vals['bio_liters'], float(bio_lpg), vals['bio_gallons'], float(bio_price), vals['bio_revenue'],
        float(ro_meter_start), float(ro_meter_end), vals['ro_liters'], float(ro_lpg), vals['ro_gallons'], float(ro_price), vals['ro_revenue'],
        vals['total_liters'], vals['total_gallons'], vals['total_revenue'], status, notes, meter_id
    ))
    conn.commit()
    conn.close()


def close_water_meter_shift(meter_id, bio_meter_end, ro_meter_end, notes=None):
    """Tutup shift meteran dengan memasukkan meter akhir dan menghitung hasil"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM water_meters WHERE id = ?", (meter_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    rec = dict(row)
    bio_start = rec['bio_meter_start']
    ro_start = rec['ro_meter_start']
    bio_lpg = rec['bio_liters_per_gallon']
    bio_price = rec['bio_price_per_gallon']
    ro_lpg = rec['ro_liters_per_gallon']
    ro_price = rec['ro_price_per_gallon']
    final_notes = notes if notes is not None else rec['notes']

    vals = calculate_water_meter_values(
        bio_start, bio_meter_end, ro_start, ro_meter_end,
        bio_lpg, bio_price, ro_lpg, ro_price, status='closed'
    )

    cursor.execute("""
        UPDATE water_meters SET
            bio_meter_end = ?, bio_liters = ?, bio_gallons = ?, bio_revenue = ?,
            ro_meter_end = ?, ro_liters = ?, ro_gallons = ?, ro_revenue = ?,
            total_liters = ?, total_gallons = ?, total_revenue = ?,
            status = 'closed', notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        float(bio_meter_end), vals['bio_liters'], vals['bio_gallons'], vals['bio_revenue'],
        float(ro_meter_end), vals['ro_liters'], vals['ro_gallons'], vals['ro_revenue'],
        vals['total_liters'], vals['total_gallons'], vals['total_revenue'],
        final_notes, meter_id
    ))
    conn.commit()
    conn.close()
    return True


def delete_water_meter(meter_id):
    """Hapus catatan flow meter"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM water_meters WHERE id = ?", (meter_id,))
    conn.commit()
    conn.close()


def get_water_meters(date_from=None, date_to=None, search=None, limit=300):
    """Mengambil daftar catatan flow meter dengan opsi filter tanggal dan pencarian"""
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM water_meters WHERE 1=1"
    params = []

    if date_from:
        query += " AND record_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND record_date <= ?"
        params.append(date_to)
    if search:
        query += " AND (shift_name LIKE ? OR user_name LIKE ? OR notes LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    query += " ORDER BY record_date DESC, id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_water_meter_by_id(meter_id):
    """Ambil satu data water meter berdasarkan ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM water_meters WHERE id = ?", (meter_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_latest_water_meter():
    """Mengambil catatan meteran terakhir yang sudah selesai untuk referensi meter awal berikutnya"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM water_meters
        WHERE status = 'closed' AND bio_meter_end > 0
        ORDER BY record_date DESC, id DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_open_water_meter_shift(user_id=None):
    """Mengecek apakah ada shift meteran yang saat ini masih berstatus 'open'"""
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT * FROM water_meters WHERE status = 'open' AND user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    else:
        cursor.execute("SELECT * FROM water_meters WHERE status = 'open' ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_water_meter_summary(date_from=None, date_to=None):
    """Mengambil total ringkasan liter, galon, dan omzet flow meter dalam rentang tanggal"""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT
            COALESCE(SUM(bio_liters), 0) as total_bio_liters,
            COALESCE(SUM(bio_gallons), 0) as total_bio_gallons,
            COALESCE(SUM(bio_revenue), 0) as total_bio_revenue,
            COALESCE(SUM(ro_liters), 0) as total_ro_liters,
            COALESCE(SUM(ro_gallons), 0) as total_ro_gallons,
            COALESCE(SUM(ro_revenue), 0) as total_ro_revenue,
            COALESCE(SUM(total_liters), 0) as total_liters,
            COALESCE(SUM(total_gallons), 0) as total_gallons,
            COALESCE(SUM(total_revenue), 0) as total_revenue,
            COUNT(*) as record_count
        FROM water_meters
        WHERE status = 'closed'
    """
    params = []
    if date_from:
        query += " AND record_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND record_date <= ?"
        params.append(date_to)

    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {
        'total_bio_liters': 0, 'total_bio_gallons': 0, 'total_bio_revenue': 0,
        'total_ro_liters': 0, 'total_ro_gallons': 0, 'total_ro_revenue': 0,
        'total_liters': 0, 'total_gallons': 0, 'total_revenue': 0,
        'record_count': 0
    }


def get_water_meter_reconciliation(target_date):
    """
    Rekonsiliasi data fisik meteran air dengan penjualan kasir (POS) pada tanggal tertentu.
    Menghitung selisih galon fisik vs galon terjual di kasir.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Total dari Flow Meter pada tanggal target
    cursor.execute("""
        SELECT
            COALESCE(SUM(bio_liters), 0) as meter_bio_liters,
            COALESCE(SUM(bio_gallons), 0) as meter_bio_gallons,
            COALESCE(SUM(bio_revenue), 0) as meter_bio_revenue,
            COALESCE(SUM(ro_liters), 0) as meter_ro_liters,
            COALESCE(SUM(ro_gallons), 0) as meter_ro_gallons,
            COALESCE(SUM(ro_revenue), 0) as meter_ro_revenue,
            COALESCE(SUM(total_liters), 0) as meter_total_liters,
            COALESCE(SUM(total_gallons), 0) as meter_total_gallons,
            COALESCE(SUM(total_revenue), 0) as meter_total_revenue
        FROM water_meters
        WHERE record_date = ? AND status = 'closed'
    """, (target_date,))
    meter_data = dict(cursor.fetchone())

    # 2. Penjualan Kasir POS pada tanggal target
    # Cari item dengan nama mengandung 'Bio' dan 'RO'
    cursor.execute("""
        SELECT
            ti.product_name,
            SUM(ti.quantity) as qty,
            SUM(ti.subtotal) as total_sales
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        WHERE DATE(t.created_at) = ? AND t.status != 'cancelled'
        GROUP BY ti.product_name
    """, (target_date,))
    pos_items = cursor.fetchall()

    pos_bio_qty = 0
    pos_bio_sales = 0.0
    pos_ro_qty = 0
    pos_ro_sales = 0.0
    pos_other_qty = 0
    pos_other_sales = 0.0

    for item in pos_items:
        p_name = item['product_name'].lower()
        if 'bio' in p_name:
            pos_bio_qty += item['qty']
            pos_bio_sales += item['total_sales']
        elif 'ro' in p_name or 'osmosis' in p_name:
            pos_ro_qty += item['qty']
            pos_ro_sales += item['total_sales']
        else:
            pos_other_qty += item['qty']
            pos_other_sales += item['total_sales']

    # Total keseluruhan transaksi POS pada tanggal tersebut
    cursor.execute("""
        SELECT COALESCE(SUM(total), 0), COUNT(*)
        FROM transactions
        WHERE DATE(created_at) = ? AND status != 'cancelled'
    """, (target_date,))
    row_t = cursor.fetchone()
    pos_total_sales = row_t[0]
    pos_trx_count = row_t[1]

    conn.close()

    # Hitung selisih (Kasir vs Meteran)
    # Selisih galon: Kasir - Meteran (Jika negatif, air keluar lebih banyak daripada tercatat kasir)
    diff_bio_qty = pos_bio_qty - meter_data['meter_bio_gallons']
    diff_bio_sales = pos_bio_sales - meter_data['meter_bio_revenue']
    diff_ro_qty = pos_ro_qty - meter_data['meter_ro_gallons']
    diff_ro_sales = pos_ro_sales - meter_data['meter_ro_revenue']
    diff_total_sales = pos_total_sales - meter_data['meter_total_revenue']

    return {
        'target_date': target_date,
        'meter': meter_data,
        'pos': {
            'bio_qty': pos_bio_qty,
            'bio_sales': pos_bio_sales,
            'ro_qty': pos_ro_qty,
            'ro_sales': pos_ro_sales,
            'other_qty': pos_other_qty,
            'other_sales': pos_other_sales,
            'total_sales': pos_total_sales,
            'trx_count': pos_trx_count,
        },
        'diff': {
            'bio_qty': round(diff_bio_qty, 2),
            'bio_sales': round(diff_bio_sales),
            'ro_qty': round(diff_ro_qty, 2),
            'ro_sales': round(diff_ro_sales),
            'total_sales': round(diff_total_sales),
        }
    }
