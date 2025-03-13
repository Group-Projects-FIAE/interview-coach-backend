import mariadb
import setup_maria_db
import time

def save_chat_message(session_id: int, is_user_message: bool, message: str):
    try:
        connection = setup_maria_db.get_db_connection(setup_maria_db.DB_NAME)
        cursor = connection.cursor()

        sender = "user" if is_user_message else "ai"

        query = """INSERT INTO ChatHistory (session_id, sender, message_text, timestamp)
        VALUES (%s, %s, %s, FROM_UNIXTIME(%s))"""
        values = (session_id, sender, message, time.time())
        cursor.execute(query, values)

        connection.commit()

    except mariadb.Error as e:
        print("Error while trying to insert new chat message:", e)
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_chat_history(session_id: str):
    try:
        connection = setup_maria_db.get_db_connection(setup_maria_db.DB_NAME)
        cursor = connection.cursor()

        query = "SELECT * FROM ChatHistory WHERE session_id = %s"
        cursor.execute(query, (session_id,))

        connection.commit()

        return cursor.fetchall()
    
    except mariadb.Error as e:
        print("Error while trying to retrieve chat history:", e)
    finally:
        if connection:
            cursor.close()
            connection.close()

#save_chat_history("0", True, "This is a test message!")
#setup_maria_db.print_table("ChatHistory")
get_chat_history(0)