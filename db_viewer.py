import sqlite3
import pandas as pd
import os

DB_FILE = "hospital.db"

def view_data():
    """
    Connect to hospital.db and check data.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        
        # 1. Check Total Counts
        cursor = conn.cursor()
        cursor.execute("SELECT type, COUNT(*) FROM places GROUP BY type")
        counts = cursor.fetchall()
        print("=== Data Summary ===")
        for type_, count in counts:
            print(f"- {type_}: {count} rows")
            
        print("\n=== Verification: Seoul Pharmacies (Limit 5) ===")
        # 2. Query 5 Pharmacies in Seoul
        df = pd.read_sql_query(
            "SELECT hpid, dutyName, dutyAddr, dutyTel1, type FROM places WHERE dutyAddr LIKE '%서울%' AND type='약국' LIMIT 5",
            conn
        )
        
        if df.empty:
            print("No data found for Seoul Pharmacies yet.")
        else:
            print(df.to_string(index=False))
            
        conn.close()
        
    except Exception as e:
        print(f"Error viewing database: {e}")

if __name__ == "__main__":
    if not os.path.exists(DB_FILE):
        print(f"Database {DB_FILE} not found. Run collector.py first.")
    else:
        view_data()
