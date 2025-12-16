from datetime import datetime
import time
from workalendar.asia import SouthKorea

cal = SouthKorea()

def parse_time(time_str):
    """
    Parses a time string like '0900' or '1830' into a time object.
    Returns None if invalid or empty.
    """
    if not time_str or not str(time_str).isdigit():
        return None
    
    time_str = str(time_str).strip()
    if len(time_str) != 4:
        return None
        
    try:
        hour = int(time_str[:2])
        minute = int(time_str[2:])
        return datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    except:
        return None

def is_open_now(item, current_datetime=None):
    """
    Determines if the facility is open at the current time.
    
    Args:
        item (dict): The data dictionary for the facility.
        current_datetime (datetime): Optional. Override current time for testing.
        
    Returns:
        dict: {
            "is_open": bool,
            "message": str (e.g. "영업 중 (18:00 종료)", "영업 종료", "휴진")
        }
    """
    if current_datetime is None:
        current_datetime = datetime.now()
    
    # Check if holiday
    date_only = current_datetime.date()
    is_holiday = cal.is_holiday(date_only) or (current_datetime.weekday() == 6) # Sunday is usually treated like holiday in dutyTime8s? 
                                                                               # Actually, API has dutyTime7 (Sun) and dutyTime8 (Holiday)
    # Re-logic:
    # Mon(0)..Sat(5) -> dutyTime1..6
    # Sun(6) -> dutyTime7
    # Public Holiday -> dutyTime8 (Overrides weekday?)
    
    # Official logic usually: If Public Holiday -> dutyTime8. Else -> dutyTime(weekday+1)
    
    start_key = None
    end_key = None
    
    if cal.is_holiday(date_only):
        start_key = "dutyTime8s"
        end_key = "dutyTime8c"
    else:
        weekday = current_datetime.weekday() # 0=Mon
        day_idx = weekday + 1
        start_key = f"dutyTime{day_idx}s"
        end_key = f"dutyTime{day_idx}c"

        
    start_time_str = item.get(start_key)
    end_time_str = item.get(end_key)

    # Convert to string and pad if integer (e.g. 900 -> "0900")
    # Using simple str() might yield "900", so we need zfill(4)
    try:
        if start_time_str:
            start_time_str = str(int(start_time_str)).zfill(4)
        if end_time_str:
            end_time_str = str(int(end_time_str)).zfill(4)
    except ValueError:
        return {"is_open": False, "message": "휴진 (시간 형식 오류)"}

    # Double check emptiness after safe conversion
    if not start_time_str or not end_time_str:
        return {"is_open": False, "message": "휴진 (정보 없음)"}
    
    current_hhmm = current_datetime.strftime("%H%M")
    
    if start_time_str <= current_hhmm <= end_time_str:
        formatted_end = f"{end_time_str[:2]}:{end_time_str[2:]}"
        return {"is_open": True, "message": f"영업 중 ({formatted_end} 종료)"}
    else:
        return {"is_open": False, "message": "영업 종료"}

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

def reverse_geocode(lat, lon):
    """
    Reverse geocodes coordinates to administrative divisions.
    Returns (city, district) tuple or (None, None).
    """
    try:
        geolocator = Nominatim(user_agent="holiday_keeper_app", timeout=10)
        location = geolocator.reverse((lat, lon), language='ko', exactly_one=True)
        if location:
            address = location.raw.get('address', {})
            # Nominatim mapping to Korean Admin Divisions
            # city (si/do) -> city, province
            # district (si/gun/gu) -> borough, district, city (if under province)
            
            # Extract City (Si/Do)
            city = address.get('city') or address.get('province') or address.get('state')
            
            # Extract District (Gun/Gu)
            # 'borough' often maps to Gu in Seoul. 'district' can be Gu. 'city' if in Gyeonggi-do (e.g. Suwon-si) but distinct from 'province'
            district = address.get('borough') or address.get('district') or address.get('city') or address.get('county')
            
            # Normalization logic could be complex. 
            # Simplified for major use cases:
            # Seoul -> City="서울특별시", District="Gangnam-gu" -> "강남구"
            
            if city and district:
                return city, district
    except Exception as e:
        print(f"Reverse geocoding error: {e}")
        
    return None, None

def forward_geocode(city, district):
    """
    Geocodes a city and district name to coordinates.
    Returns (lat, lon) or (None, None).
    """
    try:
        geolocator = Nominatim(user_agent="holiday_keeper_app", timeout=10)
        query = f"{city} {district}"
        location = geolocator.geocode(query, country_codes="kr")
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Forward geocoding error: {e}")
        
    return None, None

def format_operating_hours(item):
    """
    Formats the operating hours into a readable dictionary string.
    Keys: dutyTime1s/c (Mon) to dutyTime8s/c (Holiday).
    Returns a list of strings like "월: 09:00 - 18:00".
    """
    days_map = {
        1: "월", 2: "화", 3: "수", 4: "목", 5: "금", 6: "토", 7: "일", 8: "공휴일"
    }
    
    formatted_hours = []
    
    for i in range(1, 9):
        s_key = f"dutyTime{i}s"
        c_key = f"dutyTime{i}c"
        
        start = item.get(s_key)
        end = item.get(c_key)
        
        if start and end:
            try:
                # Format 0900 -> 09:00
                s_fmt = f"{str(start).zfill(4)[:2]}:{str(start).zfill(4)[2:]}"
                e_fmt = f"{str(end).zfill(4)[:2]}:{str(end).zfill(4)[2:]}"
                day_name = days_map.get(i, "")
                formatted_hours.append(f"{day_name}: {s_fmt} - {e_fmt}")
            except:
                continue
                
    return formatted_hours
