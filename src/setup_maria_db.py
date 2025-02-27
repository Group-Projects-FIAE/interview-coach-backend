import mariadb
import sys

def get_mariadb_connection(db_name: str = "test_db") -> mariadb.Connection:
    try:
        connection = mariadb.connect(
            user="root",
            password="root",
            host="localhost",
            port=3306
        )
        cursor = connection.cursor()
        if db_name:
            cursor.execute(f"USE {db_name}")  # Falls eine DB angegeben ist, wird sie verwendet
        return connection
    except mariadb.Error as e:
        print(f"Fehler beim Verbinden mit MariaDB: {e}")
        sys.exit(1)

# Use if you just created a new mariadb container without db
def create_database():
    print("creating database test_db")
    try:
        connection = get_mariadb_connection()
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS test_db")
        connection.commit()
        print("Datenbank 'test_db' wurde erstellt oder existiert bereits.")
    except mariadb.Error as e:
        print("Fehler beim Erstellen der Datenbank:", e)
    finally:
        if connection:
            cursor.close()
            connection.close()

def create_user_db():
    try:
        connection = get_mariadb_connection()
        cursor = connection.cursor()
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS user (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL
                )
            """)
        connection.commit()
    except mariadb.Error as e:
        print("Error while creating user db", e)
    finally:
        if connection:
            cursor.close()
            connection.close()

def list_databases():
    try:
        connection = get_mariadb_connection()
        cursor = connection.cursor()
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        print("Verfügbare Datenbanken:")
        for db in databases:
            print(f"  - {db[0]}") # Rückgabe die wir suchen steckt in einem Tupel
    except mariadb.Error as e:
        print("Error while listing databases", e)
    finally:
        if connection:
            cursor.close()
            connection.close()

def print_table():
    try:
        connection = get_mariadb_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM user")
        rows = cursor.fetchall() 
        if not rows:
            print("Keine Benutzer gefunden.")
            exit
        else:
            print("Benutzer in der Tabelle 'user':")
        for row in rows:
            print(row)  # Gibt jede Zeile aus
    except mariadb.Error as e:
        print("Error while printing user database", e)
    finally:
        if connection:
            cursor.close()
            connection.close()

