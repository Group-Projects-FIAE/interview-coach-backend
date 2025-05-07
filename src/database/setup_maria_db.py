import mariadb
import sys, time
import os
import logging
from pydantic_settings import BaseSettings
from pydantic import Field

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseSettings(BaseSettings):
    DB_NAME: str = Field(..., description="Database name")
    DB_USER: str = Field(..., description="Database user")
    DB_USER_PASSWORD: str = Field(..., description="Database password")
    DB_HOST: str = Field(default="localhost", description="Database host")
    DB_PORT: int = Field(default=3307, description="Database port")

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        env_file_encoding = "utf-8"
        env_prefix = ""
        extra = "ignore"  # This will ignore extra fields in the .env file

logger.debug(f"Current working directory: {os.getcwd()}")
logger.debug(f"Looking for .env file at: {os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')}")
logger.debug(f"Environment variables: {os.environ.get('DB_NAME')}, {os.environ.get('DB_USER')}, {os.environ.get('DB_USER_PASSWORD')}")

try:
    db_settings = DatabaseSettings()
    logger.info("Successfully loaded database settings:")
    logger.debug(f"DB_NAME: {db_settings.DB_NAME}")
    logger.debug(f"DB_USER: {db_settings.DB_USER}")
    logger.debug(f"DB_HOST: {db_settings.DB_HOST}")
    logger.debug(f"DB_PORT: {db_settings.DB_PORT}")
except Exception as e:
    logger.error(f"Error loading database settings: {e}")
    logger.error("Please check your .env file and make sure all required variables are set")
    sys.exit(1)

def get_db_connection(db_name: str = None) -> mariadb.Connection:
    try:
        connection = mariadb.connect(
            user=db_settings.DB_USER,
            password=db_settings.DB_USER_PASSWORD,
            host=db_settings.DB_HOST,
            port=db_settings.DB_PORT
        )
        cursor = connection.cursor()
        if db_name:
            cursor.execute(f"USE {db_name}")  # If a database is specified, it will be selected
        return connection
    except mariadb.Error as e:
        logger.error(f"Error connecting to MariaDB: {e}")
        logger.error(f"Connection details: host={db_settings.DB_HOST}, port={db_settings.DB_PORT}, user={db_settings.DB_USER}")
        sys.exit(1)


# Run if you created a new mariadb container
def create_tables():
    logger.info("Creating databases...")
    connection = None
    try:
        connection = get_db_connection(db_settings.DB_NAME)
        cursor = connection.cursor()

        create_tables_sql = [
            """CREATE TABLE IF NOT EXISTS Users (
                user_id VARCHAR(36) PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS Sessions (
                session_id VARCHAR(50) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
            )""",
            """CREATE TABLE IF NOT EXISTS ChatHistory (
                message_id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(50),
                sender ENUM('user', 'ai') NOT NULL,
                message_text TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES Sessions(session_id) ON DELETE CASCADE
            )""",
            """CREATE TABLE IF NOT EXISTS JobDescriptions (
                job_id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(36) NOT NULL,
                job_title VARCHAR(255) NOT NULL,
                job_url VARCHAR(500),
                job_details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES Sessions(session_id) ON DELETE CASCADE
            )""",
            """CREATE TABLE IF NOT EXISTS UserPreferences (
                preference_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL UNIQUE,
                dark_mode BOOLEAN DEFAULT FALSE,
                language VARCHAR(20) DEFAULT 'en',
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
            )""",
             """CREATE TABLE IF NOT EXISTS ExtractedNotes (
                note_id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(50),
                note_text TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES Sessions(session_id) ON DELETE CASCADE
            )"""
        ]

        for create_table_sql in create_tables_sql:
            cursor.execute(create_table_sql)
        
        connection.commit()
        logger.info("Successfully created databases!")

    except mariadb.Error as e:
        logger.error(f"Error creating database: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

### Debugging methods ###
def list_databases(db_name : str = None):
    connection = None # Needed for finally block
    try:
        connection = get_db_connection(db_name)
        cursor = connection.cursor()
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        logger.info("Available databases:")
        for db in databases:
            logger.info(f"  - {db[0]}") # Get return values from tuple
    
    except mariadb.Error as e:
        logger.error(f"Error while listing databases/tables: {e}")
    
    finally:
        if connection:
            cursor.close()
            connection.close()

def list_tables(db_name : str):
    connection = None
    try:
        connection = get_db_connection(db_name)
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        databases = cursor.fetchall()
        logger.info("Available tables:")
        for db in databases:
            logger.info(f"  - {db[0]}") # Get return values from tuple
    
    except mariadb.Error as e:
        logger.error(f"Error while listing tables: {e}")
    
    finally:
        if connection:
            cursor.close()
            connection.close()

def print_table(table_name: str):
    connection = None # Needed for finally block
    try:
        connection = get_db_connection(db_settings.DB_NAME)
        cursor = connection.cursor()

        query = f"SELECT * FROM {table_name}"
        cursor.execute(query)

        for row in cursor.fetchall():
            logger.info(row)

    except mariadb.Error as e:
        logger.error(f"Error while trying to print table {table_name}: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def create_test_user():
    connection = None # Needed for finally block
    try:
        connection = get_db_connection(db_settings.DB_NAME)
        cursor = connection.cursor()

        uuid_example = "cbe0c97f-4552-4ef4-8b25-358060737016"

        query = """INSERT INTO Users (user_id, created_at) VALUES (%s, FROM_UNIXTIME(%s))"""
        values = (uuid_example, time.time())
        cursor.execute(query, values)

        connection.commit()
        logger.info(f"Successfully created test user with UUID: {uuid_example}")

    except mariadb.Error as e:
        logger.error(f"Error while creating test user: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

#create_tables()
#list_databases()
#list_tables("interviewcoach")
#create_test_user()