import mariadb
import logging
from . import setup_maria_db
from .setup_maria_db import db_settings

# Configure logging
logger = logging.getLogger(__name__)

def save_chat_message(session_id: str, sender: str, message: str):
    connection = None
    try:
        connection = setup_maria_db.get_db_connection(db_settings.DB_NAME)
        cursor = connection.cursor()

        query = """INSERT INTO ChatHistory (session_id, sender, message_text) VALUES (%s, %s, %s)"""
        values = (session_id, sender, message)
        cursor.execute(query, values)

        connection.commit()

    except mariadb.Error as e:
        logger.error(f"Error while trying to save chat message: {e}")
        logger.error(f"Message details: session_id={session_id}, sender={sender}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_chat_history(session_id: str):
    connection = None
    try:
        connection = setup_maria_db.get_db_connection(db_settings.DB_NAME)
        cursor = connection.cursor()

        query = """SELECT sender, message_text, timestamp FROM ChatHistory WHERE session_id = %s ORDER BY timestamp ASC"""
        cursor.execute(query, (session_id,))

        chat_history = []
        for (sender, message_text, timestamp) in cursor:
            chat_history.append({
                "sender": sender,
                "message": message_text,
                "timestamp": timestamp
            })
        return chat_history

    except mariadb.Error as e:
        logger.error(f"Error while retrieving chat history: {e}")
        logger.error(f"Session ID: {session_id}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def save_extracted_notes(session_id: str, note_text: str):
    connection = None
    try:
        connection = setup_maria_db.get_db_connection(db_settings.DB_NAME)
        cursor = connection.cursor()

        query = """INSERT INTO ExtractedNotes (session_id, note_text) VALUES (%s, %s)"""
        values = (session_id, note_text)
        cursor.execute(query, values)

        connection.commit()

    except mariadb.Error as e:
        logger.error(f"Error while trying to save extracted note: {e}")
        logger.error(f"Note details: session_id={session_id}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_extracted_notes(session_id: str):
    connection = None
    try:
        connection = setup_maria_db.get_db_connection(db_settings.DB_NAME)
        cursor = connection.cursor()

        query = """SELECT note_text, timestamp FROM ExtractedNotes WHERE session_id = %s ORDER BY timestamp ASC"""
        cursor.execute(query, (session_id,))

        notes = []
        for (note_text, timestamp) in cursor:
            notes.append({
                "note": note_text,
                "timestamp": timestamp
            })
        return notes

    except mariadb.Error as e:
        logger.error(f"Error while retrieving extracted notes: {e}")
        logger.error(f"Session ID: {session_id}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

#save_chat_history("0", True, "This is a test message!")
#setup_maria_db.print_table("ChatHistory")
#get_chat_history(0)