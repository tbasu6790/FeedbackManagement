# models.py
from dbconnection import DatabaseConnection
from logger_utils import Logger
from exceptions import DuplicateFeedbackError, AuthenticationError
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash


class Student:
    def __init__(self, db: DatabaseConnection):
        self.db = db
        self.logger = Logger()

    def register(self, name: str, email: str, password: str) -> int:
        """Register a new student with hashed password."""
        cursor = self.db.get_cursor()
        hashed = generate_password_hash(password)  # Keep student password hashed
        try:
            sql = "INSERT INTO students (name, email, password) VALUES (%s, %s, %s)"
            cursor.execute(sql, (name, email, hashed))
            self.db.conn.commit()
            student_id = cursor.lastrowid
            self.logger.write_log(
                f"Registration success for email={email}, student_id={student_id}"
            )
            return student_id
        except Error as e:
            self.db.conn.rollback()
            self.logger.write_log(
                f"Registration failed for email={email}: {e}", level="error"
            )
            raise e
        finally:
            cursor.close()

    def login(self, email: str, password: str) -> dict:
        """Validate student login with hashed password."""
        cursor = self.db.get_cursor()
        try:
            sql = "SELECT * FROM students WHERE email = %s"
            cursor.execute(sql, (email,))
            row = cursor.fetchone()
            if row and check_password_hash(row["password"], password):
                self.logger.write_log(
                    f"Login success for student_id={row['student_id']}"
                )
                return row
            else:
                self.logger.write_log(
                    f"Login failed for email={email}", level="warning"
                )
                raise AuthenticationError("Invalid student credentials")
        finally:
            cursor.close()

    def submit_feedback(
        self, student_id: int, course_id: int, rating: int, comments: str
    ) -> int:
        """Submit feedback, ensuring no duplicate submission per course/student."""
        cursor = self.db.get_cursor()
        try:
            # check duplicate
            sql_check = "SELECT * FROM feedback WHERE student_id = %s AND course_id = %s"
            cursor.execute(sql_check, (student_id, course_id))
            if cursor.fetchone():
                self.logger.write_log(
                    f"Duplicate feedback attempt by student_id={student_id} for course_id={course_id}",
                    level="warning",
                )
                raise DuplicateFeedbackError(
                    "You have already submitted feedback for this course."
                )

            sql_insert = "INSERT INTO feedback (student_id, course_id, rating, comments) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql_insert, (student_id, course_id, rating, comments))
            self.db.conn.commit()
            fid = cursor.lastrowid
            self.logger.write_log(
                f"Feedback submitted by student_id={student_id} for course_id={course_id}, feedback_id={fid}"
            )
            return fid
        except Error as e:
            self.db.conn.rollback()
            self.logger.write_log(f"Error while submitting feedback: {e}", level="error")
            raise e
        finally:
            cursor.close()


class Admin:
    def __init__(self, db: DatabaseConnection):
        self.db = db
        self.logger = Logger()

    def get_by_username(self, username: str) -> dict | None:
        """Fetch admin details by username without password validation."""
        cursor = self.db.get_cursor()
        try:
            sql = "SELECT * FROM admins WHERE username = %s"
            cursor.execute(sql, (username,))
            return cursor.fetchone()  # returns None if not found
        finally:
            cursor.close()

    def login(self, username: str, password: str) -> dict:
        """Validate admin login with plain-text password."""
        cursor = self.db.get_cursor()
        try:
            sql = "SELECT * FROM admins WHERE username = %s"
            cursor.execute(sql, (username,))
            row = cursor.fetchone()
            if row and row["password"] == password:  # plain-text comparison
                self.logger.write_log(f"Admin login success: username={username}")
                return row
            else:
                self.logger.write_log(
                    f"Admin login failed: username={username}", level="warning"
                )
                raise AuthenticationError("Invalid admin credentials")
        finally:
            cursor.close()

    def view_all_feedback(self) -> list[dict]:
        """Return all feedback records with student and course details."""
        cursor = self.db.get_cursor()
        try:
            sql = """
            SELECT f.feedback_id, s.student_id, s.name AS student_name, s.email,
                   c.course_id, c.course_name, c.faculty_name,
                   f.rating, f.comments, f.created_at
            FROM feedback f
            JOIN students s ON f.student_id = s.student_id
            JOIN courses c ON f.course_id = c.course_id
            ORDER BY f.created_at DESC
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()


class Feedback:
    """Simple Feedback data holder (not tied to DB operations)."""

    def __init__(self, student_id: int, course_id: int, rating: int, comments: str):
        self.student_id = student_id
        self.course_id = course_id
        self.rating = rating
        self.comments = comments
