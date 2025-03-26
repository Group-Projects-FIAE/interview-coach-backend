import mariadb
from database import setup_maria_db

def create_user_preference(user_id: int, darkmode: str, language: str):
    try:
        connection = setup_maria_db.get_db_connection(setup_maria_db.DB_NAME)
        cursor = connection.cursor()

        query = """INSERT INTO UserPreferences (user_id, darkmode, language) VALUES (%s, %s, %s)"""
        values = (user_id, darkmode, language)
        cursor.execute(query, values)

        connection.commit()

    except mariadb.Error as e:
        print("Error while trying to insert new user preference:", e)
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_user_preference(user_id: str):
    try:
        connection = setup_maria_db.get_db_connection(setup_maria_db.DB_NAME)
        cursor = connection.cursor()

        query = "SELECT * FROM UserPreference WHERE user_id = %s"
        cursor.execute(query, (user_id,))

        connection.commit()
        return cursor.fetchall()
    
    except mariadb.Error as e:
        print("Error while trying to retrieve user preference:", e)
    finally:
        if connection:
            cursor.close()
            connection.close()

