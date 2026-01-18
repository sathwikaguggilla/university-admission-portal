from flask import Flask, render_template, request, redirect, flash, session
import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("students.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            marks INTEGER,
            entrance INTEGER,
            age INTEGER,
            dept TEXT,
            status TEXT DEFAULT 'Pending',
            allocated TEXT DEFAULT 'Not Allocated'
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Seat limits
TOTAL_SEATS = {
    "CS": 2,
    "Mech": 2,
    "Civil": 1
}

# ---------------- STUDENT PAGE ----------------
@app.route("/")
def register():
    return render_template("register.html")

# ---------------- FORM SUBMIT ----------------
@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name")
    email = request.form.get("email")
    marks = request.form.get("marks")
    entrance = request.form.get("entrance")
    age = request.form.get("age")
    dept = request.form.get("dept")

    if not all([name, email, marks, entrance, age, dept]):
        flash("❌ All fields are required")
        return redirect("/")

    conn = sqlite3.connect("students.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO students (name, email, marks, entrance, age, dept)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, email, marks, entrance, age, dept))
    conn.commit()
    conn.close()

    flash("✅ Application submitted successfully")
    return redirect("/")

# ---------------- ADMIN LOGIN ----------------
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect("/admin")
        else:
            flash("❌ Invalid credentials")
            return redirect("/admin-login")

    return render_template("admin_login.html")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/admin-login")

    conn = sqlite3.connect("students.db")
    c = conn.cursor()

    # Seat usage
    c.execute("SELECT COUNT(*) FROM students WHERE dept='CS' AND allocated='Allocated'")
    cs_used = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM students WHERE dept='Mech' AND allocated='Allocated'")
    mech_used = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM students WHERE dept='Civil' AND allocated='Allocated'")
    civil_used = c.fetchone()[0]

    # Stats
    c.execute("SELECT COUNT(*) FROM students")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM students WHERE allocated='Allocated'")
    allocated = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM students WHERE allocated='Not Allocated'")
    pending = c.fetchone()[0]

    conn.close()

    remaining = {
        "CS": TOTAL_SEATS["CS"] - cs_used,
        "Mech": TOTAL_SEATS["Mech"] - mech_used,
        "Civil": TOTAL_SEATS["Civil"] - civil_used
    }

    return render_template(
        "admin.html",
        remaining=remaining,
        total=total,
        allocated=allocated,
        pending=pending
    )

# ---------------- MERIT PAGE ----------------
@app.route("/merit")
def merit():
    conn = sqlite3.connect("students.db")
    c = conn.cursor()

    c.execute("""
        SELECT * FROM students
        ORDER BY marks DESC, entrance DESC, age DESC
    """)
    students = c.fetchall()

    conn.close()
    return render_template("merit.html", students=students)

# ---------------- SEAT ALLOCATION ----------------
@app.route("/allocate")
def allocate():
    if not session.get("admin"):
        return redirect("/admin-login")

    conn = sqlite3.connect("students.db")
    c = conn.cursor()

    c.execute("""
        SELECT * FROM students
        ORDER BY marks DESC, entrance DESC, age DESC
    """)
    students = c.fetchall()

    seats_left = TOTAL_SEATS.copy()

    for s in students:
        id, name, email, marks, entrance, age, dept, status, allocated = s

        if allocated == "Not Allocated" and seats_left.get(dept, 0) > 0:
            seats_left[dept] -= 1
            c.execute("""
                UPDATE students
                SET allocated='Allocated', status='Verified'
                WHERE id=?
            """, (id,))
            print(f"Email sent to {email}: Selected for {dept}")

    conn.commit()
    conn.close()

    return redirect("/merit")

# ---------------- CLEAR DATA ----------------
@app.route("/clear")
def clear_data():
    if not session.get("admin"):
        return redirect("/admin-login")

    conn = sqlite3.connect("students.db")
    c = conn.cursor()
    c.execute("DELETE FROM students")
    conn.commit()
    conn.close()

    flash("All data cleared")
    return redirect("/admin")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
