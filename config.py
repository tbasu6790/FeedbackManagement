# config.py
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "kol@mind1"),
    "database": os.getenv("DB_NAME", "feedback_system"),
    "port": int(os.getenv("DB_PORT", 3306))
}

SECRET_KEY = os.getenv("SECRET_KEY", "titli1234@mindteck")
LOG_FILE = os.getenv("LOG_FILE", "app.log")
