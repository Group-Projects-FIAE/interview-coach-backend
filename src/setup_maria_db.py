import mariadb
import sys, time

DB_NAME = "interviewcoach"
DB_USER = "interviewcoach"
DB_USER_PASSWORD = "password"
DB_HOST="localhost"
DB_PORT=3307

def get_db_connection(db_name: str = None) -> mariadb.Connection:
    try:
        connection = mariadb.connect(
            user=DB_USER,
            password=DB_USER_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = connection.cursor()
        if db_name:
            cursor.execute(f"USE {db_name}")  # If a database is specified, it will be selected
        return connection
    except mariadb.Error as e:
        print(f"Fehler beim Verbinden mit MariaDB: {e}")
        sys.exit(1)


# Run if you created a new mariadb container
def create_tables():
    print("creating databases...")
    connection = None
    try:
        connection = get_db_connection(DB_NAME)
        cursor = connection.cursor()

        create_tables_sql = [
            """CREATE TABLE IF NOT EXISTS Users (
                user_id VARCHAR(36) PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS Sessions (
                session_id VARCHAR(50) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
            )""",
            """CREATE TABLE IF NOT EXISTS ChatHistory (
                message_id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(50),
                sender ENUM('user', 'ai') NOT NULL,
                message_text TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES Sessions(session_id) ON DELETE CASCADE
            )""",
            """CREATE TABLE IF NOT EXISTS JobDescriptions (
                job_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                job_title VARCHAR(255) NOT NULL,
                job_url VARCHAR(500),
                job_details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
            )""",
            """CREATE TABLE IF NOT EXISTS UserPreferences (
                preference_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL UNIQUE,
                dark_mode BOOLEAN DEFAULT FALSE,
                language VARCHAR(20) DEFAULT 'en',
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
            )""",
             """CREATE TABLE IF NOT EXISTS ExtractedNotes (
                note_id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(50),
                note_text TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES Sessions(session_id) ON DELETE CASCADE
            )"""
        ]

        for create_table_sql in create_tables_sql:
            cursor.execute(create_table_sql)
        
        connection.commit()
        print("Successfully created databases!")

    except mariadb.Error as e:
        print("Fehler beim Erstellen der Datenbank:", e)
    finally:
        if connection:
            cursor.close()
            connection.close()

### Debugging methods ###
def list_databases(db_name : str = None):
    connection = None # Needed for finally block
    try:
        connection = get_db_connection(db_name)
        cursor = connection.cursor()
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        print("Available databases:")
        for db in databases:
            print(f"  - {db[0]}") # Get return values from tuple
    
    except mariadb.Error as e:
        print("Error while listing databases/tables", e)
    
    finally:
        if connection:
            cursor.close()
            connection.close()

def list_tables(db_name : str):
    connection = None
    try:
        connection = get_db_connection(db_name)
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        databases = cursor.fetchall()
        print("Available tables:")
        for db in databases:
            print(f"  - {db[0]}") # Get return values from tuple
    
    except mariadb.Error as e:
        print("Error while listing tables", e)
    
    finally:
        if connection:
            cursor.close()
            connection.close()

def print_table(table_name: str):
    connection = None # Needed for finally block
    try:
        connection = get_db_connection(DB_NAME)
        cursor = connection.cursor()

        query = f"SELECT * FROM {table_name}"
        cursor.execute(query)

        for row in cursor.fetchall():
            print(row)

    except mariadb.Error as e:
        print("Error while trying to insert new chat message:", e)
    finally:
        if connection:
            cursor.close()
            connection.close()

def create_test_user():
    connection = None # Needed for finally block
    try:
        connection = get_db_connection(DB_NAME)
        cursor = connection.cursor()

        uuid_example = "cbe0c97f-4552-4ef4-8b25-358060737016"

        query = """INSERT INTO Users (user_id, created_at) VALUES (%s, FROM_UNIXTIME(%s))"""
        values = (uuid_example, time.time())
        cursor.execute(query, values)

        connection.commit()

    except mariadb.Error as e:
        print("Error while trying to insert new chat message:", e)
    finally:
        if connection:
            cursor.close()
            connection.close()

#create_tables()
list_databases()
list_tables("interviewcoach")
#create_test_user()