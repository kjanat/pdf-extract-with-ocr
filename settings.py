import os
import logging

# Load local dev environment if present
from dotenv import load_dotenv
load_dotenv(".env", override=False)

logger = logging.getLogger(__name__)

IS_DOCKER = os.getenv("IS_DOCKER_CONTAINER") == "true"

# Default to SQLite for local dev
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")

# Default to memory broker (disables Redis & Celery async)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "memory://")

# Celery result backend
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)

# Log configuration
logger.info(f"Configuration loaded:")
logger.info(f"  IS_DOCKER = {IS_DOCKER}")
logger.info(f"  DATABASE_URL = {DATABASE_URL}")
logger.info(f"  CELERY_BROKER_URL = {CELERY_BROKER_URL}")
