import mariadb
import setup_maria_db
import time

def create_job_description(session_id: int, job_title: str, job_details: str, job_url: str = None):
    try:
        connection = setup_maria_db.get_db_connection(setup_maria_db.DB_NAME)
        cursor = connection.cursor()

        query = """INSERT INTO JobDescriptions (session_id, job_title, job_url, job_details, created_at)
        VALUES (%s, %s, %s, %s, FROM_UNIXTIME(%s))"""
        values = (session_id, job_title, job_url, job_details, time.time())
        cursor.execute(query, values)

        connection.commit()

    except mariadb.Error as e:
        print("Error while trying to insert new job description:", e)
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_job_description(session_id: str):
    try:
        connection = setup_maria_db.get_db_connection(setup_maria_db.DB_NAME)
        cursor = connection.cursor()

        query = "SELECT * FROM JobDescriptions WHERE session_id = %s"
        cursor.execute(query, (session_id,))

        connection.commit()
        return cursor.fetchall()
    
    except mariadb.Error as e:
        print("Error while trying to retrieve job description:", e)
    finally:
        if connection:
            cursor.close()
            connection.close()

#create_job_description("0", "Datenbanktester", "This is a test message!")
#setup_maria_db.print_table("JobDescriptions")
#print(get_job_description(0))
