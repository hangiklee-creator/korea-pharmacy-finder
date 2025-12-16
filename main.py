import streamlit as st
from data_loader import get_real_pharmacy_list, get_real_hospital_list, get_nearby_places
from utils import is_open_now, reverse_geocode, forward_geocode
import folium
from folium.plugins import LocateControl
from streamlit_folium import st_folium
import pandas as pd
import math

st.set_page_config(page_title="휴일지킴이", page_icon="🏥", layout="wide")

# ... (CSS preserved) ...

# --- Administrative Divisions ---
# (KOREA_ADMIN_DIVISIONS preserved)
KOREA_ADMIN_DIVISIONS = {
    "서울특별시": ["강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"],
    "경기도": ["수원시", "성남시", "의정부시", "안양시", "부천시", "광명시", "평택시", "동두천시", "안산시", "고양시", "과천시", "구리시", "남양주시", "오산시", "시흥시", "군포시", "의왕시", "하남시", "용인시", "파주시", "이천시", "안성시", "김포시", "화성시", "광주시", "양주시", "포천시", "여주시", "연천군", "가평군", "양평군"],
    "부산광역시": ["중구", "서구", "동구", "영도구", "부산진구", "동래구", "남구", "북구", "해운대구", "사하구", "금정구", "강서구", "연제구", "수영구", "사상구", "기장군"],
    "대구광역시": ["중구", "동구", "서구", "남구", "북구", "수성구", "달서구", "달성군", "군위군"],
    "인천광역시": ["중구", "동구", "미추홀구", "연수구", "남동구", "부평구", "계양구", "서구", "강화군", "옹진군"],
    "광주광역시": ["동구", "서구", "남구", "북구", "광산구"],
    "대전광역시": ["동구", "중구", "서구", "유성구", "대덕구"],
    "울산광역시": ["중구", "남구", "동구", "북구", "울주군"],
    "세종특별자치시": ["세종특별자치시"],
    "강원특별자치도": ["춘천시", "원주시", "강릉시", "동해시", "태백시", "속초시", "삼척시", "홍천군", "횡성군", "영월군", "평창군", "정선군", "철원군", "화천군", "양구군", "인제군", "고성군", "양양군"],
    "충청북도": ["청주시", "충주시", "제천시", "보은군", "옥천군", "영동군", "증평군", "진천군", "괴산군", "음성군", "단양군"],
    "충청남도": ["천안시", "공주시", "보령시", "아산시", "서산시", "논산시", "계룡시", "당진시", "금산군", "부여군", "서천군", "청양군", "홍성군", "예산군", "태안군"],
    "전북특별자치도": ["전주시", "군산시", "익산시", "정읍시", "남원시", "김제시", "완주군", "진안군", "무주군", "장수군", "임실군", "순창군", "고창군", "부안군"],
    "전라남도": ["목포시", "여수시", "순천시", "나주시", "광양시", "담양군", "곡성군", "구례군", "고흥군", "보성군", "화순군", "장흥군", "강진군", "해남군", "영암군", "무안군", "함평군", "영광군", "장성군", "완도군", "진도군", "신안군"],
    "경상북도": ["포항시", "경주시", "김천시", "안동시", "구미시", "영주시", "영천시", "상주시", "문경시", "경산시", "의성군", "청송군", "영양군", "영덕군", "청도군", "고령군", "성주군", "칠곡군", "예천군", "봉화군", "울진군", "울릉군"],
    "경상남도": ["창원시", "진주시", "통영시", "사천시", "김해시", "밀양시", "거제시", "양산시", "의령군", "함안군", "창녕군", "고성군", "남해군", "하동군", "산청군", "함양군", "거창군", "합천군"],
    "제주특별자치도": ["제주시", "서귀포시"]
}

# --- Session State Initialization ---
if "city" not in st.session_state:
    st.session_state["city"] = "경기도"
if "district" not in st.session_state:
    st.session_state["district"] = "용인시"
if "selected_pharmacy" not in st.session_state:
    st.session_state["selected_pharmacy"] = None
if "show_map" not in st.session_state:
    st.session_state["show_map"] = False
if "search_mode" not in st.session_state:
    st.session_state["search_mode"] = "반경 검색" # Default to Radius
if "radius_km" not in st.session_state:
    st.session_state["radius_km"] = 3
if "my_coords" not in st.session_state:
    # Default: Gyeonggi-do Yongin-si City Hall approx
    st.session_state["my_coords"] = [37.241086, 127.177553]

# --- Sticky Header Section ---
sticky_container = st.container()
with sticky_container:
    # Marker for CSS selection
    st.markdown('<div class="sticky-header-marker"></div>', unsafe_allow_html=True)
    
    # Row 1: Mode Selection
    mode_cols = st.columns([2, 1])
    with mode_cols[0]:
        # Swapped order: Radius First
        mode = st.radio("검색 모드", ["반경 검색", "지역 검색"], horizontal=True, label_visibility="collapsed")
        if mode != st.session_state["search_mode"]:
            st.session_state["search_mode"] = mode
            st.rerun()

    st.markdown("---", unsafe_allow_html=True) # Divider

    if st.session_state["search_mode"] == "지역 검색":
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            new_city = st.selectbox(
                "시/도", 
                list(KOREA_ADMIN_DIVISIONS.keys()), 
                index=list(KOREA_ADMIN_DIVISIONS.keys()).index(st.session_state["city"])
            )
        
        with col2:
            districts = KOREA_ADMIN_DIVISIONS.get(new_city, [])
            current_district = st.session_state["district"]
            try:
                dist_index = districts.index(current_district)
            except ValueError:
                dist_index = 0
                
            new_district = st.selectbox(
                "시/군/구", 
                districts, 
                index=dist_index
            )
        
        with col3:
            search_type = st.radio("시설 종류", ["약국", "병원"], horizontal=True, key="type_region")

        # State Update Logic
        if new_city != st.session_state["city"] or new_district != st.session_state["district"]:
            st.session_state["city"] = new_city
            st.session_state["district"] = new_district
            st.session_state["selected_pharmacy"] = None
            st.session_state["show_map"] = False
            st.rerun()
            

    else: # Radius Search
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1.2, 0.8, 1.5]) # Adjusted widths
        with col1:
             st.markdown("**반경 설정**")
             rad_opts = [3, 5, 10, 500]
             curr_rad = st.session_state.get("radius_km", 3)
             try:
                 idx = rad_opts.index(curr_rad)
             except ValueError:
                 idx = 0
             
             radius = st.selectbox("반경", rad_opts, format_func=lambda x: f"{x}km" if x < 100 else "전국", index=idx, label_visibility="collapsed")
             if radius != st.session_state.get("radius_km"):
                 st.session_state["radius_km"] = radius
                 st.session_state["filter_open_only"] = False # Reset if manually changed
                 st.rerun()
                 
        with col2:
             st.markdown("**위치 설정**")
             if st.button("📍 내 위치", use_container_width=True):
                 st.session_state["show_map"] = True
                 st.toast("지도를 움직여 위치를 정하세요.", icon="🗺️")

        with col3:
             st.markdown("**종류**")
             search_type = st.radio("시설 종류", ["약국", "병원"], horizontal=True, key="type_radius", label_visibility="collapsed")
             
        with col4:
             st.write("") # Spacer
             st.write("") # Spacer
             if st.session_state['radius_km'] >= 500:
                  st.caption("범위: 전국")
             else:
                  st.caption(f"반경 {st.session_state['radius_km']}km")

        with col5:
             st.markdown("**빠른 찾기**")
             
             def set_quick_action():
                 st.session_state["type_radius"] = "약국"
                 st.session_state["radius_km"] = 500 # Nationwide
                 st.session_state["filter_open_only"] = True # Filter On

             st.button("⚡ 영업중인 약국", use_container_width=True, on_click=set_quick_action)

    # CSS Injection (Moved here for safety)
    st.markdown("""
<style>
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.is-open) {
        background-color: #e8f5e9 !important;
        border: 1px solid #a5d6a7 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.is-closed) {
        background-color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)


# --- Data Fetching ---
data_list = []
search_source = ""

if st.session_state["search_mode"] == "지역 검색":
    city = st.session_state["city"]
    district = st.session_state["district"]
    search_source = f"{city} {district}"
    
    with st.spinner(f"{search_source} 데이터 불러오는 중..."):
        if search_type == "약국":
            data_list = get_real_pharmacy_list(city, district)
        else:
            data_list = get_real_hospital_list(city, district)

else: # Radius Search
    lat, lon = st.session_state["my_coords"]
    radius = st.session_state["radius_km"]
    search_source = f"현재 위치 반경 {radius}km"
    
    with st.spinner(f"주변 {search_type} 검색 중... (DB)"):
        data_list = get_nearby_places(lat, lon, radius, place_type=search_type)

# Process Data
processed_data = []
for item in data_list:
    status = is_open_now(item)
    
    # Filter Open Only Logic
    if st.session_state.get("filter_open_only") and not status["is_open"]:
        continue # Skip closed places
        
    name = item.get("dutyName") or item.get("yadmNm")
    addr = item.get("dutyAddr") or item.get("addr")
    tel = item.get("dutyTel1") or item.get("telno")
    lat = item.get("wgs84Lat") or item.get("YPos")
    lon = item.get("wgs84Lon") or item.get("XPos")
    dist = item.get("distance")
    
    # Sunday Check (dutyTime7s exists and is valid)
    is_sunday = False
    if item.get("dutyTime7s") and item.get("dutyTime7c"):
        is_sunday = True

    if lat and lon:
        processed_data.append({
            "name": name, 
            "address": addr, 
            "tel": tel,
            "lat": float(lat), 
            "lon": float(lon),
            "is_open": status["is_open"], 
            "status_msg": status["message"],
            "distance": dist,
            "is_sunday": is_sunday,
            "raw": item
        })

# Sort
if st.session_state["search_mode"] == "지역 검색":
    processed_data.sort(key=lambda x: x["is_open"], reverse=True)
else:
    processed_data.sort(key=lambda x: (not x["is_open"], x.get("distance", 999)))

# Auto Select Top Logic (for Quick Action)

from utils import is_open_now, reverse_geocode, forward_geocode, format_operating_hours

# Limit to top 100 results for performance
processed_data = processed_data[:100]

# --- Main Layout ---

# 1. Detail View
if st.session_state["selected_pharmacy"]:
    sel = st.session_state["selected_pharmacy"]
    with st.container(border=True):
        st.markdown(f"### 🏥 {sel['name']}")
        st.markdown(f"**상태**: <span style='color:{'green' if sel['is_open'] else 'red'}'>{sel['status_msg']}</span>", unsafe_allow_html=True)
        c1, c2 = st.columns([2, 1])
        with c1:
            st.write(f"📍 {sel['address']}")
            st.write(f"📞 {sel['tel']}")
            
            # Operating Hours Expander
            with st.expander("🕒 영업 시간 보기"):
                hours_list = format_operating_hours(sel['raw'])
                if hours_list:
                    for h in hours_list:
                        st.text(h)
                else:
                    st.text("운영 시간 정보가 없습니다.")

        with c2:
             sub_c1, sub_c2, sub_c3 = st.columns(3)
             with sub_c1:
                 import streamlit.components.v1 as components
                 html_code = f"""
                 <!DOCTYPE html>
                 <html style="height: 100%; margin: 0; overflow: hidden;">
                 <body style="height: 100%; margin: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; background-color: transparent;">
                    <button id="copy_btn" onclick="copyAddress()" style="width: 100%; height: 100%; background-color: white; border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.5rem; cursor: pointer;">📋 주소복사</button>
                    <script>
                        function copyAddress() {{
                            navigator.clipboard.writeText('{sel['address']}').then(() => {{
                                document.getElementById("copy_btn").innerHTML = "✅ 완료!";
                                setTimeout(() => {{ document.getElementById("copy_btn").innerHTML = "📋 주소복사"; }}, 2000);
                            }});
                        }}
                    </script>
                 </body>
                 </html>
                 """
                 components.html(html_code, height=42)
             with sub_c2:
                 st.link_button("📞", f"tel:{sel['tel']}", use_container_width=True)
             with sub_c3:
                 if st.button("🗺️", key="btn_show_map", use_container_width=True):
                     st.session_state["show_map"] = True
                     st.rerun()
    st.markdown("---")

# 2. Grid View
if not processed_data:
    st.info("검색 결과가 없습니다.")
else:
    st.subheader(f"{search_source} 목록 ({len(processed_data)}곳)")
    cols = st.columns(4)
    for idx, item in enumerate(processed_data):
        col_idx = idx % 4
        with cols[col_idx]:
            with st.container(border=True):
                # Hidden Marker for CSS Targeting
                marker_class = "is-open" if item["is_open"] else "is-closed"
                st.markdown(f'<div class="{marker_class}" style="display:none;"></div>', unsafe_allow_html=True)
                
                # Title & Status
                # Layout for Title/Status
                t_col1, t_col2 = st.columns([3, 1])
                with t_col1:
                     sunday_badge = " <span style='background-color:#ffebee; color:#c62828; padding:2px 4px; border-radius:4px; font-size:0.8em; border:1px solid #ffcdd2;'>🌞일요일</span>" if item["is_sunday"] else ""
                     st.markdown(f"**{item['name']}**{sunday_badge}", unsafe_allow_html=True)
                with t_col2:
                     # Status Badge
                     status_badge = f"<span class='status-badge-open'>영업중</span>" if item["is_open"] else f"<span class='status-badge-closed'>{item['status_msg']}</span>"
                     st.markdown(f"{status_badge}", unsafe_allow_html=True)
                
                # Distance Badge (Radius Mode Only)
                if item.get("distance") is not None:
                    st.caption(f"📏 {item['distance']:.1f}km")

                # Select Button
                if st.button("상세보기", key=f"sel_{idx}"):
                    st.session_state["selected_pharmacy"] = item
                    st.session_state["show_map"] = False 
                    st.rerun()

# --- Bottom Map Section ---
if st.session_state["show_map"]: 
    st.markdown("---")
    st.subheader("🗺️ 지도 보기")
    
    start_loc = [37.5665, 126.9780] 
    zoom = 14
    
    markers_to_show = []
    
    if st.session_state["search_mode"] == "반경 검색":
        start_loc = st.session_state["my_coords"]
        markers_to_show.append({
            "loc": start_loc,
            "popup": "기준 위치",
            "icon": "user",
            "color": "blue"
        })
        
        for p in processed_data[:20]: 
             markers_to_show.append({
                 "loc": [p["lat"], p["lon"]],
                 "popup": p["name"],
                 "icon": "plus" if "병원" in search_type else "medkit", 
                 "color": "green" if p["is_open"] else "red"
             })
             
    elif st.session_state["selected_pharmacy"]:
        sel = st.session_state["selected_pharmacy"]
        start_loc = [sel["lat"], sel["lon"]]
        markers_to_show.append({
            "loc": start_loc,
            "popup": sel["name"],
            "icon": "info-sign",
            "color": "green" if sel["is_open"] else "red"
        })

    m = folium.Map(location=start_loc, zoom_start=zoom)
    
    # Add Locate Control with auto_start to request geolocation
    LocateControl(auto_start=True).add_to(m)
    
    # Add Markers
    for mk in markers_to_show:
        folium.Marker(
            mk["loc"],
            popup=mk["popup"],
            icon=folium.Icon(color=mk["color"], icon=mk["icon"])
        ).add_to(m)
    
    # Render with center capture
    map_data = st_folium(m, width="100%", height=400, returned_objects=["last_object_clicked", "center"])
    
    # Input for updating location in Radius Mode
    if st.session_state["search_mode"] == "반경 검색" and map_data:
        new_center = map_data.get("center")
        if new_center:
            # Check if moved significantly to avoid loop
            current_lat, current_lon = st.session_state["my_coords"]
            new_lat = new_center["lat"]
            new_lon = new_center["lng"]
            
            # Update only if moved > 0.0001 deg (~10m)
            if abs(new_lat - current_lat) > 0.0001 or abs(new_lon - current_lon) > 0.0001:
                 st.session_state["my_coords"] = [new_lat, new_lon]
                 st.rerun()

