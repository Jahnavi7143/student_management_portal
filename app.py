from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import os
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.serving import WSGIRequestHandler
import csv

app = Flask(__name__)

# 🔐 Secret key
app.secret_key = os.environ.get("SECRET_KEY") or "fallback_secret"

# 🔐 Secure cookies
app.config.update(
    SESSION_COOKIE_SECURE=False,  # keep False for localhost
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Strict'
)

# 🔐 Hide server version
WSGIRequestHandler.server_version = "SecureServer"
WSGIRequestHandler.sys_version = ""

csrf = CSRFProtect(app)

# 🔐 Headers
@app.after_request
def set_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Server'] = 'SecureServer'
    return response

DB = "database.db"

# ---------------- DB ----------------
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        marks INTEGER
    )""")

    conn.commit()
    conn.close()

# ---------------- HELPERS ----------------
def is_admin():
    return session.get("role") == "admin"

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return redirect(url_for("login"))

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET","POST"])
def register():
    error = success = None
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                         (username, password, "user"))
            conn.commit()
            success = "Account created successfully!"
        except:
            error = "Username already exists."
        conn.close()

    return render_template("register.html", error=error, success=success)

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html",
                           username=session["username"],
                           role=session["role"])

# ---------------- MY DATA ----------------
@app.route("/my_data")
def my_data():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id=?",
                           (session["user_id"],)).fetchone()
    conn.close()

    return render_template("my_data.html", student=student)

# ---------------- UPDATE PROFILE ----------------
@app.route("/update_profile", methods=["GET","POST"])
def update_profile():
    if "username" not in session:
        return redirect(url_for("login"))

    success = None

    if request.method == "POST":
        new_username = request.form["username"]
        new_password = generate_password_hash(request.form["password"])

        conn = get_db()
        conn.execute(
            "UPDATE users SET username=?, password=? WHERE id=?",
            (new_username, new_password, session["user_id"])
        )
        conn.commit()
        conn.close()

        session["username"] = new_username
        success = "Profile updated successfully!"

    return render_template("update_profile.html",
                           username=session["username"],
                           role=session["role"],
                           success=success)

# ---------------- STUDENTS ----------------
@app.route("/students")
def students():
    if "username" not in session:
        return redirect(url_for("login"))
    if not is_admin():
        return "Access Denied"

    conn = get_db()
    data = conn.execute("SELECT * FROM students").fetchall()
    conn.close()

    return render_template("students.html", students=data)

# ---------------- ADD USER ----------------
@app.route("/add_user", methods=["GET","POST"])
def add_user():
    if not is_admin():
        return "Access Denied"

    error = success = None

    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        try:
            conn.execute("INSERT INTO users VALUES (NULL,?,?,?)",
                         (username, password, "user"))
            conn.commit()
            success = "User added!"
        except:
            error = "User already exists"
        conn.close()

    conn = get_db()
    users = conn.execute("SELECT id,username,role FROM users").fetchall()
    conn.close()

    return render_template("add_user.html", users=users, error=error, success=success)

# ---------------- DELETE ----------------
@app.route("/delete", methods=["GET","POST"])
def delete():
    if not is_admin():
        return "Access Denied"

    conn = get_db()
    message = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "delete_all":
            conn.execute("DELETE FROM students")
            message = "All students deleted!"

        elif action == "delete_one":
            student_id = request.form.get("student_id")
            conn.execute("DELETE FROM students WHERE id=?", (student_id,))
            message = "Student deleted!"

        conn.commit()

    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()

    return render_template("delete.html", students=students, message=message)

# ---------------- DOWNLOAD CSV ----------------
@app.route("/download_students")
def download_students():
    if not is_admin():
        return "Access Denied"

    conn = get_db()
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()

    with open("students.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Marks"])
        for s in students:
            writer.writerow([s["id"], s["name"], s["marks"]])

    return send_file("students.csv", as_attachment=True)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- MAIN ----------------
if __name__ == "__main__":
    init_db()
    app.run(debug=False)