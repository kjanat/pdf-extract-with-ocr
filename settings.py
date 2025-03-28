import os

# Load local dev environment if present
from dotenv import load_dotenv
load_dotenv(".env.dev", override=True)

IS_DOCKER = os.getenv("IS_DOCKER_CONTAINER") == "true"

# Default to SQLite for local dev
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")

# Default to memory broker (disables Redis & Celery async)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "memory://")

# Enable basic logging for debugging
print(f"[config] IS_DOCKER = {IS_DOCKER}")
print(f"[config] DATABASE_URL = {DATABASE_URL}")
print(f"[config] CELERY_BROKER_URL = {CELERY_BROKER_URL}")
