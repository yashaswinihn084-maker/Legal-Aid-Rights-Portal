from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import os
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = "legal_aid_secret_key_2026"

def get_db():
    try:
        url = os.getenv("DATABASE_URL")
        result = urlparse(url)
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port,
            sslmode='require'
        )
        return conn
    except Exception as e:
        print(f"DB connection failed: {e}")
        return None

@app.route("/login", methods=["GET", "POST"])
def login():
    user = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db_conn = get_db()
        if db_conn is None:
            return "Database not available on live server"
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session["user_logged_in"] = True
            session["user_name"] = user[1]
            session["user_email"] = user[2]
            session["user_phone"] = user[3]
            return redirect(url_for("user_dashboard"))
        else:
            return "Invalid email or password"

    return render_template("login.html")

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/user-dashboard")
def user_dashboard():
    if not session.get("user_logged_in"):
        return redirect(url_for("login"))

    user_email = session.get("user_email")

    db_conn = get_db()
    if db_conn is None:
        return "Database not available on live server"
    cursor = db_conn.cursor()

    sql = "SELECT * FROM legal_aid_requests WHERE user_email = %s ORDER BY created_at DESC"
    cursor.execute(sql, (user_email,))
    requests = cursor.fetchall()
    cursor.close()

    return render_template("user_dashboard.html", requests=requests)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        if not phone.isdigit() or len(phone)!= 10:
            return "Phone number must be exactly 10 digits"

        db_conn = get_db()
        if db_conn is None:
            return "Database not available on live server"
        try:
            cursor = db_conn.cursor()
            sql = "INSERT INTO users (name, email, phone, password) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (name, email, phone, password))
            db_conn.commit()
            cursor.close()
        except Exception as e:
            return f"Registration error: {e}"

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/rights")
def rights():
    return render_template("rights.html")

@app.route("/laws")
def laws():
    return render_template("laws.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        subject = request.form["subject"]
        message = request.form["message"]

        db_conn = get_db()
        if db_conn is None:
            return "Database not available on live server"
        cursor = db_conn.cursor()

        sql = "INSERT INTO contact_messages (name, email, subject, message) VALUES (%s, %s, %s, %s)"
        values = (name, email, subject, message)

        cursor.execute(sql, values)
        db_conn.commit()
        cursor.close()
        return "Your message has been submitted successfully."
    return render_template("contact.html")

@app.route("/legal-aid", methods=["GET", "POST"])
def legal_aid():
    if request.method == "POST":
        try:
            name = request.form["name"]
            email = request.form["email"]
            phone = request.form["phone"]
            category = request.form["category"]
            description = request.form["description"]

            if not phone.isdigit() or len(phone)!= 10:
                return "Phone number must be exactly 10 digits"

            db_conn = get_db()
            if db_conn is None:
                return "Database not available on live server"
            cursor = db_conn.cursor()

            sql = "INSERT INTO legal_aid_requests (user_email, name, phone, issue_type, description, status) VALUES (%s, %s, %s, %s, %s, 'Pending')"
            values = (email, name, phone, category, description)

            cursor.execute(sql, values)
            db_conn.commit()
            cursor.close()

            return "Your legal aid request has been submitted successfully."
        except Exception as e:
            return f"Error submitting request: {e}"
    return render_template("legal_aid.html")

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin123':
            session['admin'] = True
            return redirect('/admin-dashboard')
        else:
            return "Invalid admin credentials"
    return render_template('admin_login.html')

@app.route("/admin-messages")

def admin_messages():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    db_conn = get_db()
    if db_conn is None:
        return "Database not available on live server"
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM contact_messages")
    messages = cursor.fetchall()
    cursor.close()
    return render_template("admin_messages.html", messages=messages)

@app.route("/admin")
def admin():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    db_conn = get_db()
    if db_conn is None:
        return "Database not available on live server"
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM legal_aid_requests")
    requests = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", requests=requests)

@app.route("/admin-logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

@app.route("/user-logout")
def user_logout():
    session.pop("user_logged_in", None)
    session.pop("user_name", None)
    session.pop("user_email", None)
    session.pop("user_phone", None)
    return redirect(url_for("login"))

@app.route("/update-status/<int:request_id>", methods=["GET", "POST"])
def update_status(request_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        status = request.form["status"]
        db_conn = get_db()
        if db_conn is None:
            return "Database not available on live server"
        cursor = db_conn.cursor()
        sql = "UPDATE legal_aid_requests SET status = %s WHERE id = %s"
        cursor.execute(sql, (status, request_id))
        db_conn.commit()
        cursor.close()
        return redirect(url_for("admin"))

    return render_template("update_status.html")

@app.route("/delete-request/<int:request_id>")
def delete_request(request_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    db_conn = get_db()
    if db_conn is None:
        return "Database not available on live server"
    cursor = db_conn.cursor()
    sql = "DELETE FROM legal_aid_requests WHERE id = %s"
    cursor.execute(sql, (request_id,))
    db_conn.commit()
    cursor.close()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True)
