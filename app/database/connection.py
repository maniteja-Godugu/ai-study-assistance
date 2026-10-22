import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from app.database.base import Base
import logging

logger = logging.getLogger(__name__)


load_dotenv(".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured")

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )
   

except (ImportError, SQLAlchemyError) as exc:
    logger.exception("Database connection check failed")

    raise RuntimeError(
        "Failed to initialize the database engine"
    ) from exc





