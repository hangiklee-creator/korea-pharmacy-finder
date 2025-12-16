import os
import requests
import sqlite3
import pandas as pd
from dotenv import load_dotenv
import time

# Load Environment Variables
load_dotenv()
API_KEY = os.getenv("DATA_GO_KR_API_KEY")

# Configuration
DB_FILE = "hospital.db"
NUM_OF_ROWS = 1000 # Max rows per page

# API Endpoints
PHARMACY_URL = "http://apis.data.go.kr/B552657/ErmctInsttInfoInqireService/getParmacyListInfoInqire"
HOSPITAL_URL = "http://apis.data.go.kr/B552657/HsptlAsembySearchService/getHsptlMdcncListInfoInqire"

def init_db():
    """Initialize the SQLite database and create table if not exists."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create Table
    # Using 'INSERT OR REPLACE' logic requires a UNIQUE constraint or Primary Key.
    # hpid is the unique ID for pharmacies/hospitals.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS places (
            hpid TEXT PRIMARY KEY,
            dutyName TEXT,
            dutyAddr TEXT,
            dutyTel1 TEXT,
            wgs84Lat REAL,
            wgs84Lon REAL,
            
            dutyTime1s TEXT, dutyTime1c TEXT,
            dutyTime2s TEXT, dutyTime2c TEXT,
            dutyTime3s TEXT, dutyTime3c TEXT,
            dutyTime4s TEXT, dutyTime4c TEXT,
            dutyTime5s TEXT, dutyTime5c TEXT,
            dutyTime6s TEXT, dutyTime6c TEXT,
            dutyTime7s TEXT, dutyTime7c TEXT,
            dutyTime8s TEXT, dutyTime8c TEXT,
            
            type TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Database {DB_FILE} initialized.")

def fetch_and_save(url, type_label):
    """Fetch data from API and upsert into database."""
    page_no = 1
    total_saved = 0
    
    print(f"--- Starting Collection for {type_label} ---")
    
    while True:
        params = {
            "serviceKey": API_KEY,
            "numOfRows": NUM_OF_ROWS,
            "pageNo": page_no,
            "_type": "json"
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('response', {}).get('body', {}).get('items', {}).get('item')
            
            # Check if items exist
            if not items:
                print(f"No more data found at page {page_no}. Stopping.")
                break
                
            # Normalize to list if single item dict
            if isinstance(items, dict):
                items = [items]
            
            if len(items) == 0:
                print(f"Empty list at page {page_no}. Stopping.")
                break
                
            # Process Data
            processed_rows = []
            for item in items:
                # Essential fields check
                if not item.get('hpid'):
                    continue
                    
                row = {
                    "hpid": item.get('hpid'),
                    "dutyName": item.get('dutyName') or item.get('yadmNm'), # yadmNm is for hospital sometimes
                    "dutyAddr": item.get('dutyAddr') or item.get('addr'),
                    "dutyTel1": item.get('dutyTel1') or item.get('telno'),
                    "wgs84Lat": item.get('wgs84Lat') or item.get('YPos'), # Hospital API uses XPos/YPos often
                    "wgs84Lon": item.get('wgs84Lon') or item.get('XPos'),
                    "type": type_label
                }
                
                # Time columns
                for i in range(1, 9):
                    row[f"dutyTime{i}s"] = item.get(f"dutyTime{i}s")
                    row[f"dutyTime{i}c"] = item.get(f"dutyTime{i}c")
                
                # Data Cleaning: Skip invalid coordinates (optional, user said "exclude or null")
                # We save them as None if missing, Sqlite handles text/real mix fine usually but let's be safe
                try:
                    if row["wgs84Lat"]: row["wgs84Lat"] = float(row["wgs84Lat"])
                    if row["wgs84Lon"]: row["wgs84Lon"] = float(row["wgs84Lon"])
                except:
                    row["wgs84Lat"] = None
                    row["wgs84Lon"] = None
                
                processed_rows.append(row)
            
            if not processed_rows:
                print(f"Page {page_no}: No valid rows to save.")
                page_no += 1
                continue

            # Upsert using SQL
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Prepare Query
            # SQLite 'INSERT OR REPLACE' is the standard UPSERT if PK exists
            columns = ', '.join(processed_rows[0].keys())
            placeholders = ', '.join(['?'] * len(processed_rows[0]))
            sql = f"INSERT OR REPLACE INTO places ({columns}) VALUES ({placeholders})"
            
            # Execute Batch
            values = [tuple(row.values()) for row in processed_rows]
            cursor.executemany(sql, values)
            
            conn.commit()
            conn.close()
            
            count = len(processed_rows)
            total_saved += count
            print(f"{page_no}페이지 수집 완료 ({count}건) - 누적 {total_saved}건")
            
            page_no += 1
            
        except Exception as e:
            print(f"Error on page {page_no}: {e}")
            time.sleep(2) # Retry or skip? User didn't specify. Break for safety to avoid infinite loops on auth error.
            break

    print(f"--- {type_label} Collection Complete. Total Saved: {total_saved} ---")

if __name__ == "__main__":
    init_db()
    
    # Collect Pharmacies
    fetch_and_save(PHARMACY_URL, "약국")
    
    # Collect Hospitals
    fetch_and_save(HOSPITAL_URL, "병원")
    
    print("모든 데이터 수집이 완료되었습니다.")
