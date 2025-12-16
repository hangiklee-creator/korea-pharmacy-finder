import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DATA_GO_KR_API_KEY")

def get_pharmacy_list(Q0, Q1, ord="NAME", pageNo=1, numOfRows=10):
    """
    국립중앙의료원_전국 약국 정보 조회 서비스
    Q0: 주소(시도) - 서울특별시
    Q1: 주소(시군구) - 강남구
    ord: 정렬순서
    """
    url = "http://apis.data.go.kr/B552657/ErmctInsttInfoInqireService/getParmacyListInfoInqire"
    params = {
        "serviceKey": API_KEY,
        "Q0": Q0,
        "Q1": Q1,
        "ORD": ord,
        "pageNo": pageNo,
        "numOfRows": numOfRows,
        # "dataType": "JSON" # 공공데이터포털 some APIs don't support JSON param explicitly or require specific handling. 
        # Typically XML is default. Let's try to see if JSON is supported via query param or if we need to parse XML. 
        # Many newer APIs support _type=json or dataType=JSON. Let's try adding _type=json first as it is common for data.go.kr
        "_type": "json" 
    }
    
    # URL Encoding of the key is often tricky. requests handles parameters, but sometimes the key needs to be pre-encoded or not.
    # The user provided key looks decoded. requests will urlencode it again.
    # If the key provided is ALREADY encoded, we might have issues.
    # Usually keys starting with long alphanumeric strings are decoded. %2B... are encoded.
    # The provided key: b081... seems decoded (hex).
    
    response = requests.get(url, params=params)
    # print(f"Request URL: {response.url}") # Debug URL
    return response

def get_pharmacy_list_v2(Q0, Q1, pageNo=1, numOfRows=10):
    """
    Alternative endpoint for testing: 국립중앙의료원 or 심평원
    """
    # Try the endpoint that matches the user's function name literally, assuming it might be NEMC or HIRA
    # This one is for NEMC but with the specific function name if it exists? 
    # Actually, let's try the HIRA endpoint which corresponds to 'getListOfPharmacyAcctoLcinfo' just in case the key works there.
    # Provider: Health Insurance Review & Assessment Service (B551182)
    # Service: pharmacyInfoService
    url = "http://apis.data.go.kr/B552657/ErmctInsttInfoInqireService/getListOfPharmacyAcctoLcinfo" # Trying NEMC with user's op name
    
    # If that fails, we might try B551182 (HIRA)
    # url = "http://apis.data.go.kr/B551182/pharmacyInfoService/getListOfPharmacyAcctoLcinfo"
    
    params = {
        "serviceKey": API_KEY,
        "Q0": Q0,
        "Q1": Q1,
        "pageNo": pageNo,
        "numOfRows": numOfRows,
        "_type": "json"
    }
    response = requests.get(url, params=params)
    print(f"Request URL V2: {response.url}")
    return response

def get_hospital_list(Q0, Q1, ord="NAME", pageNo=1, numOfRows=10):
    """
    국립중앙의료원_전국 병·의원 찾기 서비스
    """
    url = "http://apis.data.go.kr/B552657/HsptlAsembySearchService/getHsptlMdcncListInfoInqire"
    params = {
        "serviceKey": API_KEY,
        "Q0": Q0,
        "Q1": Q1,
        "ORD": ord,
        "pageNo": pageNo,
        "numOfRows": numOfRows,
        "_type": "json"
    }
    response = requests.get(url, params=params)
    print(f"Request URL Hospital: {response.url}")
    return response

def get_mock_pharmacy_list():
    """
    Returns mock data for pharmacies in Gangnam-gu, mirroring the expected API structure.
    """
    return [
        {
            "dutyName": "행복약국 (Mock)",
            "dutyAddr": "서울특별시 강남구 강남대로 100",
            "dutyTel1": "02-1234-5678",
            "wgs84Lat": "37.498095",
            "wgs84Lon": "127.027610",
            # Mon-Fri 09:00 - 18:00
            "dutyTime1s": "0900", "dutyTime1c": "1800",
            "dutyTime2s": "0900", "dutyTime2c": "1800",
            "dutyTime3s": "0900", "dutyTime3c": "1800",
            "dutyTime4s": "0900", "dutyTime4c": "1800",
            "dutyTime5s": "0900", "dutyTime5c": "1800",
            # Sat 09:00 - 13:00
            "dutyTime6s": "0900", "dutyTime6c": "1300",
            # Closed on Sunday/Holiday (no keys or null)
        },
        {
            "dutyName": "24시 야간약국 (Mock)",
            "dutyAddr": "서울특별시 강남구 테헤란로 200",
            "dutyTel1": "02-9876-5432",
            "wgs84Lat": "37.500000",
            "wgs84Lon": "127.035000",
            # Mon-Sun 09:00 - 23:00, Holiday Open
            "dutyTime1s": "0900", "dutyTime1c": "2300",
            "dutyTime2s": "0900", "dutyTime2c": "2300",
            "dutyTime3s": "0900", "dutyTime3c": "2300",
            "dutyTime4s": "0900", "dutyTime4c": "2300",
            "dutyTime5s": "0900", "dutyTime5c": "2300",
            "dutyTime6s": "0900", "dutyTime6c": "2300",
            "dutyTime7s": "0900", "dutyTime7c": "2300", # Sunday
            "dutyTime8s": "0900", "dutyTime8c": "2300", # Holiday
        },
         {
            "dutyName": "주말 닫는 약국 (Mock)",
            "dutyAddr": "서울특별시 강남구 도산대로 300",
            "dutyTel1": "02-555-5555",
            "wgs84Lat": "37.510000",
            "wgs84Lon": "127.040000",
            "dutyTime1s": "1000", "dutyTime1c": "1900",
            "dutyTime2s": "1000", "dutyTime2c": "1900",
            "dutyTime3s": "1000", "dutyTime3c": "1900",
            "dutyTime4s": "1000", "dutyTime4c": "1900",
            "dutyTime5s": "1000", "dutyTime5c": "1900",
        }
    ]

def get_mock_hospital_list():
    """
    Returns mock data for hospitals.
    """
    return [
        {
            "yadmNm": "서울아산병원 (Mock)",
            "addr": "서울특별시 송파구 올림픽로43길 88",
            "telno": "1688-7575",
            "XPos": "127.107937", # Caution: Hospital API sometimes uses X/Y vs Lat/Lon
            "YPos": "37.526569",  # We need to normalize this in UI
            "dutyTime1s": "0900", "dutyTime1c": "1800",
            "dutyTime2s": "0900", "dutyTime2c": "1800",
            "dutyTime3s": "0900", "dutyTime3c": "1800",
            "dutyTime4s": "0900", "dutyTime4c": "1800",
            "dutyTime5s": "0900", "dutyTime5c": "1800",
            "dutyTime6s": "0900", "dutyTime6c": "1300",
        },
        {
             "yadmNm": "강남세브란스 (Mock)",
             "addr": "서울특별시 강남구 언주로 211",
             "telno": "02-2019-2114",
             "XPos": "127.046294",
             "YPos": "37.492778",
             "dutyTime1s": "0900", "dutyTime1c": "1730",
             "dutyTime2s": "0900", "dutyTime2c": "1730",
             "dutyTime3s": "0900", "dutyTime3c": "1730",
             "dutyTime4s": "0900", "dutyTime4c": "1730",
             "dutyTime5s": "0900", "dutyTime5c": "1730",
             "dutyTime6s": "0900", "dutyTime6c": "1230",
        }
    ]

def get_real_pharmacy_list(Q0, Q1):
    """
    Fetches and parses real pharmacy data.
    """
    try:
        response = get_pharmacy_list(Q0, Q1, numOfRows=500)
        if response.status_code != 200:
            return []
        
        data = response.json()
        items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
        
        # Determine if it's a list or dict (sometimes single item is dict)
        if isinstance(items, dict):
            items = [items]
        elif items is None:
            items = []
            
        return items
    except Exception as e:
        print(f"Error fetching real pharmacy data: {e}")
        return []

def get_real_hospital_list(Q0, Q1):
    """
    Fetches and parses real hospital data.
    """
    try:
        response = get_hospital_list(Q0, Q1, numOfRows=500)
        if response.status_code != 200:
            return []
            
        data = response.json()
        items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
        
        if isinstance(items, dict):
            items = [items]
        elif items is None:
            items = []
            
    except Exception as e:
        print(f"Error fetching real hospital data: {e}")
        return []

import sqlite3
import math

DB_FILE = "hospital.db"

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def get_nearby_places(lat, lon, radius_km, place_type="약국", limit=1000):
    """
    Fetches places within radius_km from the local DB.
    Optimized with a bounding box query first.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row # Access columns by name
        cursor = conn.cursor()
        
        # 1. Bounding Box Filter (Approximate)
        # 1 degree lat ~= 111km
        # 1 degree lon ~= 111km * cos(lat)
        delta_lat = radius_km / 111.0
        delta_lon = radius_km / (111.0 * math.cos(math.radians(lat)))
        
        min_lat = lat - delta_lat
        max_lat = lat + delta_lat
        min_lon = lon - delta_lon
        max_lon = lon + delta_lon
        
        cursor.execute('''
            SELECT * FROM places 
            WHERE type = ? 
            AND wgs84Lat BETWEEN ? AND ?
            AND wgs84Lon BETWEEN ? AND ?
        ''', (place_type, min_lat, max_lat, min_lon, max_lon))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            # Convert Row to Dict
            item = dict(row)
            
            # Calculate Exact Distance
            p_lat = item['wgs84Lat']
            p_lon = item['wgs84Lon']
            
            if p_lat is None or p_lon is None:
                continue
                
            dist = haversine(lat, lon, p_lat, p_lon)
            
            if dist <= radius_km:
                item['distance'] = dist
                results.append(item)
        
        # Sort by distance
        results.sort(key=lambda x: x['distance'])
        
        return results[:limit]
        
    except Exception as e:
        print(f"Error fetching nearby places: {e}")
        return []

