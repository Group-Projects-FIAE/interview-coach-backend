import mariadb
import time
import setup_maria_db

def create_session(session_id: str, user_id: str):
    try:
        connection = setup_maria_db.get_db_connection(setup_maria_db.DB_NAME)
        cursor = connection.cursor()

        query = """INSERT INTO Sessions (session_id, user_id, start_time)
        VALUES (%s, %s, FROM_UNIXTIME(%s))"""
        values = (session_id, user_id, time.time())

        cursor.execute(query, values)

        connection.commit()

    except mariadb.Error as e:
        print("Error while trying to insert new session:", e)
    finally:
        if connection:
            cursor.close()
            connection.close()

#create_session("0", "cbe0c97f-4552-4ef4-8b25-358060737016")
#setup_maria_db.print_table("Sessions")