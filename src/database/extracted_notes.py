import mariadb
import logging
from . import setup_maria_db
from .setup_maria_db import db_settings
import time

# Configure logging
logger = logging.getLogger(__name__)

def create_extracted_notes(session_id: str, notes: str):
    connection = None
    try:
        connection = setup_maria_db.get_db_connection(db_settings.DB_NAME)
        cursor = connection.cursor()

        query = """INSERT INTO ExtractedNotes (session_id, notes, created_at)
        VALUES (%s, %s, FROM_UNIXTIME(%s))"""
        values = (session_id, notes, time.time())
        cursor.execute(query, values)

        connection.commit()

    except mariadb.Error as e:
        logger.error(f"Error while trying to insert extracted notes: {e}")
        logger.error(f"Session ID: {session_id}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_extracted_notes(session_id: str):
    connection = None
    try:
        connection = setup_maria_db.get_db_connection(db_settings.DB_NAME)
        cursor = connection.cursor()

        query = "SELECT notes, created_at FROM ExtractedNotes WHERE session_id = %s"
        cursor.execute(query, (session_id,))

        result = cursor.fetchall()
        return result

    except mariadb.Error as e:
        logger.error(f"Error while trying to retrieve extracted notes: {e}")
        logger.error(f"Session ID: {session_id}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()
