import mariadb
from database import setup_maria_db
import time


def create_extracted_note(session_id: int, note_text: str):
    try:
        connection = setup_maria_db.get_db_connection(setup_maria_db.DB_NAME)
        cursor = connection.cursor()

        query = """INSERT INTO ExtractedNotes (session_id, note_text, created_at) VALUES (%s, %s, %s, FROM_UNIXTIME(%s))"""
        values = (session_id, note_text, time.time())
        cursor.execute(query, values)

        connection.commit()

    except mariadb.Error as e:
        print("Error while trying to insert new extracted note:", e)
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_extracted_note(session_id: str):
    try:
        connection = setup_maria_db.get_db_connection(setup_maria_db.DB_NAME)
        cursor = connection.cursor()

        query = "SELECT * FROM ExtractedNotes WHERE session_id = %s"
        cursor.execute(query, (session_id,))

        connection.commit()
        return cursor.fetchall()
    
    except mariadb.Error as e:
        print("Error while trying to retrieve extracted notes:", e)
    finally:
        if connection:
            cursor.close()
            connection.close()
