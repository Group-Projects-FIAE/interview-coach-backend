import mariadb
import time
from . import setup_maria_db
from .setup_maria_db import db_settings

def create_session(session_id: str, user_id: str):
    connection = None
    try:
        connection = setup_maria_db.get_db_connection(db_settings.DB_NAME)
        cursor = connection.cursor()

        # Start transaction
        connection.autocommit = False

        # Check if user already exists
        cursor.execute("SELECT user_id FROM Users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            # Create a new user for the session
            query = """INSERT INTO Users (user_id, created_at) VALUES (%s, FROM_UNIXTIME(%s))"""
            values = (user_id, time.time())
            cursor.execute(query, values)

        # Create the session
        query = """INSERT INTO Sessions (session_id, user_id, start_time)
        VALUES (%s, %s, FROM_UNIXTIME(%s))"""
        values = (session_id, user_id, time.time())
        cursor.execute(query, values)

        # Commit the transaction
        connection.commit()
        return True

    except mariadb.Error as e:
        print("Error while trying to insert new session:", e)
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.autocommit = True
            cursor.close()
            connection.close()

def get_job_description(session_id: str):
    try:
        connection = setup_maria_db.get_db_connection(db_settings.DB_NAME)
        cursor = connection.cursor()

        query = "SELECT * FROM Sessions WHERE session_id = %s"
        cursor.execute(query, (session_id,))

        connection.commit()
        return cursor.fetchall()
    
    except mariadb.Error as e:
        print("Error while trying to retrieve session:", e)
    finally:
        if connection:
            cursor.close()
            connection.close()

#create_session("0", "cbe0c97f-4552-4ef4-8b25-358060737016")
#setup_maria_db.print_table("Sessions")