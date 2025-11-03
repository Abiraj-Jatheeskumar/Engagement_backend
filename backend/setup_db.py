"""
Database setup script
Run this to initialize the database
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db, engine, Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize database"""
    logger.info("Initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

