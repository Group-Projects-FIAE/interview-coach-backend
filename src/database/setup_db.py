import logging
from setup_maria_db import create_tables, list_tables, db_settings

# Configure logging
logger = logging.getLogger(__name__)

def initialize_database():
    logger.info("Initializing database...")
    create_tables()
    logger.info("Verifying tables...")
    list_tables(db_settings.DB_NAME)

if __name__ == "__main__":
    initialize_database() 