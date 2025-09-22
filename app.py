# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from dbconnection import DatabaseConnection
from models import Student, Admin
from logger_utils import Logger
from exceptions import DatabaseConnectionError, DuplicateFeedbackError, AuthenticationError, FileHandlingError
from config import SECRET_KEY, LOG_FILE
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialize DB and utilities
db = DatabaseConnection()
logger = Logger()

# Initialize model wrappers
student_model = Student(db)
admin_model = Admin(db)

# Utility decorators
def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("student"):
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            flash("Admin login required.", "warning")
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper

def ensure_db_connection():
    try:
        db.connect()
    except DatabaseConnectionError as e:
        logger.write_log(f"App startup DB connection failed: {e}", level="error")
        print("Database connection issue. Check app.log for details.")

@app.route('/')
def index():
    return render_template("index.html")

# ---------- Student Registration ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            # hash the password before storing
            hashed_pw = generate_password_hash(password)
            sid = student_model.register(name, email, hashed_pw)
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            logger.write_log(f"Registration exception for {email}: {e}", level="error")
            flash(f"Registration failed: {str(e)}", "danger")
            return render_template("register.html", name=name, email=email)
    return render_template("register.html")

# ---------- Student Login ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            user = student_model.get_by_email(email)
            if not user or not check_password_hash(user['password'], password):
                raise AuthenticationError("Invalid email or password.")

            session['student'] = {
                "student_id": user['student_id'],
                "name": user['name'],
                "email": user['email']
            }
            flash("Logged in successfully.", "success")
            return redirect(url_for("submit_feedback"))
        except AuthenticationError as e:
            flash(str(e), "danger")
            return render_template("login.html", email=email)
        except Exception as e:
            logger.write_log(f"Login error for {email}: {e}", level="error")
            flash("An error occurred during login.", "danger")
            return render_template("login.html", email=email)
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('student', None)
    session.pop('admin', None)
    flash("Logged out.", "info")
    return redirect(url_for('index'))

# ---------- Feedback Submission ----------
@app.route('/submit_feedback', methods=['GET', 'POST'])
@login_required
def submit_feedback():
    student = session.get('student')
    cursor = db.get_cursor()
    try:
        cursor.execute("SELECT * FROM courses")
        courses = cursor.fetchall()
    finally:
        cursor.close()

    if request.method == 'POST':
        course_id = request.form.get("course_id")
        rating = int(request.form.get("rating"))
        comments = request.form.get("comments")
        try:
            fid = student_model.submit_feedback(student['student_id'], course_id, rating, comments)
            flash("Feedback submitted. Thank you!", "success")
            return redirect(url_for('submit_feedback'))
        except DuplicateFeedbackError as e:
            flash(str(e), "warning")
            return render_template("submit_feedback.html", courses=courses)
        except Exception as e:
            logger.write_log(f"Submit feedback error for student {student['student_id']}: {e}", level="error")
            flash("Failed to submit feedback. Try again later.", "danger")
            return render_template("submit_feedback.html", courses=courses)

    return render_template("submit_feedback.html", courses=courses)

# ---------- Admin login ----------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        try:
            # Fetch admin by username (plain-text password comparison)
            admin = admin_model.get_by_username(username)
            if not admin or admin['password'] != password:
                raise AuthenticationError("Invalid username or password.")

            session['admin'] = {
                "admin_id": admin['id'],
                "username": admin['username']
            }
            flash("Admin logged in.", "success")
            return redirect(url_for("admin_view_feedback"))
        except AuthenticationError as e:
            flash(str(e), "danger")
            return render_template("admin_login.html", username=username)
        except Exception as e:
            print("erorr",e)
            logger.write_log(f"Admin login error for {username}: {e}", level="error")
            flash("Admin login error.", "danger")
            return render_template("admin_login.html", username=username)
    return render_template("admin_login.html")

# ---------- Admin view feedback ----------
@app.route('/admin/view_feedback')
@admin_required
def admin_view_feedback():
    try:
        rows = admin_model.view_all_feedback()
        return render_template("admin_view_feedback.html", rows=rows)
    except Exception as e:
        logger.write_log(f"Error fetching feedback for admin: {e}", level="error")
        flash("Failed to load feedback.", "danger")
        return render_template("admin_view_feedback.html", rows=[])

# ---------- Download logs (admin only) ----------
@app.route('/admin/download_logs')
@admin_required
def download_logs():
    try:
        if not os.path.exists(LOG_FILE):
            raise FileHandlingError("Log file not found.")
        return send_file(LOG_FILE, as_attachment=True)
    except FileHandlingError as e:
        logger.write_log(f"Log download error: {e}", level="error")
        flash(str(e), "danger")
        return redirect(url_for("admin_view_feedback"))
    except Exception as e:
        logger.write_log(f"Unexpected error when admin downloaded logs: {e}", level="error")
        flash("Error downloading logs.", "danger")
        return redirect(url_for("admin_view_feedback"))

if __name__ == "__main__":
    open(LOG_FILE, 'a').close()
    app.run(debug=True)
