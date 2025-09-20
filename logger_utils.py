# logger_utils.py
import logging
from logging.handlers import RotatingFileHandler
from config import LOG_FILE

class Logger:
    def __init__(self, logfile=LOG_FILE):
        self.logfile = logfile
        self._setup_logger()

    def _setup_logger(self):
        self.logger = logging.getLogger("feedback_app")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = RotatingFileHandler(self.logfile, maxBytes=5*1024*1024, backupCount=2)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def write_log(self, msg, level="info"):
        if level == "info":
            self.logger.info(msg)
        elif level == "error":
            self.logger.error(msg)
        elif level == "warning":
            self.logger.warning(msg)
        else:
            self.logger.debug(msg)
