import logging
import logging.handlers
import sys
import os
from pathlib import Path
from config import settings


class RequestIdFormatter(logging.Formatter):
    """Custom formatter that includes request_id from context"""

    def format(self, record):
        from core.context import get_request_id
        record.request_id = get_request_id()
        return super().format(record)


def setup_logging():
    """Configure comprehensive logging with circular file rotation"""

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Log file paths
    app_log_file = log_dir / "app.log"
    error_log_file = log_dir / "error.log"
    access_log_file = log_dir / "access.log"

    # Formatters
    detailed_formatter = RequestIdFormatter(
        "%(asctime)s | [%(request_id)s] | %(name)s | %(levelname)s | "
        "%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = RequestIdFormatter(
        "%(asctime)s | [%(request_id)s] | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Root logger setup
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)

    # Rotating app log file
    app_file_handler = CircularRotatingFileHandler(
        app_log_file, maxBytes=10 * 1024 * 1024, backupCount=9, encoding="utf-8"
    )
    app_file_handler.setLevel(logging.DEBUG)
    app_file_handler.setFormatter(detailed_formatter)

    # Rotating error log file
    error_file_handler = CircularRotatingFileHandler(
        error_log_file, maxBytes=10 * 1024 * 1024, backupCount=9, encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(detailed_formatter)

    # Attach handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_file_handler)
    root_logger.addHandler(error_file_handler)

    # Configure sub-loggers
    configure_specific_loggers()

    # Startup messages
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {settings.log_level.upper()}")
    logger.info(f"Log files created in: {log_dir.absolute()}")
    logger.info("Circular rotation: 10 files maximum, cycles back to overwrite oldest")


class CircularRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Circular rotating log handler to manage app/error logs"""

    def emit(self, record):
        try:
            if self.stream is None or not os.path.exists(self.baseFilename):
                self._reopen_if_needed()
            super().emit(record)
        except Exception:
            try:
                self._reopen_if_needed()
                super().emit(record)
            except Exception as e:
                print(f"Logging error: {e}", file=sys.stderr)

    def _reopen_if_needed(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        os.makedirs(os.path.dirname(self.baseFilename), exist_ok=True)
        self.stream = self._open()

    def shouldRollover(self, record):
        if not os.path.exists(self.baseFilename):
            return False
        return super().shouldRollover(record)

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        if not os.path.exists(self.baseFilename):
            self.stream = self._open()
            return

        max_backup = self.backupCount
        if os.path.exists(f"{self.baseFilename}.{max_backup}"):
            for i in range(1, max_backup + 1):
                next_name = f"{self.baseFilename}.{i}"
                if i == max_backup and os.path.exists(next_name):
                    os.remove(next_name)
                    break

        for i in range(min(max_backup - 1, self._find_highest_backup()), 0, -1):
            src, dst = f"{self.baseFilename}.{i}", f"{self.baseFilename}.{i + 1}"
            if os.path.exists(src):
                if os.path.exists(dst):
                    os.remove(dst)
                os.rename(src, dst)

        if os.path.exists(self.baseFilename):
            dst = f"{self.baseFilename}.1"
            if os.path.exists(dst):
                os.remove(dst)
            os.rename(self.baseFilename, dst)

        self.stream = self._open()

    def _find_highest_backup(self):
        for i in range(self.backupCount, 0, -1):
            if os.path.exists(f"{self.baseFilename}.{i}"):
                return i
        return 0


def configure_specific_loggers():
    """Configure specific loggers for third-party and app modules"""

    # --- Suppress noisy third-party logs ---
    logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.ERROR)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.ERROR)
    logging.getLogger("alembic").setLevel(logging.WARNING)

    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # --- Core FastAPI logging ---
    logging.getLogger("fastapi").setLevel(logging.INFO)

    # --- Your application modules ---
    app_modules = ["services", "routes", "core", "database", "utils"]
    for module in app_modules:
        logging.getLogger(module).setLevel(logging.DEBUG)

    # --- Optional SQL log file (debug only) ---
    # Uncomment to keep SQL logs separately instead of printing
    """
    sql_log_file = Path("logs/sqlalchemy.log")
    sql_logger = logging.getLogger("sqlalchemy.engine")
    sql_handler = logging.FileHandler(sql_log_file, encoding="utf-8")
    sql_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    sql_handler.setLevel(logging.INFO)
    sql_logger.addHandler(sql_handler)
    sql_logger.propagate = False
    """


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance with proper configuration"""
    return logging.getLogger(name or __name__)
