import sqlite3
from datetime import datetime, timedelta
import json
import os

# Get the absolute path of the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Point to the database folder inside your project
DB_PATH = os.path.join(BASE_DIR, 'database', 'study_planner.db')

def run_simulation():
    # Ensure the database directory exists before trying to connect
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    #def run_simulation():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🚀 Starting simulation: Inserting 15 days of behavioral data...")

    for i in range(15, 0, -1):
        log_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
    # Force a strong correlation between Sleep and Completion
    for i in range(1, 15):
        sleep = 4 + (i * 0.4) # Sleep goes from 4.4 to 10.0
        completion = 40 + (i * 4) # Completion goes from 44% to 100%
    # Insert this into your daily_logs and plans tables  
        # Simulate a burnout trend in the last 3 days
        if i <= 3:
            mood, energy, stress, sleep, completion = 3, 3, 9, 5.0, 40
        else:
            mood, energy, stress, sleep, completion = 7, 8, 4, 7.5, 95

        # 1. Insert Daily Logs (Behavioral Data)
        cursor.execute("""
            INSERT INTO daily_logs (log_date, mood_score, energy_score, stress_score, sleep_hours)
            VALUES (?, ?, ?, ?, ?)
        """, (log_date, mood, energy, stress, sleep))

        # 2. Insert Plans (Execution Data)
        subjects = json.dumps([{"name": "Cybersecurity", "difficulty": 8, "days_until_exam": i+5}])
        cursor.execute("""
            INSERT INTO plans (plan_date, input_available_hours, input_subjects, 
                               input_difficulty_avg, output_allocated_hours, 
                               output_completion_pct, phase_at_creation)
            VALUES (?, 6.0, ?, 8.0, 4.8, ?, 'bootstrapping')
        """, (log_date, subjects, completion))

    conn.commit()
    conn.close()
    print("✅ Simulation complete. System should now be in 'Adaptive Phase'.")

if __name__ == "__main__":
    run_simulation()
