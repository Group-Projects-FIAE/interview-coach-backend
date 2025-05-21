import mariadb
import logging
from . import setup_maria_db
from .setup_maria_db import db_settings
import time

# Configure logging
logger = logging.getLogger(__name__)

def create_interview_feedback(session_id: str, feedback: str):
    connection = None
    try:
        connection = setup_maria_db.get_db_connection(db_settings.DB_NAME)
        cursor = connection.cursor()

        query = """INSERT INTO InterviewFeedback (session_id, feedback, created_at)
        VALUES (%s, %s, FROM_UNIXTIME(%s))"""
        values = (session_id, feedback, time.time())
        cursor.execute(query, values)

        connection.commit()

    except mariadb.Error as e:
        logger.error(f"Error while trying to insert interview feedback: {e}")
        logger.error(f"Session ID: {session_id}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_interview_feedback(session_id: str):
    connection = None
    try:
        connection = setup_maria_db.get_db_connection(db_settings.DB_NAME)
        cursor = connection.cursor()

        query = "SELECT feedback, created_at FROM InterviewFeedback WHERE session_id = %s"
        cursor.execute(query, (session_id,))

        result = cursor.fetchall()
        return result

    except mariadb.Error as e:
        logger.error(f"Error while trying to retrieve interview feedback: {e}")
        logger.error(f"Session ID: {session_id}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close() 