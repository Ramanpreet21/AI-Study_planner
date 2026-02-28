import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'study_planner.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def initialize_db():
    """Reads the schema.sql file and creates the tables."""
    if not os.path.exists(DB_PATH):
        print("Initializing database...")
        with open(SCHEMA_PATH, 'r') as f:
            schema_sql = f.read()
        
        conn = get_connection()
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
        print("Database initialized successfully.")
    else:
        print("Database already exists.")

# Example function to add a daily log
def add_daily_log(log_data):
    """
    log_data: dict containing log_date, mood_score, energy_score, 
    stress_score, sleep_hours
    """
    conn = get_connection()
    query = """
        INSERT INTO daily_logs (log_date, mood_score, energy_score, stress_score, sleep_hours)
        VALUES (?, ?, ?, ?, ?)
    """
    conn.execute(query, (
        log_data['log_date'], 
        log_data['mood_score'], 
        log_data['energy_score'], 
        log_data['stress_score'], 
        log_data['sleep_hours']
    ))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Running this file directly will create the .db file
    initialize_db()
