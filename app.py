"""
app.py – PickSpot Core Backend
Stack : Flask + PyMySQL (SSL for TiDB Cloud)
Run   : python app.py  (dev)
"""

from flask import (Flask, render_template, redirect,
                   url_for, request, session, flash)
import pymysql
import pymysql.cursors
import hashlib
from functools import wraps
from datetime import datetime

# ── App & Config ─────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'pickspot_s3cr3t_2025'          # ganti di production

DB = dict(
    host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
    port=4000,
    user="hLJX4qyXZRc23dw.root",
    password="7UoqtuH0kUfCjhLn",
    database="test",
    ssl_verify_cert=True,
    ssl={"ssl": {}},
    connect_timeout=10
)


# ── Helpers ──────────────────────────────────────────────────
def get_db():
    return pymysql.connect(
        **DB,
        cursorclass=pymysql.cursors.DictCursor
    )


def hash_pw(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def login_required(f):
    @wraps(f)
    def inner(*a, **kw):
        if 'id_user' not in session:
            flash('Silakan login terlebih dahulu.', 'error')
            return redirect(url_for('login'))
        return f(*a, **kw)
    return inner


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def inner(*a, **kw):
            if session.get('role') not in roles:
                flash('Akses ditolak.', 'error')
                return redirect(url_for('home'))
            return f(*a, **kw)
        return inner
    return decorator


# ── PUBLIC ROUTES ────────────────────────────────────────────

@app.route('/')
def home():
    """Home – daftar spot tersedia untuk semua pengunjung."""
    lokasi  = request.args.get('lokasi', '')
    tanggal = request.args.get('tanggal', '')

    db  = get_db()
    cur = db.cursor()

    if lokasi:
        cur.execute(
            "SELECT * FROM spots WHERE stok_booking > 0 AND lokasi LIKE %s ORDER BY rating DESC",
            (f'%{lokasi}%',)
        )
    else:
        cur.execute("SELECT * FROM spots WHERE stok_booking > 0 ORDER BY rating DESC")

    spots = cur.fetchall()
    db.close()
    return render_template('index.html', spots=spots, lokasi=lokasi, tanggal=tanggal)


# ── AUTH ROUTES ───────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'id_user' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email    = request.form['email'].strip()
        password = hash_pw(request.form['password'])

        db  = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cur.fetchone()
        db.close()

        if user:
            session.update(id_user=user['id_user'], nama=user['nama'], role=user['role'])
            flash(f"Selamat datang, {user['nama']}! 🐱", 'success')
            return redirect(url_for('dashboard') if user['role'] != 'member' else url_for('home'))

        flash('Email atau password salah.', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nama     = request.form['nama'].strip()
        email    = request.form['email'].strip()
        password = hash_pw(request.form['password'])

        db  = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                "INSERT INTO users (nama, email, password, role) VALUES (%s,%s,%s,'member')",
                (nama, email, password)
            )
            db.commit()
            flash('Registrasi berhasil! Silakan login. 🎉', 'success')
            return redirect(url_for('login'))
        except pymysql.IntegrityError:
            flash('Email sudah terdaftar.', 'error')
        finally:
            db.close()

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Kamu berhasil logout.', 'success')
    return redirect(url_for('home'))


# ── MEMBER ROUTES ─────────────────────────────────────────────

@app.route('/book/<int:id_spot>')
@login_required
def book_spot(id_spot):
    if session.get('role') != 'member':
        flash('Hanya member yang bisa melakukan booking.', 'error')
        return redirect(url_for('home'))

    db  = get_db()
    cur = db.cursor()
    cur.execute("SELECT stok_booking FROM spots WHERE id_spot=%s", (id_spot,))
    spot = cur.fetchone()

    if spot and spot['stok_booking'] > 0:
        cur.execute(
            "INSERT INTO bookings (id_user, id_spot, tanggal_waktu, status) VALUES (%s,%s,%s,'pending')",
            (session['id_user'], id_spot, datetime.now())
        )
        cur.execute("UPDATE spots SET stok_booking = stok_booking - 1 WHERE id_spot=%s", (id_spot,))
        db.commit()
        flash('Booking berhasil! Status: Pending. ✅', 'success')
    else:
        flash('Maaf, slot booking untuk spot ini sudah habis.', 'error')

    db.close()
    return redirect(url_for('home'))


# ── ADMIN / STAFF ROUTES ──────────────────────────────────────

@app.route('/dashboard')
@login_required
@role_required('admin', 'staff')
def dashboard():
    db  = get_db()
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) AS n FROM spots")
    total_spots = cur.fetchone()['n']
    cur.execute("SELECT COUNT(*) AS n FROM bookings")
    total_bookings = cur.fetchone()['n']
    cur.execute("SELECT COUNT(*) AS n FROM users WHERE role='member'")
    total_members = cur.fetchone()['n']

    cur.execute("""
        SELECT s.*, COUNT(b.id_booking) AS jml_booking
        FROM spots s
        LEFT JOIN bookings b ON s.id_spot = b.id_spot
        GROUP BY s.id_spot
        ORDER BY s.id_spot DESC
    """)
    spots = cur.fetchall()
    db.close()

    return render_template('dashboard.html',
                           spots=spots,
                           total_spots=total_spots,
                           total_bookings=total_bookings,
                           total_members=total_members)


@app.route('/add_spot', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def add_spot():
    if request.method == 'POST':
        data = (
            request.form['nama_spot'].strip(),
            request.form['deskripsi'].strip(),
            request.form['lokasi'].strip(),
            request.form['harga_estimasi'],
            request.form['stok_booking'],
        )
        db  = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO spots (nama_spot, deskripsi, lokasi, harga_estimasi, stok_booking) "
            "VALUES (%s,%s,%s,%s,%s)", data
        )
        db.commit()
        db.close()
        flash('Spot baru berhasil ditambahkan! 📍', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_spot.html')


@app.route('/edit_spot/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def edit_spot(id):
    db  = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        data = (
            request.form['nama_spot'].strip(),
            request.form['deskripsi'].strip(),
            request.form['lokasi'].strip(),
            request.form['harga_estimasi'],
            request.form['stok_booking'],
            id,
        )
        cur.execute(
            "UPDATE spots SET nama_spot=%s, deskripsi=%s, lokasi=%s, "
            "harga_estimasi=%s, stok_booking=%s WHERE id_spot=%s", data
        )
        db.commit()
        db.close()
        flash('Spot berhasil diperbarui! ✏️', 'success')
        return redirect(url_for('dashboard'))

    cur.execute("SELECT * FROM spots WHERE id_spot=%s", (id,))
    spot = cur.fetchone()
    db.close()

    if not spot:
        flash('Spot tidak ditemukan.', 'error')
        return redirect(url_for('dashboard'))

    return render_template('edit_spot.html', spot=spot)


@app.route('/delete_spot/<int:id>')
@login_required
@role_required('admin')                   # hanya admin boleh hapus
def delete_spot(id):
    db  = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM spots WHERE id_spot=%s", (id,))
    db.commit()
    db.close()
    flash('Spot berhasil dihapus.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/bookings')
@login_required
@role_required('admin', 'staff')
def bookings_report():
    db  = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT b.id_booking, u.nama AS nama_user, s.nama_spot, s.lokasi,
               b.tanggal_waktu, b.status
        FROM bookings b
        JOIN users u ON b.id_user  = u.id_user
        JOIN spots s ON b.id_spot  = s.id_spot
        ORDER BY b.tanggal_waktu DESC
    """)
    bookings = cur.fetchall()
    db.close()
    return render_template('bookings.html', bookings=bookings)


@app.route('/update_booking_status/<int:id>', methods=['POST'])
@login_required
@role_required('admin', 'staff')
def update_booking_status(id):
    status = request.form.get('status')
    if status not in ('pending', 'confirmed', 'cancelled'):
        flash('Status tidak valid.', 'error')
        return redirect(url_for('bookings_report'))

    db  = get_db()
    cur = db.cursor()
    cur.execute("UPDATE bookings SET status=%s WHERE id_booking=%s", (status, id))
    db.commit()
    db.close()
    flash('Status booking diperbarui.', 'success')
    return redirect(url_for('bookings_report'))


# ── Entry Point ───────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5000)
