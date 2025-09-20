# db_connection.py
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG
from exceptions import DatabaseConnectionError
from logger_utils import Logger

class DatabaseConnection:
    def __init__(self, config=DB_CONFIG):
        self.config = config
        self.conn = None
        self.logger = Logger()

    def connect(self):
        try:
            self.conn = mysql.connector.connect(
                host=self.config.get("host"),
                user=self.config.get("user"),
                password=self.config.get("password"),
                database=self.config.get("database"),
                port=self.config.get("port")
            )
            if self.conn.is_connected():
                self.logger.write_log("Database connected successfully.")
                return self.conn
            else:
                raise DatabaseConnectionError("Unable to connect to database.")
        except Error as e:
            self.logger.write_log(f"Database connection failed: {e}", level="error")
            raise DatabaseConnectionError(str(e))

    def disconnect(self):
        try:
            if self.conn and self.conn.is_connected():
                self.conn.close()
                self.logger.write_log("Database connection closed.")
        except Error as e:
            self.logger.write_log(f"Error when closing DB connection: {e}", level="error")

    def get_cursor(self):
        if not self.conn or not self.conn.is_connected():
            self.connect()
        return self.conn.cursor(dictionary=True)
