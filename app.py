# from flask import Flask, render_template, request, redirect, url_for, session
# import sqlite3
# import os

# app = Flask(__name__)
# app.secret_key = "supersecretkey123"  # VULNERABILITY: Hardcoded weak secret key

# DB = "database.db"

# # ─── DATABASE SETUP ──────────────────────────────────────────────────────────

# def get_db():
#     conn = sqlite3.connect(DB)
#     conn.row_factory = sqlite3.Row
#     return conn

# def init_db():
#     conn = get_db()
#     c = conn.cursor()

#     # Users table – passwords stored in PLAIN TEXT (intentional vulnerability)
#     c.execute("""
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             username TEXT NOT NULL UNIQUE,
#             password TEXT NOT NULL,
#             role TEXT NOT NULL DEFAULT 'user'
#         )
#     """)

#     # Students table
#     c.execute("""
#         CREATE TABLE IF NOT EXISTS students (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             name TEXT NOT NULL,
#             marks INTEGER NOT NULL
#         )
#     """)

#     # Seed admin
#     c.execute("SELECT * FROM users WHERE username='admin'")
#     if not c.fetchone():
#         c.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")

#     # Seed a student user
#     c.execute("SELECT * FROM users WHERE username='john'")
#     if not c.fetchone():
#         c.execute("INSERT INTO users (username, password, role) VALUES ('john', 'john123', 'user')")

#     # Seed student data
#     c.execute("SELECT COUNT(*) FROM students")
#     if c.fetchone()[0] == 0:
#         c.executemany("INSERT INTO students (name, marks) VALUES (?, ?)", [
#             ("Rahul", 85),
#             ("Priya", 92),
#             ("John",  78),
#             ("Amit",  65),
#             ("Sara",  88),
#         ])

#     conn.commit()
#     conn.close()

# # ─── ROUTES ──────────────────────────────────────────────────────────────────

# @app.route("/")
# def index():
#     return redirect(url_for("login"))


# # ── LOGIN ──────────────────────────────────────────────────────────────────
# @app.route("/login", methods=["GET", "POST"])
# def login():
#     error = None
#     if request.method == "POST":
#         username = request.form["username"]
#         password = request.form["password"]

#         conn = get_db()
#         # VULNERABILITY: SQL Injection – user input directly in query string
#         query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
#         try:
#             user = conn.execute(query).fetchone()
#         except Exception as e:
#             error = f"DB Error: {e}"
#             conn.close()
#             return render_template("login.html", error=error)
#         conn.close()

#         if user:
#             session["user_id"]  = user["id"]
#             session["username"] = user["username"]
#             session["password"] = user["password"]   # VULNERABILITY: password in session
#             session["role"]     = user["role"]
#             return redirect(url_for("dashboard"))
#         else:
#             error = "Invalid username or password."

#     return render_template("login.html", error=error)


# # ── REGISTER ───────────────────────────────────────────────────────────────
# @app.route("/register", methods=["GET", "POST"])
# def register():
#     error = None
#     success = None
#     if request.method == "POST":
#         username = request.form["username"]
#         password = request.form["password"]
#         role     = request.form.get("role", "user")   # VULNERABILITY: user can self-assign role

#         conn = get_db()
#         try:
#             # VULNERABILITY: No password hashing – stored plain text
#             conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
#                          (username, password, role))
#             conn.commit()
#             success = "Account created! You can now login."
#         except sqlite3.IntegrityError:
#             error = "Username already exists."
#         conn.close()

#     return render_template("register.html", error=error, success=success)


# # ── DASHBOARD ──────────────────────────────────────────────────────────────
# @app.route("/dashboard")
# def dashboard():
#     if "username" not in session:
#         return redirect(url_for("login"))
#     return render_template("dashboard.html",
#                            username=session["username"],
#                            password=session["password"],   # VULNERABILITY: password displayed
#                            role=session["role"])


# # ── MY DATA (student only) ─────────────────────────────────────────────────
# @app.route("/my_data")
# def my_data():
#     if "username" not in session:
#         return redirect(url_for("login"))

#     conn = get_db()
#     # VULNERABILITY: IDOR – uses user-supplied GET param instead of session id
#     student_id = request.args.get("id", session.get("user_id", 1))
#     student = conn.execute(f"SELECT * FROM students WHERE id={student_id}").fetchone()
#     conn.close()

#     return render_template("my_data.html",
#                            student=student,
#                            username=session["username"],
#                            role=session["role"])


# # ── ALL STUDENTS (admin) ───────────────────────────────────────────────────
# @app.route("/students")
# def students():
#     # VULNERABILITY: No proper role check – any logged-in user can reach this
#     if "username" not in session:
#         return redirect(url_for("login"))

#     conn = get_db()
#     all_students = conn.execute("SELECT * FROM students").fetchall()
#     conn.close()
#     return render_template("students.html",
#                            students=all_students,
#                            username=session["username"],
#                            role=session["role"])


# # ── ADD USER (admin) ───────────────────────────────────────────────────────
# @app.route("/add_user", methods=["GET", "POST"])
# def add_user():
#     # VULNERABILITY: No role check – any logged-in user can add users
#     if "username" not in session:
#         return redirect(url_for("login"))

#     error = None
#     success = None
#     if request.method == "POST":
#         username = request.form["username"]
#         password = request.form["password"]
#         role     = request.form.get("role", "user")
#         conn = get_db()
#         try:
#             conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
#                          (username, password, role))
#             conn.commit()
#             success = f"User '{username}' added successfully."
#         except sqlite3.IntegrityError:
#             error = "Username already exists."
#         conn.close()

#     conn = get_db()
#     all_users = conn.execute("SELECT id, username, role FROM users").fetchall()
#     conn.close()
#     return render_template("add_user.html",
#                            error=error, success=success,
#                            users=all_users,
#                            username=session["username"],
#                            role=session["role"])


# # ── DELETE (admin) ─────────────────────────────────────────────────────────
# @app.route("/delete", methods=["GET", "POST"])
# def delete():
#     # VULNERABILITY: No role check
#     if "username" not in session:
#         return redirect(url_for("login"))

#     message = None
#     if request.method == "POST":
#         action    = request.form.get("action")
#         student_id = request.form.get("student_id")
#         conn = get_db()
#         if action == "delete_all":
#             conn.execute("DELETE FROM students")
#             conn.commit()
#             message = "All student records deleted."
#         elif action == "delete_one" and student_id:
#             conn.execute(f"DELETE FROM students WHERE id={student_id}")  # VULNERABILITY: SQLi
#             conn.commit()
#             message = f"Student ID {student_id} deleted."
#         conn.close()

#     conn = get_db()
#     all_students = conn.execute("SELECT * FROM students").fetchall()
#     conn.close()
#     return render_template("delete.html",
#                            students=all_students,
#                            message=message,
#                            username=session["username"],
#                            role=session["role"])


# # ── UPDATE PROFILE ─────────────────────────────────────────────────────────
# @app.route("/update_profile", methods=["GET", "POST"])
# def update_profile():
#     if "username" not in session:
#         return redirect(url_for("login"))

#     success = None
#     if request.method == "POST":
#         new_username = request.form["username"]
#         new_password = request.form["password"]
#         # VULNERABILITY: Can also change role via hidden field manipulation
#         new_role     = request.form.get("role", session["role"])

#         conn = get_db()
#         conn.execute("UPDATE users SET username=?, password=?, role=? WHERE id=?",
#                      (new_username, new_password, new_role, session["user_id"]))
#         conn.commit()
#         conn.close()

#         session["username"] = new_username
#         session["password"] = new_password
#         session["role"]     = new_role
#         success = "Profile updated successfully!"

#     return render_template("update_profile.html",
#                            username=session["username"],
#                            password=session["password"],
#                            role=session["role"],
#                            success=success)


# # ── LOGOUT ─────────────────────────────────────────────────────────────────
# @app.route("/logout")
# def logout():
#     session.clear()
#     return redirect(url_for("login"))


# # ─── MAIN ─────────────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     init_db()
#     app.run(debug=True)   # VULNERABILITY: debug=True in production


from flask import Flask, render_template, request, redirect, url_for, session, Response
import sqlite3
import csv
import io

app = Flask(__name__)
app.secret_key = "supersecretkey123"

DB = "database.db"

# ─── DATABASE ─────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        marks INTEGER NOT NULL
    )""")

    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES ('admin','admin123','admin')")

    c.execute("SELECT * FROM users WHERE username='john'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES ('john','john123','user')")

    c.execute("SELECT COUNT(*) FROM students")
    if c.fetchone()[0] == 0:
        students = [
            ("Rahul Sharma",    85), ("Priya Patel",     92),
            ("John Mathew",     78), ("Amit Verma",      65),
            ("Sara Khan",       88), ("Ravi Kumar",      74),
            ("Neha Singh",      91), ("Arjun Nair",      55),
            ("Pooja Mehta",     83), ("Vikram Rao",      69),
            ("Anjali Gupta",    95), ("Suresh Das",      61),
            ("Divya Reddy",     87), ("Karan Joshi",     72),
            ("Meera Iyer",      90), ("Rohit Bose",      48),
            ("Sneha Pillai",    76), ("Aakash Tiwari",   82),
            ("Lakshmi Nair",    93), ("Deepak Chauhan",  67),
        ]
        c.executemany("INSERT INTO students (name, marks) VALUES (?,?)", students)

    conn.commit()
    conn.close()

def grade(marks):
    if marks >= 90: return "A+"
    elif marks >= 80: return "A"
    elif marks >= 70: return "B"
    elif marks >= 60: return "C"
    else: return "F"

# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        try:
            user = conn.execute(query).fetchone()
        except:
            error = "Something went wrong. Please try again."
            conn.close()
            return render_template("login.html", error=error)
        conn.close()
        if user:
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            session["password"] = user["password"]
            session["role"]     = user["role"]
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password."
    return render_template("login.html", error=error)

@app.route("/register", methods=["GET","POST"])
def register():
    error = success = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role     = request.form.get("role", "user")
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                         (username, password, role))
            conn.commit()
            success = "Account created successfully! You can now login."
        except sqlite3.IntegrityError:
            error = "Username already exists. Please choose another."
        conn.close()
    return render_template("register.html", error=error, success=success)

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html",
                           username=session["username"],
                           password=session["password"],
                           role=session["role"])

@app.route("/my_data")
def my_data():
    if "username" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    student_id = request.args.get("id", session.get("user_id", 1))
    student = conn.execute(f"SELECT * FROM students WHERE id={student_id}").fetchone()
    conn.close()
    return render_template("my_data.html", student=student,
                           username=session["username"], role=session["role"])

@app.route("/students")
def students():
    if "username" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    all_students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()
    # attach grade
    data = [{"id": s["id"], "name": s["name"],
              "marks": s["marks"], "grade": grade(s["marks"])} for s in all_students]
    return render_template("students.html", students=data,
                           username=session["username"], role=session["role"])

@app.route("/download_students")
def download_students():
    if "username" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    rows = conn.execute("SELECT * FROM students").fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Marks", "Grade"])
    for s in rows:
        writer.writerow([s["id"], s["name"], s["marks"], grade(s["marks"])])
    output.seek(0)
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=students_data.csv"})

@app.route("/add_user", methods=["GET","POST"])
def add_user():
    if "username" not in session:
        return redirect(url_for("login"))
    error = success = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role     = request.form.get("role","user")
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                         (username, password, role))
            conn.commit()
            success = f"User '{username}' added successfully."
        except sqlite3.IntegrityError:
            error = "Username already exists."
        conn.close()
    conn = get_db()
    all_users = conn.execute("SELECT id,username,role FROM users").fetchall()
    conn.close()
    return render_template("add_user.html", error=error, success=success,
                           users=all_users, username=session["username"], role=session["role"])

@app.route("/delete", methods=["GET","POST"])
def delete():
    if "username" not in session:
        return redirect(url_for("login"))
    message = None
    if request.method == "POST":
        action     = request.form.get("action")
        student_id = request.form.get("student_id")
        conn = get_db()
        if action == "delete_all":
            conn.execute("DELETE FROM students")
            conn.commit()
            message = "All student records have been deleted."
        elif action == "delete_one" and student_id:
            conn.execute(f"DELETE FROM students WHERE id={student_id}")
            conn.commit()
            message = "Student record deleted successfully."
        conn.close()
    conn = get_db()
    all_students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()
    return render_template("delete.html", students=all_students,
                           message=message, username=session["username"], role=session["role"])

@app.route("/update_profile", methods=["GET","POST"])
def update_profile():
    if "username" not in session:
        return redirect(url_for("login"))
    success = None
    if request.method == "POST":
        new_username = request.form["username"]
        new_password = request.form["password"]
        new_role     = request.form.get("role", session["role"])
        conn = get_db()
        conn.execute("UPDATE users SET username=?,password=?,role=? WHERE id=?",
                     (new_username, new_password, new_role, session["user_id"]))
        conn.commit()
        conn.close()
        session["username"] = new_username
        session["password"] = new_password
        session["role"]     = new_role
        success = "Profile updated successfully!"
    return render_template("update_profile.html",
                           username=session["username"],
                           password=session["password"],
                           role=session["role"],
                           success=success)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)