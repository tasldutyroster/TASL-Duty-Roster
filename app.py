import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import base64
from datetime import datetime
import io
import calendar

# ==============================================================================
# 1. PAGE CONFIGURATION & INITIALIZATION
# ==============================================================================
st.set_page_config(
    page_title="TASL Shift & Attendance Calendar",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BANNER_CACHE_PATH = "banner_cache.b64"
STAFF_STORAGE_PATH = "staff_registry_storage.json"
ROSTER_STORAGE_PATH = "roster_storage_v2.pkl"  
SWAP_STORAGE_PATH = "swap_tracking.json"     
SWAP_META_PATH = "swap_meta_tracking.json"   
SETTINGS_PASSWORD = "0477"  

DEFAULT_STAFF = [
    {"name": "MAHESH PU", "emp_id": "", "designation": "Officer", "aep_no": "", "pcc_expiry": "", "avsec_date": "", "avsec_validity": "", "photo": None, "status": "Active", "last_day": "", "training_start": "", "training_end": "", "aep_issue": "", "aep_expiry": ""},
    {"name": "AJITH KUMAR S", "emp_id": "", "designation": "Officer", "aep_no": "", "pcc_expiry": "", "avsec_date": "", "avsec_validity": "", "photo": None, "status": "Active", "last_day": "", "training_start": "", "training_end": "", "aep_issue": "", "aep_expiry": ""},
    {"name": "BALU S", "emp_id": "", "designation": "Officer", "aep_no": "", "pcc_expiry": "", "avsec_date": "", "avsec_validity": "", "photo": None, "status": "Active", "last_day": "", "training_start": "", "training_end": "", "aep_issue": "", "aep_expiry": ""},
    {"name": "SHINE SAGAR", "emp_id": "", "designation": "Officer", "aep_no": "", "pcc_expiry": "", "avsec_date": "", "avsec_validity": "", "photo": None, "status": "Active", "last_day": "", "training_start": "", "training_end": "", "aep_issue": "", "aep_expiry": ""},
    {"name": "NAVANEETH T S", "emp_id": "", "designation": "Officer", "aep_no": "", "pcc_expiry": "", "avsec_date": "", "avsec_validity": "", "photo": None, "status": "Active", "last_day": "", "training_start": "", "training_end": "", "aep_issue": "", "aep_expiry": ""},
    {"name": "AMAL P PRASAD", "emp_id": "", "designation": "Officer", "aep_no": "", "pcc_expiry": "", "avsec_date": "", "avsec_validity": "", "photo": None, "status": "Active", "last_day": "", "training_start": "", "training_end": "", "aep_issue": "", "aep_expiry": ""},
    {"name": "VACANT", "emp_id": "", "designation": "Officer", "aep_no": "", "pcc_expiry": "", "avsec_date": "", "avsec_validity": "", "photo": None, "status": "Active", "last_day": "", "training_start": "", "training_end": "", "aep_issue": "", "aep_expiry": ""},
    {"name": "NANDAKISHOR TR", "emp_id": "", "designation": "Officer", "aep_no": "", "pcc_expiry": "", "avsec_date": "", "avsec_validity": "", "photo": None, "status": "Active", "last_day": "", "training_start": "", "training_end": "", "aep_issue": "", "aep_expiry": ""}
]

def load_staff_registry():
    if os.path.exists(STAFF_STORAGE_PATH):
        try:
            with open(STAFF_STORAGE_PATH, "r", encoding="utf-8") as f:
                registry = json.load(f)
                for staff in registry:
                    if "aep_issue" not in staff: staff["aep_issue"] = ""
                    if "aep_expiry" not in staff: staff["aep_expiry"] = ""
                    if "emp_id" not in staff: staff["emp_id"] = ""
                    if "designation" not in staff: staff["designation"] = "Officer"
                    if "aep_no" not in staff: staff["aep_no"] = ""
                    if "pcc_expiry" not in staff: staff["pcc_expiry"] = ""
                    if "avsec_date" not in staff: staff["avsec_date"] = ""
                    if "avsec_validity" not in staff: staff["avsec_validity"] = ""
                return registry
        except Exception:
            return DEFAULT_STAFF
    return DEFAULT_STAFF

def save_staff_registry(registry):
    with open(STAFF_STORAGE_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=4)

def load_swaps():
    if os.path.exists(SWAP_STORAGE_PATH):
        try:
            with open(SWAP_STORAGE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_swaps(data):
    with open(SWAP_STORAGE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_swap_meta():
    if os.path.exists(SWAP_META_PATH):
        try:
            with open(SWAP_META_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_swap_meta(data):
    with open(SWAP_META_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def generate_infinite_rosters():
    staff_list = [s["name"] for s in st.session_state.get("staff_registry", DEFAULT_STAFF) if s["status"] == "Active"]
    if not staff_list:
        staff_list = [s["name"] for s in DEFAULT_STAFF]
        
    shift_cycle = ['B', 'B', np.nan, 'A', 'A', 'G', np.nan, np.nan]
    months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    
    def get_days_in_month(year, month_name):
        month_map = {
            "January": 31, "February": 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28,
            "March": 31, "April": 30, "May": 31, "June": 30, "July": 31, "August": 31,
            "September": 30, "October": 31, "November": 30, "December": 31
        }
        return month_map.get(month_name, 30)

    target_sequence = [(2025, "November"), (2025, "December")]
    for y in range(2026, 2031):
        for m in months_list:
            target_sequence.append((y, m))
            
    all_rosters = {}
    total_days_elapsed = 0
    
    month_to_num = {"January":1, "February":2, "March":3, "April":4, "May":5, "June":6, "July":7, "August":8, "September":9, "October":10, "November":11, "December":12}
    
    for year, m_name in target_sequence:
        days_count = get_days_in_month(year, m_name)
        dates = [str(d) for d in range(1, days_count + 1)]
        m_num = month_to_num[m_name]
        
        month_roster = []
        for emp_idx, emp in enumerate(staff_list):
            emp_row = [emp]
            base_offset = (7 - emp_idx) % 8
            
            designation = "Officer"
            for s in st.session_state.get("staff_registry", DEFAULT_STAFF):
                if s["name"] == emp and s["status"] == "Active":
                    designation = s.get("designation", "Officer")
                    break
            
            for day_idx in range(days_count):
                day_num = day_idx + 1
                curr_date = datetime(year, m_num, day_num)
                weekday = curr_date.weekday()
                
                if designation == "Network Engineer":
                    val = "G" if weekday < 5 else ""
                else:
                    absolute_day_index = total_days_elapsed + day_idx
                    shift_idx = (absolute_day_index + base_offset) % len(shift_cycle)
                    val = shift_cycle[shift_idx]
                    val = val if pd.notna(val) else ""
                    
                emp_row.append(val)
            month_roster.append(emp_row)
            
        m_df = pd.DataFrame(month_roster, columns=['Employee'] + dates)
        all_rosters[f"{m_name} {year}"] = m_df
        total_days_elapsed += days_count
        
    return all_rosters

def load_rosters():
    if os.path.exists(ROSTER_STORAGE_PATH):
        try:
            return pd.read_pickle(ROSTER_STORAGE_PATH)
        except Exception:
            pass
    return generate_infinite_rosters()

def save_rosters(rosters_dict):
    pd.to_pickle(rosters_dict, ROSTER_STORAGE_PATH)

def get_q(key, default):
    try: return st.query_params.get(key, default)
    except: return default

def set_q(key, val):
    try: st.query_params[key] = val
    except: pass

def initialize_session():
    if "current_view" not in st.session_state:
        st.session_state["current_view"] = get_q("view", "Dashboard")
    if "roster_sub" not in st.session_state:
        st.session_state["roster_sub"] = get_q("sub", "Calendar Grid")
    if "settings_sub" not in st.session_state:
        st.session_state["settings_sub"] = get_q("set", "Staff")
        
    if "settings_authenticated" not in st.session_state:
        st.session_state["settings_authenticated"] = False
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False
        
    if "app_font_size" not in st.session_state:
        st.session_state["app_font_size"] = "14px"
        
    if "banner_b64" not in st.session_state:
        if os.path.exists(BANNER_CACHE_PATH):
            try:
                with open(BANNER_CACHE_PATH, "r", encoding="utf-8") as f:
                    st.session_state["banner_b64"] = f.read().strip()
            except Exception:
                st.session_state["banner_b64"] = None
        else:
            st.session_state["banner_b64"] = None
            
    if "staff_registry" not in st.session_state:
        st.session_state["staff_registry"] = load_staff_registry()
    if "action_type" not in st.session_state:
        st.session_state["action_type"] = "Mark Leave"
    
    if "swap_data" not in st.session_state:
        st.session_state["swap_data"] = load_swaps()
    if "swap_meta" not in st.session_state:
        st.session_state["swap_meta"] = load_swap_meta()

initialize_session()

if "sheets_dict" not in st.session_state:
    st.session_state["sheets_dict"] = load_rosters()
sheets_dict = st.session_state["sheets_dict"]

def navigate_to(view_name):
    if view_name != "Settings":
        st.session_state["settings_authenticated"] = False
        
    st.session_state["current_view"] = view_name
    set_q("view", view_name)
    st.rerun()

def nav_roster(sub_name):
    st.session_state["roster_sub"] = sub_name
    set_q("sub", sub_name)
    st.rerun()

def nav_settings(sub_name):
    st.session_state["settings_sub"] = sub_name
    set_q("set", sub_name)
    st.rerun()

# ==============================================================================
# 2. DESIGN SYSTEM & CSS
# ==============================================================================
is_dark = st.session_state["dark_mode"]
font_size = st.session_state["app_font_size"]

if is_dark:
    cal_palette = {
        "bg_body": "#090D16", "bg_surface": "#131C2E",
        "text_main": "#F8FAFC", "text_sub": "#94A3B8",
        "border": "rgba(255, 255, 255, 0.12)", "accent": "#0066CC",
        "card_bg": "#131C2E", "card_text": "#FFFFFF",
        "shadow": "0 6px 20px rgba(0,0,0,0.5)"
    }
else:
    cal_palette = {
        "bg_body": "#F4F6F9", "bg_surface": "#FFFFFF",
        "text_main": "#1E293B", "text_sub": "#64748B",
        "border": "#CBD5E1", "accent": "#0066CC",
        "card_bg": "#FFFFFF", "card_text": "#0F172A",
        "shadow": "0 4px 16px rgba(0, 0, 0, 0.06)"
    }

def render_styled_html_table(df, current_month_str=""):
    """Renders a professional HTML table with leaves highlighted in red and swaps highlighted in amber/orange with (S)"""
    swap_meta = st.session_state.get("swap_meta", {})
    month_meta = swap_meta.get(current_month_str, {})
    swapped_cells = set()
    for pair_key, meta in month_meta.items():
        for e, d in meta.get("cells", []):
            swapped_cells.add((str(e).strip().upper(), str(d).strip()))

    html = '<div style="overflow-x: auto; border: 2px solid #000000; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); background-color: #F8FAFC; margin-bottom: 0.5rem;">'
    html += f'<table style="width: 100%; border-collapse: collapse; font-family: \'Plus Jakarta Sans\', sans-serif; font-size: {font_size};">'
    
    # Header
    html += '<thead><tr style="background-color: #E2E8F0; border-bottom: 2px solid #000000;">'
    for col in df.columns:
        html += f'<th style="padding: 10px 12px; border: 1px solid #000000; color: #000000; font-weight: 800; text-align: left;">{col}</th>'
    html += '</tr></thead>'
    
    # Body
    html += '<tbody>'
    emp_col_name = df.columns[0]
    for idx, row in df.iterrows():
        row_bg = "#F8FAFC" if idx % 2 == 0 else "#FFFFFF"
        html += f'<tr style="background-color: {row_bg}; transition: background 0.2s ease;">'
        emp_val = str(row[emp_col_name]).strip().upper()
        
        for col in df.columns:
            val = row[col] if pd.notna(row[col]) else ""
            cell_str = str(val).strip().upper()
            
            is_swapped = (col != emp_col_name) and ((emp_val, str(col).strip()) in swapped_cells)
            is_leave = (col != emp_col_name) and (cell_str in ["LEAVE", "SICK", "HOLIDAY"])
            
            if is_swapped:
                display_val = f"{val}<br><span style='font-size:0.7rem; color:#D97706; font-weight:800;'>(S)</span>" if str(val).strip() else "<span style='font-size:0.7rem; color:#D97706; font-weight:800;'>(S)</span>"
                cell_style = "background-color: #FEF3C7; border: 2px solid #D97706; color: #92400E; font-weight: 800; text-align: center;"
                html += f'<td style="padding: 6px 10px; border: 1px solid #000000; {cell_style}">{display_val}</td>'
            elif is_leave:
                html += f'<td style="padding: 8px 12px; border: 1px solid #000000; color: #EF4444; font-weight: 800;">{val}</td>'
            else:
                html += f'<td style="padding: 8px 12px; border: 1px solid #000000; color: #000000; font-weight: 600;">{val if pd.notna(val) else ""}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', sans-serif;
    }}
    
    html, body, [class*="css"], .stApp, .stMarkdown p, label p, button p {{
        font-size: {font_size} !important; 
    }}
    
    .stApp {{
        background-color: {cal_palette["bg_body"]};
        color: {cal_palette["text_main"]};
        animation: fadeIn 0.4s ease-in-out;
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(4px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    header[data-testid="stHeader"] {{ display: none !important; }}
    #MainMenu, footer {{ visibility: hidden !important; }}
    
    .block-container {{
        padding-top: 0.2rem !important;
        padding-bottom: 1rem !important;
        max-width: 99% !important;
    }}
    
    div.element-container {{
        margin-bottom: -0.3rem !important;
    }}

    label[data-testid="stWidgetLabel"] p, label p, .stMarkdown p {{
        color: {cal_palette["text_main"]} !important;
        font-weight: 700 !important;
        margin-bottom: 2px !important;
    }}

    .brand-container {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 0;
        white-space: nowrap;
    }}
    .brand-title {{
        font-size: 1.35rem;
        font-weight: 800;
        color: {cal_palette["text_main"]};
    }}

    div[data-baseweb="input"],
    div[data-baseweb="base-input"] {{
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1.5px solid #CBD5E1 !important;
        transition: all 0.2s ease;
    }}
    
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="base-input"]:focus-within {{
        border-color: {cal_palette["accent"]} !important;
        box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2) !important;
    }}
    
    input {{
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        background-color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: {font_size} !important;
    }}
    
    div[data-baseweb="calendar"], 
    div[data-baseweb="calendar"] * {{
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }}
    div[data-baseweb="calendar"] [aria-selected="true"],
    div[data-baseweb="calendar"] [aria-selected="true"] * {{
        background-color: #0066CC !important;
        color: #FFFFFF !important;
    }}

    div[data-testid="stPopoverBody"] {{
        background-color: #FFFFFF !important;
        border: 1.5px solid #94A3B8 !important;
        border-radius: 10px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15) !important;
        animation: popIn 0.2s ease-out;
    }}
    
    @keyframes popIn {{
        from {{ opacity: 0; transform: scale(0.95); }}
        to {{ opacity: 1; transform: scale(1); }}
    }}

    div[data-testid="stPopoverBody"] * {{
        color: #0F172A !important;
        font-size: {font_size} !important;
    }}

    [data-testid="stExpander"] summary {{
        background-color: {cal_palette["card_bg"]} !important; 
        border: 1px solid {cal_palette["border"]} !important;
        border-radius: 10px !important;
        box-shadow: {cal_palette["shadow"]} !important;
        padding: 0.5rem 0.9rem !important;
        transition: all 0.2s ease;
    }}
    [data-testid="stExpander"] summary:hover {{
        border-color: {cal_palette["accent"]} !important;
        transform: translateY(-1px);
    }}
    [data-testid="stExpander"] summary p, 
    [data-testid="stExpander"] summary span {{
        color: {cal_palette["card_text"]} !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }}

    button[kind="secondary"] {{
        background-color: {cal_palette["card_bg"]} !important;
        border: 1.5px solid {cal_palette["border"]} !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 0.45rem 0.9rem !important;
        box-shadow: {cal_palette["shadow"]} !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}
    button[kind="secondary"] p, button[kind="secondary"] div, button[kind="secondary"] span {{
        color: {cal_palette["card_text"]} !important;
        font-weight: 700 !important;
        font-size: {font_size} !important;
    }}
    button[kind="secondary"]:hover {{
        border-color: {cal_palette["accent"]} !important;
        background-color: #F8FAFC !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.08) !important;
    }}

    button[kind="primary"] {{
        background: linear-gradient(135deg, {cal_palette["accent"]} 0%, #004D99 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 0.45rem 0.9rem !important;
        box-shadow: 0 4px 14px rgba(0, 102, 204, 0.3) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}
    button[kind="primary"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 102, 204, 0.4) !important;
    }}
    button[kind="primary"] p, button[kind="primary"] div, button[kind="primary"] span {{
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: {font_size} !important;
    }}
    
    .shift-staff-tile {{
        background-color: {cal_palette["card_bg"]};
        color: {cal_palette["card_text"]};
        padding: 12px 16px;
        border-radius: 12px;
        border: 1px solid {cal_palette["border"]};
        font-weight: 600;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 14px;
        box-shadow: {cal_palette["shadow"]};
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .shift-staff-tile:hover {{
        transform: translateY(-3px);
        border-color: {cal_palette["accent"]};
        box-shadow: 0 10px 25px rgba(0, 102, 204, 0.15);
    }}
    .avatar-img {{
        width: 56px; height: 56px; border-radius: 50%; object-fit: cover; border: 2.5px solid {cal_palette["accent"]};
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        transition: transform 0.2s ease;
    }}
    .shift-staff-tile:hover .avatar-img {{
        transform: scale(1.05);
    }}

    .shift-header-box {{
        background: {cal_palette["bg_surface"]};
        padding: 10px 14px;
        border-radius: 10px;
        border: 1px solid {cal_palette["border"]};
        border-left: 5px solid {cal_palette["accent"]};
        margin-bottom: 8px;
        box-shadow: {cal_palette["shadow"]};
    }}
    .shift-title {{
        font-size: 1.1rem;
        font-weight: 800;
        color: {cal_palette["text_main"]};
        margin: 0;
    }}
    .shift-time {{
        font-size: 0.85rem;
        font-weight: 700;
        color: {cal_palette["accent"]};
        margin-top: 2px;
    }}

    .banner-wrapper {{
        width: 100%; border-radius: 12px; overflow: hidden;
        border: 1px solid {cal_palette["border"]}; margin-bottom: 0.8rem;
        box-shadow: {cal_palette["shadow"]};
        animation: fadeIn 0.5s ease;
    }}
    .banner-default {{
        width: 100%; min-height: 90px;
        background: linear-gradient(135deg, #0A192F 0%, #004D99 50%, {cal_palette["accent"]} 100%);
        display: flex; flex-direction: column; justify-content: center; padding: 14px 22px; color: #FFFFFF;
    }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# CUSTOM SELECT COMPONENT
# ==============================================================================
def custom_select(label, options, key_prefix, icon="🔽", default_idx=0):
    if not options:
        return None
    radio_key = f"{key_prefix}_radio"
    if radio_key not in st.session_state:
        st.session_state[radio_key] = options[default_idx] if len(options) > default_idx else options[0]
        
    current_val = st.session_state[radio_key]
    if current_val not in options:
        current_val = options[0]
        st.session_state[radio_key] = current_val

    st.markdown(f'<p style="font-size:{font_size}; font-weight:700; margin-bottom:2px; color:{cal_palette["text_main"]};">{label}</p>', unsafe_allow_html=True)
    with st.popover(f"{icon} {current_val}", use_container_width=True):
        st.radio(f"Choose {label}", options, key=radio_key, label_visibility="collapsed")
        
    return st.session_state[radio_key]

# ==============================================================================
# 3. TOP NAVIGATION BAR 
# ==============================================================================
col_brand, col_nav = st.columns([3.2, 5.8])

with col_brand:
    st.markdown('<div class="brand-container"><span style="font-size: 1.6rem;">📅</span><span class="brand-title">TASL Shift & Attendance Calendar</span></div>', unsafe_allow_html=True)

nav_views = [
    ("Dashboard", "📊 Live Attendance"),
    ("Duty Roster", "🗓️ Shift Calendar"),
    ("AEP", "🪪 AEP"),
    ("Settings", "⚙️ Settings & HR"),
]

with col_nav:
    nav_cols = st.columns([1, 1, 1, 1, 0.4])
    for idx, (v_key, v_label) in enumerate(nav_views):
        btn_type = "primary" if st.session_state["current_view"] == v_key else "secondary"
        if nav_cols[idx].button(v_label, key=f"nav_{v_key}", use_container_width=True, type=btn_type):
            navigate_to(v_key)

    theme_icon = "☀️" if is_dark else "🌙"
    if nav_cols[4].button(theme_icon, key="theme_toggle", use_container_width=True, help="Toggle Calendar Theme"):
        st.session_state["dark_mode"] = not st.session_state["dark_mode"]
        st.rerun()

st.divider()

current_view = st.session_state["current_view"]

def get_staff_photo_html(emp_name):
    safe_emp_name = str(emp_name).strip().upper()
    for staff in st.session_state["staff_registry"]:
        if staff["name"].strip().upper() == safe_emp_name and staff.get("photo"):
            return f'<img src="{staff["photo"]}" class="avatar-img" />'
    return f'<div style="width:56px; height:56px; border-radius:50%; background:{cal_palette["accent"]}; color:#fff; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:18px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">{safe_emp_name[:2]}</div>'

def get_emp_id_by_name(emp_name):
    safe_emp_name = str(emp_name).strip().upper()
    for staff in st.session_state["staff_registry"]:
        if staff["name"].strip().upper() == safe_emp_name:
            return staff.get("emp_id", "")
    return ""

# ==============================================================================
# VIEW 1: LIVE ATTENDANCE & SHIFT DASHBOARD 
# ==============================================================================
if current_view == "Dashboard":
    if st.session_state.get("banner_b64"):
        b_src = st.session_state["banner_b64"]
        if not b_src.startswith("data:image"):
            b_src = f"data:image/png;base64,{b_src}"
        st.markdown(f'<div class="banner-wrapper"><img src="{b_src}" style="width: 100%; max-height: 220px; display: block; object-fit: contain;" /></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="banner-wrapper"><div class="banner-default"><h2 style="margin:0; font-size: 1.4rem; font-weight: 800; color: #FFFFFF;">TASL Shift & Attendance Calendar</h2><p style="margin: 3px 0 0 0; opacity: 0.85; font-size: 0.9rem; color: #FFFFFF;">Real-time attendance tracking and leave administration.</p></div></div>', unsafe_allow_html=True)

    col_d1, col_d2 = st.columns([1, 4])
    with col_d1:
        dash_date = st.date_input("🗓️ Select Dashboard Date:", value=datetime.now())
    with col_d2:
        st.caption("*The dashboard automatically pulls shift assignments directly from the Duty Roster matrix for the date selected.*")
        
    current_month_str = dash_date.strftime("%B %Y")
    current_day_int = str(dash_date.day)
    
    st.markdown(f"### 📊 Attendance & Duty Roster — **{dash_date.strftime('%B %d, %Y (%A)')}**")

    if current_month_str not in sheets_dict:
        st.warning(f"⚠️ Data for **{current_month_str}** not available. Please generate the roster.")
    else:
        live_df = sheets_dict[current_month_str]
        emp_col = live_df.columns[0]
        
        if current_day_int in live_df.columns:
            today_sub = live_df[[emp_col, current_day_int]].dropna(subset=[emp_col]).copy()
            today_sub.columns = ["Employee", "Shift"]
            today_sub["Shift"] = today_sub["Shift"].astype(str).str.strip().str.upper()
            
            t_day = today_sub[today_sub["Shift"] == "A"]
            t_gen = today_sub[today_sub["Shift"] == "G"]
            t_night = today_sub[today_sub["Shift"] == "B"]
            t_leave = today_sub[today_sub["Shift"].isin(["LEAVE", "SICK", "HOLIDAY"])]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown('<div class="shift-header-box"><div class="shift-title">🌅 Day Shift (A)</div><div class="shift-time">08:00 – 20:00 Hours</div></div>', unsafe_allow_html=True)
                for _, r in t_day.iterrows():
                    emp_n = r["Employee"]
                    e_id = get_emp_id_by_name(emp_n)
                    disp_id = f" <span style='font-size: 0.85rem; color: #64748b;'>({e_id})</span>" if e_id else ""
                    avatar = get_staff_photo_html(emp_n)
                    st.markdown(f'<div class="shift-staff-tile">{avatar} <div><span style="font-size: 1.05rem; font-weight: 800;">{emp_n}</span>{disp_id}</div></div>', unsafe_allow_html=True)
                if len(t_day) == 0:
                    st.caption("No attendance recorded")
                    
            with col2:
                st.markdown('<div class="shift-header-box"><div class="shift-title">🏢 General Shift (G)</div><div class="shift-time">08:00 – 18:00 Hours</div></div>', unsafe_allow_html=True)
                for _, r in t_gen.iterrows():
                    emp_n = r["Employee"]
                    e_id = get_emp_id_by_name(emp_n)
                    disp_id = f" <span style='font-size: 0.85rem; color: #64748b;'>({e_id})</span>" if e_id else ""
                    avatar = get_staff_photo_html(emp_n)
                    st.markdown(f'<div class="shift-staff-tile">{avatar} <div><span style="font-size: 1.05rem; font-weight: 800;">{emp_n}</span>{disp_id}</div></div>', unsafe_allow_html=True)
                if len(t_gen) == 0:
                    st.caption("No attendance recorded")
                    
            with col3:
                st.markdown('<div class="shift-header-box"><div class="shift-title">🌙 Night Shift (B)</div><div class="shift-time">20:00 – 08:00 Hours</div></div>', unsafe_allow_html=True)
                for _, r in t_night.iterrows():
                    emp_n = r["Employee"]
                    e_id = get_emp_id_by_name(emp_n)
                    disp_id = f" <span style='font-size: 0.85rem; color: #64748b;'>({e_id})</span>" if e_id else ""
                    avatar = get_staff_photo_html(emp_n)
                    st.markdown(f'<div class="shift-staff-tile">{avatar} <div><span style="font-size: 1.05rem; font-weight: 800;">{emp_n}</span>{disp_id}</div></div>', unsafe_allow_html=True)
                if len(t_night) == 0:
                    st.caption("No attendance recorded")
            
            # ------------------------------------------------------------------
            # LEAVE SECTION
            # ------------------------------------------------------------------
            st.write("---")
            st.markdown("#### 🚫 On Leave / General Holiday Today")
            if len(t_leave) > 0:
                l_cols = st.columns(3)
                for i, (_, r) in enumerate(t_leave.iterrows()):
                    with l_cols[i % 3]:
                        emp_name = r["Employee"]
                        shift_type = r["Shift"]
                        e_id = get_emp_id_by_name(emp_name)
                        disp_id = f" <span style='font-size: 0.85rem; color: #64748b;'>({e_id})</span>" if e_id else ""
                        avatar = get_staff_photo_html(emp_name)
                        color = "#EF4444" if shift_type in ["LEAVE", "SICK"] else "#10B981"
                        
                        st.markdown(f'''
                        <div class="shift-staff-tile" style="border-left: 4px solid {color};">
                            {avatar} 
                            <div>
                                <span style="font-size: 1.05rem; font-weight: 800;">{emp_name}</span>{disp_id}<br>
                                <span style="color: {color}; font-weight: 700; font-size: 0.85rem;">Status: {shift_type}</span>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
            else:
                st.caption("All assigned staff are currently on duty. No leaves reported for this date.")

            # ------------------------------------------------------------------
            # COMPLIANCE EXPIRY ALERTS (AEP, PCC, AVSEC)
            # ------------------------------------------------------------------
            today_real_date = datetime.now().date()
            compliance_alerts = []
            
            for staff in st.session_state["staff_registry"]:
                if staff["status"] == "Active":
                    name = staff["name"]
                    emp_id = staff.get("emp_id", "")
                    
                    if staff.get("aep_expiry"):
                        try:
                            exp = datetime.strptime(staff["aep_expiry"], "%Y-%m-%d").date()
                            d_left = (exp - today_real_date).days
                            if d_left <= 45:
                                compliance_alerts.append({"name": name, "id": emp_id, "type": "AEP Pass", "days": d_left})
                        except: pass
                        
                    if staff.get("pcc_expiry"):
                        try:
