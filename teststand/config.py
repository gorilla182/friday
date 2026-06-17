import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "data" / "teststand.db"

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-for-teststand-only")
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-jwt-secret-for-teststand-only")
JWT_EXPIRY_HOURS = 24

MIN_PASSWORD_LENGTH = 6
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# Rate limit for edge-case endpoint (requests per minute per IP)
RATE_LIMIT_PER_MINUTE = 5
