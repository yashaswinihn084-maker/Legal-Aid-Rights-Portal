from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = "legal_aid_secret_key_2026"

def get_db():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "26122006"),
            database=os.getenv("DB_NAME", "legal_aid_portal")
        )
    except Exception as e:
        print(f"DB connection failed: {e}")
        return None

db = get_db()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        cursor = db.cursor()
        sql = """
        SELECT * FROM users
        WHERE email = %s AND password = %s
        """
        cursor.execute(sql, (email, password))
        user = cursor.fetchone()
        cursor.close()
        if user:
            session["user_logged_in"] = True
            session["user_name"] = user[1]
            session["user_email"] = user[2]
            session["user_phone"] = user[3]
            return redirect(url_for("user_dashboard"))
        return "Invalid email or password"
    return render_template("login.html")

@app.route("/user-dashboard")
def user_dashboard():

    if not session.get("user_logged_in"):
        return redirect(url_for("login"))

    user_email = session.get("user_email")

    db_conn = get_db()
if db_conn is None:
    return "Database not available on live server"
cursor = db_conn.cursor()

    sql = """
    SELECT * FROM legal_aid_requests
    WHERE email = %s
    """

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

        db_conn = get_db()
if db_conn is None:
    return "Database not available on live server"
cursor = db_conn.cursor()

        sql = """
        INSERT INTO users (name, email, phone, password)
        VALUES (%s, %s, %s, %s)
        """

        values = (name, email, phone, password)

        cursor.execute(sql, values)
        db.commit()
        cursor.close()

        return "Registration successful!"

    return render_template("register.html")

@app.route("/")
def home():
    return render_template("index.html")


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

        sql = """
        INSERT INTO contact_messages
        (name, email, subject, message)
        VALUES (%s, %s, %s, %s)
        """

        values = (name, email, subject, message)

        cursor.execute(sql, values)
        db.commit()
        cursor.close()

        return "Your message has been submitted successfully."

    return render_template("contact.html")


@app.route("/legal-aid", methods=["GET", "POST"])
def legal_aid():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        category = request.form["category"]
        description = request.form["description"]

        db_conn = get_db()
if db_conn is None:
    return "Database not available on live server"
cursor = db_conn.cursor()

        sql = """
        INSERT INTO legal_aid_requests
        (user_name, email, phone, subject, description)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (name, email, phone, category, description)

        cursor.execute(sql, values)
        db.commit()
        cursor.close()

        return "Your legal aid request has been submitted successfully."

    return render_template("legal_aid.html")

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))

        return "Invalid username or password"

    return render_template("admin_login.html")

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

        sql = """
        UPDATE legal_aid_requests
        SET status = %s
        WHERE id = %s
        """

        cursor.execute(sql, (status, request_id))
        db.commit()
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
    db.commit()
    cursor.close()

    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True)
