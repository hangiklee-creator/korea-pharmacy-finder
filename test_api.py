from data_loader import get_pharmacy_list, get_hospital_list
import json

def test_pharmacy_api():
    print("Testing Pharmacy API...")
    try:
        response = get_pharmacy_list("서울특별시", "강남구")
        print(f"Status Code: {response.status_code}")
    
        try:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
            
            header = data.get('response', {}).get('header', {})
            if header.get('resultCode') == '00':
                print("Pharmacy API Success!")
            else:
                print(f"Pharmacy API Error: {header.get('resultMsg')}")
                
        except json.JSONDecodeError:
            print("Failed to parse JSON. Response might be XML or HTML.")
            print("Raw Response:", response.text[:500])
    except Exception as e:
        print(f"Pharmacy API Request Failed: {e}")

    print("\nTesting Pharmacy API V2 (User provided name)...")
    try:
        from data_loader import get_pharmacy_list_v2
        response = get_pharmacy_list_v2("서울특별시", "강남구")
        print(f"Status Code: {response.status_code}")
        try:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False)[:300])
        except:
            print("Raw Response V2:", response.text[:300])
    except Exception as e:
        print(f"Pharmacy API V2 Request Failed: {e}")

def test_hospital_api():
    print("\nTesting Hospital API...")
    try:
        from data_loader import get_hospital_list
        response = get_hospital_list("서울특별시", "강남구")
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
            
            header = data.get('response', {}).get('header', {})
            if header.get('resultCode') == '00':
                print("Hospital API Success!")
            else:
                print(f"Hospital API Error: {header.get('resultMsg')}")
                
        except json.JSONDecodeError:
            print("Failed to parse JSON")
            print("Raw Response:", response.text[:500])
    except Exception as e:
        print(f"Hospital API Request Failed: {e}")

def test_mock_data():
    print("\nTesting Mock Data...")
    from data_loader import get_mock_pharmacy_list, get_mock_hospital_list
    from utils import is_open_now
    
    pharmacies = get_mock_pharmacy_list()
    print(f"Loaded {len(pharmacies)} mock pharmacies")
    
    for item in pharmacies:
        status = is_open_now(item)
        print(f"Pharmacy: {item['dutyName']} -> {status['message']}")
        
    hospitals = get_mock_hospital_list()
    print(f"Loaded {len(hospitals)} mock hospitals")
    for item in hospitals:
        status = is_open_now(item)
        print(f"Hospital: {item['yadmNm']} -> {status['message']}")

if __name__ == "__main__":
    test_pharmacy_api() 
    test_hospital_api()
    # test_mock_data()
