import mariadb
import logging
from . import setup_maria_db
from .setup_maria_db import db_settings
import time

# Configure logging
logger = logging.getLogger(__name__)

def create_job_description(session_id: str, job_title: str, job_details: str, job_url: str = None):
    connection = None
    try:
        connection = setup_maria_db.get_db_connection(db_settings.DB_NAME)
        cursor = connection.cursor()

        query = """INSERT INTO JobDescriptions (session_id, job_title, job_url, job_details, created_at)
        VALUES (%s, %s, %s, %s, FROM_UNIXTIME(%s))"""
        values = (session_id, job_title, job_url, job_details, time.time())
        cursor.execute(query, values)

        connection.commit()

    except mariadb.Error as e:
        logger.error(f"Error while trying to insert new job description: {e}")
        logger.error(f"Details: session_id={session_id}, job_title={job_title}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_job_description(session_id: str):
    connection = None
    try:
        connection = setup_maria_db.get_db_connection(db_settings.DB_NAME)
        cursor = connection.cursor()

        query = "SELECT job_title, job_url, job_details, created_at FROM JobDescriptions WHERE session_id = %s"
        cursor.execute(query, (session_id,))

        result = cursor.fetchall()
        return result
    
    except mariadb.Error as e:
        logger.error(f"Error while trying to retrieve job description: {e}")
        logger.error(f"Session ID: {session_id}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

#create_job_description("0", "Datenbanktester", "This is a test message!")
#setup_maria_db.print_table("JobDescriptions")
#print(get_job_description(0))
