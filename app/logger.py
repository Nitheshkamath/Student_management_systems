import logging
from logging.handlers import RotatingFileHandler
import os

# Create logs directory if not exists
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Configure logger
log_file = os.path.join(log_dir, "student_management.log")

log_formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
)

handler = RotatingFileHandler(
    log_file, maxBytes=5 * 1024 * 1024, backupCount=5
)
handler.setFormatter(log_formatter)
handler.setLevel(logging.INFO)

logger = logging.getLogger("student_managements_system")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False
