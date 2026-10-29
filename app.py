import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import base64
from datetime import datetime
import io
import calendar
import shutil
import glob
from github import Github

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
BACKUP_DIR = "backups"
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

def push_to_github(file_path):
    """Automatically commits saved files directly back to your GitHub repo so they survive server reboots."""
    try:
        if "GITHUB_TOKEN" not in st.secrets:
            return
            
        token = st.secrets["GITHUB_TOKEN"] 
        repo_name = "tasldutyroster/TASL-Duty-Roster" 
        
        g = Github(token)
        repo = g.get_repo(repo_name)
        file_name = os.path.basename(file_path)
        
        with open(file_path, 'rb') as f:
            content = f.read()
            
        try:
            contents = repo.get_contents(file_name, ref="main")
            repo.update_file(contents.path, f"Auto-sync: {file_name}", content, contents.sha, branch="main")
        except:
            repo.create_file(file_name, f"Auto-sync initial: {file_name}", content, branch="main")
    except Exception as e:
        pass

def perform_auto_backup():
    try:
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_subfolder = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
        os.makedirs(target_subfolder, exist_ok=True)
        
        files_to_backup = [STAFF_STORAGE_PATH, ROSTER_STORAGE_PATH, SWAP_STORAGE_PATH, SWAP_META_PATH, BANNER_CACHE_PATH]
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                shutil.copy(file_path, target_subfolder)
                
        all_backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "backup_*")))
        if len(all_backups) > 10:
            for old_backup in all_backups[:-10]:
                shutil.rmtree(old_backup)
    except Exception:
        pass

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
    push_to_github(STAFF_STORAGE_PATH)
    perform_auto_backup()

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
    push_to_github(SWAP_STORAGE_PATH)
    perform_auto_backup()

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
    push_to_github(SWAP_META_PATH)
    perform_auto_backup()

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
    push_to_github(ROSTER_STORAGE_PATH)
    perform_auto_backup()

def initialize_session():
    if "current_view" not in st.session_state:
        st.session_state["current_view"] = "Dashboard"
    if "roster_sub" not in st.session_state:
        st.session_state["roster_sub"] = "Calendar Grid"
    if "settings_sub" not in st.session_state:
        st.session_state["settings_sub"] = "Staff"
        
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

    perform_auto_backup()

initialize_session()

if "sheets_dict" not in st.session_state:
    st.session_state["sheets_dict"] = load_rosters()
sheets_dict = st.session_state["sheets_dict"]

def navigate_to(view_name):
    if view_name != "Settings":
        st.session_state["settings_authenticated"] = False
    st.session_state["current_view"] = view_name
    st.rerun()

def nav_roster(sub_name):
    st.session_state["roster_sub"] = sub_name
    st.rerun()

def nav_settings(sub_name):
    st.session_state["settings_sub"] = sub_name
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
    swap_meta = st.session_state.get("swap_meta", {})
    month_meta = swap_meta.get(current_month_str, {})
    swapped_cells = set()
    for pair_key, meta in month_meta.items():
        for e, d in meta.get("cells", []):
            swapped_cells.add((str(e).strip().upper(), str(d).strip()))

    html = '<div style="overflow-x: auto; border: 2px solid #000000; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); background-color: #F8FAFC; margin-bottom: 0.5rem;">'
    html += f'<table style="width: 100%; border-collapse: collapse; font-family: \'Plus Jakarta Sans\', sans-serif; font-size: {font_size};">'
    
    html += '<thead><tr style="background-color: #E2E8F0; border-bottom: 2px solid #000000;">'
    for col in df.columns:
        html += f'<th style="padding: 10px 12px; border: 1px solid #000000; color: #000000; font-weight: 800; text-align: left;">{col}</th>'
    html += '</tr></thead>'
    
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

    /* SAFELY FORMATTED INPUT FIELDS TO FIX INVISIBLE TEXT & BLACK THEME BUG */
    div[data-testid="stDateInput"] div[data-baseweb="base-input"],
    div[data-testid="stTextInput"] div[data-baseweb="base-input"],
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
    
    input, 
    input[type="text"], 
    input[type="password"] {{
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
                            exp = datetime.strptime(staff["pcc_expiry"], "%Y-%m-%d").date()
                            d_left = (exp - today_real_date).days
                            if d_left <= 45:
                                compliance_alerts.append({"name": name, "id": emp_id, "type": "PCC Certificate", "days": d_left})
                        except: pass
                        
                    if staff.get("avsec_validity"):
                        try:
                            exp = datetime.strptime(staff["avsec_validity"], "%Y-%m-%d").date()
                            d_left = (exp - today_real_date).days
                            if d_left <= 45:
                                compliance_alerts.append({"name": name, "id": emp_id, "type": "AVSEC Course", "days": d_left})
                        except: pass
                        
            if compliance_alerts:
                st.write("---")
                st.markdown("#### ⚠️ Compliance Expiry Alerts (AEP, PCC & AVSEC)")
                st.caption("The following personnel have permits, clearances, or courses that are expired or expiring within the next 45 days.")
                
                alert_cols = st.columns(3)
                for i, alert in enumerate(compliance_alerts):
                    with alert_cols[i % 3]:
                        emp_name = alert["name"]
                        e_id = alert["id"]
                        c_type = alert["type"]
                        days_left = alert["days"]
                        avatar = get_staff_photo_html(emp_name)
                        disp_id = f" <span style='font-size: 0.85rem; color: #64748b;'>({e_id})</span>" if e_id else ""
                        
                        if days_left < 0:
                            color = "#EF4444" 
                            msg = f"{c_type} expired {abs(days_left)} days ago!"
                        else:
                            color = "#F59E0B" 
                            msg = f"{c_type} expires in {days_left} days"
                            
                        st.markdown(f'''
                        <div class="shift-staff-tile" style="border-left: 4px solid {color}; background-color: rgba(239, 68, 68, 0.03);">
                            {avatar} 
                            <div>
                                <span style="font-size: 1.05rem; font-weight: 800;">{emp_name}</span>{disp_id}<br>
                                <span style="color: {color}; font-weight: 800; font-size: 0.9rem;">{msg}</span>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
                
        else:
            st.warning(f"⚠️ Selected date column ({current_day_int}) not found in the matrix.")

# ==============================================================================
# VIEW 2: DUTY ROSTER & SHIFT CALENDAR
# ==============================================================================
elif current_view == "Duty Roster":
    st.subheader("🗓️ Interactive Shift & Attendance Calendar Matrix")
    
    existing_sheets = list(sheets_dict.keys())
    default_month_str = datetime.now().strftime("%B %Y")
    default_idx = existing_sheets.index(default_month_str) if default_month_str in existing_sheets else 0
    
    col_sel1, col_sel2 = st.columns([2, 3])
    with col_sel1:
        selected_month = custom_select("Select Calendar Month & Year:", existing_sheets, "roster_month", icon="🗓️", default_idx=default_idx)
    
    active_df = sheets_dict[selected_month]
    active_df.columns = [str(c).strip() for c in active_df.columns]
    
    sub_c1, sub_c2, sub_c3, sub_c4 = st.columns(4)
    with sub_c1:
        if st.button("📅 Attendance Grid", use_container_width=True, type="primary" if st.session_state.get("roster_sub") == "Calendar Grid" else "secondary"):
            nav_roster("Calendar Grid")
    with sub_c2:
        if st.button("⚙️ Leave / Swaps", use_container_width=True, type="primary" if st.session_state.get("roster_sub") == "Actions" else "secondary"):
            nav_roster("Actions")
    with sub_c3:
        if st.button("🌴 Quota Report", use_container_width=True, type="primary" if st.session_state.get("roster_sub") == "Report" else "secondary"):
            nav_roster("Report")
    with sub_c4:
        csv_data = active_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export CSV",
            data=csv_data,
            file_name=f"TASL_Roster_{selected_month.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True
        )
            
    st.divider()
    curr_roster_sub = st.session_state.get("roster_sub", "Calendar Grid")
    
    if curr_roster_sub == "Calendar Grid":
        st.markdown(f"#### Monthly Shift & Attendance Calendar — **{selected_month}**")
        st.caption("A = Day Shift | B = Night Shift | G = General Shift | LEAVE = Ordinary Leave | SICK = Sick Leave | HOLIDAY = General Holiday | (S) = Swapped Shift")
        render_styled_html_table(active_df, current_month_str=selected_month)
        
    elif curr_roster_sub == "Actions":
        st.markdown("#### ⚙️ Attendance & Leave Action Center")
        
        c_act1, c_act2 = st.columns([2, 3])
        with c_act1:
            current_system_month = datetime.now().strftime("%B %Y")
            act_month_idx = existing_sheets.index(current_system_month) if current_system_month in existing_sheets else 0
            act_month = custom_select("Select Month for Action:", existing_sheets, "act_month_sel", icon="🗓️", default_idx=act_month_idx)
        
        act_df = sheets_dict[act_month]
        act_df.columns = [str(c).strip() for c in act_df.columns]
        emp_col = act_df.columns[0]
        emp_list = act_df[emp_col].dropna().tolist()
        date_cols = [str(c) for c in act_df.columns[1:]]
        
        st.write("")
        act_c1, act_c2 = st.columns(2)
        with act_c1:
            if st.button("📌 Assign Leave / Holiday", use_container_width=True, type="primary" if st.session_state.get("action_type") == "Mark Leave" else "secondary"):
                st.session_state["action_type"] = "Mark Leave"
                st.rerun()
        with act_c2:
            if st.button("🔄 Swap Calendar Shifts", use_container_width=True, type="primary" if st.session_state.get("action_type") == "Swap Shifts" else "secondary"):
                st.session_state["action_type"] = "Swap Shifts"
                st.rerun()
        
        if st.session_state.get("action_type", "Mark Leave") == "Mark Leave":
            st.markdown(f"##### Assign Leave or Holiday to Employee (for **{act_month}**)")
            c1, c2, c3 = st.columns(3)
            with c1: 
                sel_emp = custom_select("Select Employee:", emp_list, "assign_emp", icon="🧑‍💼")
            with c2: 
                month_obj = datetime.strptime(act_month, "%B %Y")
                last_day = calendar.monthrange(month_obj.year, month_obj.month)[1]
                min_d = month_obj.date()
                max_d = min_d.replace(day=last_day)
                
                cal_val = st.date_input("Select Date:", value=min_d, min_value=min_d, max_value=max_d, key="assign_date_cal")
                sel_date = str(cal_val.day)
            with c3: 
                st.markdown(f'<p style="font-size:{font_size}; font-weight:700; margin-bottom:4px;">Select Type of Leave:</p>', unsafe_allow_html=True)
                leave_type = st.radio("Select Type of Leave:", ["Leave (Casual)", "Sick Leave", "General Holiday"], horizontal=True, label_visibility="collapsed")
            
            row_idx = act_df[act_df[emp_col] == sel_emp].index
            if len(row_idx) > 0:
                emp_row_vals = act_df.loc[row_idx, date_cols].values[0]
                leaves_taken_count = sum(1 for v in emp_row_vals if str(v).upper() in ["LEAVE", "SICK"])
                
                if leaves_taken_count >= 3:
                    st.warning(f"⚠️ **Notice:** **{sel_emp}** has already utilized **{leaves_taken_count} paid leaves** in {act_month}. **Total quota for this month done!**")
                else:
                    st.info(f"ℹ️ Current utilized paid leaves for **{sel_emp}** in {act_month}: **{leaves_taken_count}/3** (Remaining: {max(0, 3 - leaves_taken_count)})")

            if st.button("✅ Confirm & Apply to Calendar", type="primary"):
                code_map = {"Leave (Casual)": "LEAVE", "Sick Leave": "SICK", "General Holiday": "HOLIDAY"}
                assigned_code = code_map.get(leave_type, "LEAVE")
                
                if len(row_idx) > 0:
                    act_df.loc[row_idx, sel_date] = assigned_code
                    st.session_state["sheets_dict"][act_month] = act_df
                    save_rosters(st.session_state["sheets_dict"])
                    
                    if leave_type == "General Holiday":
                        st.success(f"Successfully assigned **General Holiday** to **{sel_emp}** on date **{sel_date} {act_month}**.")
                    else:
                        st.success(f"Successfully assigned **{leave_type}** to **{sel_emp}** on date **{sel_date} {act_month}**!")
                    st.rerun()
                else:
                    st.error("Employee not found in active roster matrix.")
        
        else:
            st.markdown(f"##### Execute Inter-Staff Calendar Shift Swap (for **{act_month}**)")
            st.info("ℹ️ **Rule:** A maximum of TWO swaps are permitted per employee per month. The shifts on the selected dates will be exchanged.")
            
            c1, c2 = st.columns(2)
            with c1: 
                swap_emp1 = custom_select("Employee 1 (Person A):", emp_list, "sw_e1", icon="🧑‍💼")
                
                month_obj = datetime.strptime(act_month, "%B %Y")
                last_day = calendar.monthrange(month_obj.year, month_obj.month)[1]
                min_d = month_obj.date()
                max_d = min_d.replace(day=last_day)
                
                cal_val1 = st.date_input("Date Person A works for Person B:", value=min_d, min_value=min_d, max_value=max_d, key="sw_d1_cal")
                swap_date1 = str(cal_val1.day)
            with c2: 
                emp2_options = [e for e in emp_list if e != swap_emp1]
                swap_emp2 = custom_select("Employee 2 (Person B):", emp2_options, "sw_e2", icon="🧑‍💼")
                
                cal_val2 = st.date_input("Date Person B works for Person A:", value=min_d, min_value=min_d, max_value=max_d, key="sw_d2_cal")
                swap_date2 = str(cal_val2.day)
            
            month_swaps = st.session_state["swap_data"].setdefault(act_month, {})
            emp1_swaps = month_swaps.get(swap_emp1, 0)
            emp2_swaps = month_swaps.get(swap_emp2, 0)
            
            st.markdown(f"""
            <div style="background-color: rgba(0, 102, 204, 0.05); border: 1px solid #CBD5E1; padding: 10px 16px; border-radius: 8px; margin-bottom: 12px; font-size:{font_size};">
                <strong>📊 Live Swap Quota Used for {act_month}:</strong> 
                <span style="color: #0066CC; font-weight: 800; margin-left: 8px;">{swap_emp1}: {emp1_swaps}/2</span> | 
                <span style="color: #0066CC; font-weight: 800;">{swap_emp2}: {emp2_swaps}/2</span>
            </div>
            """, unsafe_allow_html=True)
            
            val1_A_curr = act_df.loc[act_df[emp_col] == swap_emp1, swap_date1].values[0]
            val1_B_curr = act_df.loc[act_df[emp_col] == swap_emp2, swap_date1].values[0]
            
            val2_A_curr = act_df.loc[act_df[emp_col] == swap_emp1, swap_date2].values[0]
            val2_B_curr = act_df.loc[act_df[emp_col] == swap_emp2, swap_date2].values[0]
            
            s1_a = val1_A_curr if str(val1_A_curr).strip() else "OFF"
            s1_b = val1_B_curr if str(val1_B_curr).strip() else "OFF"
            
            s2_a = val2_A_curr if str(val2_A_curr).strip() else "OFF"
            s2_b = val2_B_curr if str(val2_B_curr).strip() else "OFF"
            
            bg_col = "#1E293B" if is_dark else "#F1F5F9"
            txt_col = "#FFFFFF" if is_dark else "#0F172A"
            
            st.markdown(f"""
            <div style="background-color: {bg_col}; padding: 16px; border-radius: 8px; border-left: 5px solid #0066CC; margin-bottom: 18px; color: {txt_col}; font-size:{font_size};">
                <strong>🔍 Live Swap Preview:</strong><br>
                <div style="margin-top: 6px;">• On <strong>Date {swap_date1}</strong>: {swap_emp1} will take {swap_emp2}'s shift (Changing from {s1_a} ➔ <strong>{s1_b}</strong>).</div>
                <div style="margin-top: 4px;">• On <strong>Date {swap_date2}</strong>: {swap_emp2} will take {swap_emp1}'s shift (Changing from {s2_b} ➔ <strong>{s2_a}</strong>).</div>
            </div>
            """, unsafe_allow_html=True)
            
            if emp1_swaps >= 2 or emp2_swaps >= 2:
                st.error("❌ **Swap is not possible. The monthly limit of 2 swaps has already been reached** by one or both selected employees.")
            else:
                if st.button("🔄 Execute Shift Swap", type="primary"): 
                    val1_A = act_df.loc[act_df[emp_col] == swap_emp1, swap_date1].values[0]
                    val1_B = act_df.loc[act_df[emp_col] == swap_emp2, swap_date1].values[0]
                    act_df.loc[act_df[emp_col] == swap_emp1, swap_date1] = val1_B
                    act_df.loc[act_df[emp_col] == swap_emp2, swap_date1] = val1_A
                    
                    if swap_date1 != swap_date2:
                        val2_A = act_df.loc[act_df[emp_col] == swap_emp1, swap_date2].values[0]
                        val2_B = act_df.loc[act_df[emp_col] == swap_emp2, swap_date2].values[0]
                        act_df.loc[act_df[emp_col] == swap_emp1, swap_date2] = val2_B
                        act_df.loc[act_df[emp_col] == swap_emp2, swap_date2] = val2_A
                    
                    st.session_state["sheets_dict"][act_month] = act_df
                    save_rosters(st.session_state["sheets_dict"])
                    
                    month_swaps[swap_emp1] = emp1_swaps + 1
                    month_swaps[swap_emp2] = emp2_swaps + 1
                    st.session_state["swap_data"][act_month] = month_swaps
                    save_swaps(st.session_state["swap_data"])
                    
                    month_meta = st.session_state["swap_meta"].setdefault(act_month, {})
                    transaction_id = f"{swap_emp1}_{swap_date1}__{swap_emp2}_{swap_date2}"
                    month_meta[transaction_id] = {
                        "cells": [
                            (swap_emp1, swap_date1),
                            (swap_emp2, swap_date1),
                            (swap_emp1, swap_date2),
                            (swap_emp2, swap_date2)
                        ]
                    }
                    save_swap_meta(st.session_state["swap_meta"])
                    
                    st.success(f"✅ Shifts successfully swapped between **{swap_emp1}** and **{swap_emp2}**!")
                    st.rerun()
            
    elif curr_roster_sub == "Report":
        st.markdown("#### 🌴 Personnel Attendance Quota & Balance Report")
        st.info("ℹ️ **Internal Team Purpose:** General Holidays (HOLIDAY) are officially credited as working days and do not reduce the employee's standard working quota. Maximum paid leave limit is 3 per month.")
        
        rep_c1, rep_c2 = st.columns(2)
        with rep_c1:
            start_d = st.date_input("Report Start Date:", value=datetime.now())
        with rep_c2:
            end_d = st.date_input("Report End Date:", value=datetime.now())
            
        if st.button("Generate Attendance Report", type="primary"):
            emp_col = active_df.columns[0]
            employees = active_df[emp_col].dropna().tolist()
            report_data = []
            for emp in employees:
                emp_r = active_df[active_df[emp_col] == emp]
                if not emp_r.empty:
                    vals = emp_r.values[0][1:]
                    l_taken = sum(1 for v in vals if str(v).upper() in ["LEAVE", "SICK"])
                    h_taken = sum(1 for v in vals if str(v).upper() == "HOLIDAY")
                    balance = max(0, 3 - l_taken)
                    status_str = "Total quota for this month done!" if l_taken >= 3 else f"{balance} Remaining"
                    
                    e_id = get_emp_id_by_name(emp)
                    disp_name = f"{emp} ({e_id})" if e_id else emp
                    
                    report_data.append({
                        "Employee Name": disp_name,
                        "Allowed Quota": 3,
                        "Leaves Utilized": l_taken,
                        "General Holidays (Working Days)": h_taken,
                        "Quota Status": status_str
                    })
            st.success(f"Generated attendance report for interval: **{start_d.strftime('%d %b %Y')}** to **{end_d.strftime('%d %b %Y')}**")
            render_styled_html_table(pd.DataFrame(report_data), current_month_str=selected_month)

# ==============================================================================
# VIEW 3: AEP
# ==============================================================================
elif current_view == "AEP":
    st.subheader("🪪 AEP")
    st.info("Update compliance dates for all personnel. Staff with AEP passes expiring within 45 days will be automatically flagged on the Dashboard.")
    
    comp_data = []
    for s in st.session_state["staff_registry"]:
        if s["status"] == "Active":
            comp_data.append({
                "NAME": s["name"],
                "DESIGNATION": s.get("designation", "Officer"),
                "AEP NO": s.get("aep_no", ""),
                "AEP Valid Up to": s.get("aep_expiry", ""),
                "PCC Valid Up to": s.get("pcc_expiry", ""),
                "DATE OF ATTENDING AVSEC AWARENESS COURSE": s.get("avsec_date", ""),
                "AVSEC AWARENESS COURSE VALIDITY": s.get("avsec_validity", "")
            })
    
    st.markdown("##### Current Compliance Status Matrix")
    render_styled_html_table(pd.DataFrame(comp_data))
    
    st.write("---")
    st.markdown("##### Administrative Compliance Updates")
    for idx, staff in enumerate(st.session_state["staff_registry"]):
        if staff["status"] == "Active":
            disp_id = f" ({staff.get('emp_id', '')})" if staff.get('emp_id') else ""
            with st.expander(f"🪪 {staff['name']}{disp_id} — Compliance Details Update"):
                c1, c2, c3 = st.columns(3)
                
                def parse_date(date_str):
                    try: return datetime.strptime(date_str, "%Y-%m-%d")
                    except: return datetime.now()
                
                with c1:
                    new_aep_no = st.text_input(f"AEP No:", value=staff.get("aep_no", ""), key=f"trk_aep_no_{idx}")
                    new_aep_iss = st.date_input(f"AEP Issue Date:", value=parse_date(staff.get("aep_issue")), key=f"trk_aep_iss_{idx}")
                    new_aep_exp = st.date_input(f"AEP Valid Up to:", value=parse_date(staff.get("aep_expiry")), key=f"trk_aep_exp_{idx}")
                
                with c2:
                    new_pcc_exp = st.date_input(f"PCC Valid Up to:", value=parse_date(staff.get("pcc_expiry")), key=f"trk_pcc_{idx}")
                    new_avsec_d = st.date_input(f"AVSEC Attended Date:", value=parse_date(staff.get("avsec_date")), key=f"trk_avsec_d_{idx}")
                    new_avsec_exp = st.date_input(f"AVSEC Course Validity:", value=parse_date(staff.get("avsec_validity")), key=f"trk_avsec_v_{idx}")
                
                with c3:
                    st.write("")
                    st.write("")
                    if st.button("💾 Save Compliance Data", key=f"btn_comp_{idx}", type="primary"):
                        st.session_state["staff_registry"][idx]["aep_no"] = new_aep_no.strip().upper()
                        st.session_state["staff_registry"][idx]["aep_issue"] = new_aep_iss.strftime("%Y-%m-%d")
                        st.session_state["staff_registry"][idx]["aep_expiry"] = new_aep_exp.strftime("%Y-%m-%d")
                        st.session_state["staff_registry"][idx]["pcc_expiry"] = new_pcc_exp.strftime("%Y-%m-%d")
                        st.session_state["staff_registry"][idx]["avsec_date"] = new_avsec_d.strftime("%Y-%m-%d")
                        st.session_state["staff_registry"][idx]["avsec_validity"] = new_avsec_exp.strftime("%Y-%m-%d")
                        save_staff_registry(st.session_state["staff_registry"])
                        st.success(f"Compliance dates updated for {staff['name']}!")
                        st.rerun()

# ==============================================================================
# VIEW 4: SETTINGS & HR MANAGEMENT (Password Protected Admin Portal)
# ==============================================================================
elif current_view == "Settings":
    st.subheader("⚙️ Enterprise System Configuration & HR Suite")

    if not st.session_state["settings_authenticated"]:
        st.markdown("### 🔒 Restricted Access")
        st.info("Please enter the administrator PIN (`0477`) to access Settings and HR Management.")
        pwd_input = st.text_input("Enter Admin PIN:", type="password", key="admin_pin_input")
        if st.button("Unlock Settings", type="primary"):
            if pwd_input == SETTINGS_PASSWORD:
                st.session_state["settings_authenticated"] = True
                st.success("Access granted!")
                st.rerun()
            else:
                st.error("❌ Invalid PIN. Please try again.")
    else:
        col_lock, _ = st.columns([1, 5])
        with col_lock:
            if st.button("🔒 Lock Settings", type="secondary"):
                st.session_state["settings_authenticated"] = False
                st.rerun()

        st.divider()
        set_c1, set_c2, set_c3 = st.columns(3)
        with set_c1:
            if st.button("👥 Staff Registry & Handover", use_container_width=True, type="primary" if st.session_state.get("settings_sub") == "Staff" else "secondary"):
                nav_settings("Staff")
        with set_c2:
            if st.button("🗑️ Revert / Clear Leave", use_container_width=True, type="primary" if st.session_state.get("settings_sub") == "ClearLeave" else "secondary"):
                nav_settings("ClearLeave")
        with set_c3:
            if st.button("🖼️ Dashboard Banner & App UI", use_container_width=True, type="primary" if st.session_state.get("settings_sub") == "Banner" else "secondary"):
                nav_settings("Banner")
                
        st.divider()
        curr_settings_sub = st.session_state.get("settings_sub", "Staff")

        if curr_settings_sub == "Staff":
            st.markdown("#### Staff Registry, Passport Photos & Training Handover Overlap")
            
            with st.expander("➕ Register New Joinee / Replacement Staff", expanded=False):
                st.markdown("##### Basic Details")
                col_reg1, col_reg2, col_reg3 = st.columns(3)
                with col_reg1:
                    new_name = st.text_input("Staff Full Name:", placeholder="e.g. RAHUL")
                with col_reg2:
                    new_emp_id = st.text_input("Employee ID:", placeholder="e.g. TASL001")
                with col_reg3:
                    st.markdown(f'<p style="font-size:{font_size}; font-weight:700; margin-bottom:4px;">Designation (Staff Type):</p>', unsafe_allow_html=True)
                    new_desig = st.radio("Designation", ["Officer", "Network Engineer", "Engineer Incharge"], label_visibility="collapsed")
                    
                new_photo = st.file_uploader("Passport Size Photograph (.png, .jpg)", type=["png", "jpg", "jpeg"], key="new_staff_photo")
                
                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    t_start = st.date_input("Training Start Date (Overlap):", value=datetime.now(), key="new_t_start")
                with col_h2:
                    t_end = st.date_input("Training End Date (Full Integration):", value=datetime.now(), key="new_t_end")
                
                st.markdown("##### Compliance Details")
                col_aep1, col_aep2, col_aep3 = st.columns(3)
                with col_aep1:
                    new_aep_n = st.text_input("AEP Number:", placeholder="e.g. AEP-123")
                    new_aep_iss = st.date_input("AEP Issue Date:", value=datetime.now(), key="new_aep_iss")
                with col_aep2:
                    new_aep_exp = st.date_input("AEP Valid Up to:", value=datetime.now(), key="new_aep_exp")
                    new_pcc_exp = st.date_input("PCC Valid Up to:", value=datetime.now(), key="new_pcc_exp")
                with col_aep3:
                    new_avsec_d = st.date_input("AVSEC Attended Date:", value=datetime.now(), key="new_avsec_d")
                    new_avsec_exp = st.date_input("AVSEC Course Validity:", value=datetime.now(), key="new_avsec_exp")
                    
                if st.button("Register Staff & Initialize Training", type="primary"):
                    if new_name.strip():
                        photo_b64 = None
                        if new_photo:
                            b_bytes = new_photo.getvalue()
                            photo_b64 = f"data:{new_photo.type or 'image/png'};base64,{base64.b64encode(b_bytes).decode('utf-8')}"
                            
                        st.session_state["staff_registry"].append({
                            "name": new_name.strip().upper(),
                            "emp_id": new_emp_id.strip().upper(),
                            "designation": new_desig,
                            "aep_no": new_aep_n.strip().upper(),
                            "photo": photo_b64,
                            "status": "Active",
                            "last_day": "",
                            "training_start": t_start.strftime("%Y-%m-%d"),
                            "training_end": t_end.strftime("%Y-%m-%d"),
                            "aep_issue": new_aep_iss.strftime("%Y-%m-%d"),
                            "aep_expiry": new_aep_exp.strftime("%Y-%m-%d"),
                            "pcc_expiry": new_pcc_exp.strftime("%Y-%m-%d"),
                            "avsec_date": new_avsec_d.strftime("%Y-%m-%d"),
                            "avsec_validity": new_avsec_exp.strftime("%Y-%m-%d")
                        })
                        save_staff_registry(st.session_state["staff_registry"])
                        st.success(f"🎉 New personnel **{new_name.strip().upper()}** registered successfully!")
                        st.rerun()
                    else:
                        st.error("Please enter a valid staff name.")

            st.divider()
            st.markdown("#### Manage Current Staff (Photos, ID, Resignation)")
            
            for idx, staff in enumerate(st.session_state["staff_registry"]):
                disp_id = f" ({staff.get('emp_id', '')})" if staff.get('emp_id') else ""
                with st.expander(f"👤 {staff['name']}{disp_id} — Status: {staff['status']}"):
                    
                    col_n1, col_n2, col_n3 = st.columns([1.5, 1, 1.5])
                    with col_n1:
                        new_edit_name = st.text_input(f"Edit Name:", value=staff['name'], key=f"edit_name_{idx}")
                    with col_n2:
                        new_edit_id = st.text_input(f"Edit Employee ID:", value=staff.get('emp_id', ''), key=f"edit_id_{idx}")
                    with col_n3:
                        st.markdown(f'<p style="font-size:{font_size}; font-weight:700; margin-bottom:4px;">Designation:</p>', unsafe_allow_html=True)
                        desig_opts = ["Officer", "Network Engineer", "Engineer Incharge"]
                        curr_desig = staff.get("designation", "Officer")
                        new_edit_desig = st.radio("Desig", desig_opts, index=desig_opts.index(curr_desig) if curr_desig in desig_opts else 0, key=f"edit_desig_{idx}", label_visibility="collapsed", horizontal=True)

                    if st.button("Update Details", key=f"btn_edit_name_{idx}", type="primary"):
                        old_name = staff['name']
                        new_name_clean = new_edit_name.strip().upper()
                        new_id_clean = new_edit_id.strip().upper()
                        
                        needs_save = False
                        
                        if new_id_clean != staff.get('emp_id', ''):
                            st.session_state["staff_registry"][idx]["emp_id"] = new_id_clean
                            needs_save = True
                            
                        if new_edit_desig != staff.get('designation', ''):
                            st.session_state["staff_registry"][idx]["designation"] = new_edit_desig
                            needs_save = True
                            
                        if new_name_clean and new_name_clean != old_name:
                            st.session_state["staff_registry"][idx]["name"] = new_name_clean
                            needs_save = True
                            
                            for m_key, df in st.session_state["sheets_dict"].items():
                                if old_name in df.values:
                                    df.loc[df['Employee'] == old_name, 'Employee'] = new_name_clean
                                    st.session_state["sheets_dict"][m_key] = df
                            save_rosters(st.session_state["sheets_dict"])
                            
                        if needs_save:
                            save_staff_registry(st.session_state["staff_registry"])
                            st.success(f"Details updated successfully!")
                            st.rerun()

                    st.divider()
                    
                    col_p1, col_p2 = st.columns([1, 3])
                    with col_p1:
                        if staff.get("photo"):
                            st.markdown(f'<img src="{staff["photo"]}" class="avatar-img" style="width:70px; height:70px;" />', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div style="width:70px; height:70px; border-radius:50%; background:{cal_palette["accent"]}; color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:20px;">{staff["name"][:2]}</div>', unsafe_allow_html=True)
                    with col_p2:
                        up_photo = st.file_uploader(f"Upload/Change Passport Photo for {staff['name']}", type=["png", "jpg", "jpeg"], key=f"up_photo_{idx}")
                        if up_photo:
                            b_bytes = up_photo.getvalue()
                            photo_b64 = f"data:{up_photo.type or 'image/png'};base64,{base64.b64encode(b_bytes).decode('utf-8')}"
                            st.session_state["staff_registry"][idx]["photo"] = photo_b64
                            save_staff_registry(st.session_state["staff_registry"])
                            st.success(f"✅ Successfully updated photo for {staff['name']}!")
                            st.rerun()

                    st.divider()
                    
                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        res_date = st.date_input(f"Last Working Day (Resignation):", key=f"resign_{idx}", value=datetime.now() if not staff['last_day'] else datetime.strptime(staff['last_day'], "%Y-%m-%d"))
                    with col_s2:
                        st.write("")
                        st.write("")
                        if st.button("Mark Resigned", key=f"btn_res_{idx}", type="secondary"):
                            st.session_state["staff_registry"][idx]["status"] = "Resigned"
                            st.session_state["staff_registry"][idx]["last_day"] = res_date.strftime("%Y-%m-%d")
                            save_staff_registry(st.session_state["staff_registry"])
                            st.success(f"Marked {staff['name']} as Resigned.")
                            st.rerun()

        elif curr_settings_sub == "ClearLeave":
            st.markdown("#### 🗑️ Master Audit Log: Staff Leaves, Holidays & Swaps")
            st.info("Select a month below to view a clean list of only the staff members who took leaves, sick days, holidays, or performed shift swaps.")
            
            existing_sheets_set = list(sheets_dict.keys())
            current_m_str = datetime.now().strftime("%B %Y")
            default_m_idx = existing_sheets_set.index(current_m_str) if current_m_str in existing_sheets_set else 0
            
            clr_month = custom_select("Select Month Roster for Audit:", existing_sheets_set, "clr_month_sel", icon="🗓️", default_idx=default_m_idx)
            
            if clr_month:
                clr_df = sheets_dict[clr_month]
                emp_col = clr_df.columns[0]
                emp_list = clr_df[emp_col].dropna().tolist()
                date_cols = [str(c) for c in clr_df.columns[1:]]
                
                swap_meta = st.session_state.get("swap_meta", {}).get(clr_month, {})
                swapped_cell_map = {}
                for t_id, meta in swap_meta.items():
                    cells = meta.get("cells", [])
                    staffs_in_swap = list(set([c[0] for c in cells]))
                    if len(staffs_in_swap) > 1:
                        for e, d in cells:
                            partner = [s for s in staffs_in_swap if s != e][0]
                            swapped_cell_map[(str(e).strip().upper(), str(d).strip())] = partner

                st.write("")
                st.markdown(f"##### 📋 Leaves, Holidays & Swaps Log for **{clr_month}**")
                
                total_records_found = False
                
                for emp in emp_list:
                    emp_idx = clr_df[clr_df[emp_col] == emp].index
                    if len(emp_idx) > 0:
                        curr_row = clr_df.loc[emp_idx[0]]
                        emp_name_upper = str(emp).strip().upper()
                        
                        staff_records = []
                        for d in date_cols:
                            val = str(curr_row[d]).strip() if pd.notna(curr_row[d]) else ""
                            val_upper = val.upper()
                            
                            is_leave_status = val_upper in ["LEAVE", "SICK", "HOLIDAY"]
                            is_swap_status = (emp_name_upper, str(d).strip()) in swapped_cell_map
                            
                            if is_leave_status or is_swap_status:
                                partner_name = swapped_cell_map.get((emp_name_upper, str(d).strip()), None)
                                staff_records.append((d, val, partner_name))
                                
                        if staff_records:
                            total_records_found = True
                            st.markdown(f"""
                            <div style="background-color: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
                                <div style="font-size: 1.1rem; font-weight: 800; color: #0F172A; margin-bottom: 8px;">
                                    👤 {emp}
                                </div>
                            """, unsafe_allow_html=True)
                            
                            for rec in staff_records:
                                d, shift_val, partner_name = rec
                                type_badge = f"<span style='color: #EF4444; font-weight: 800;'>{shift_val}</span>" if shift_val.upper() in ["LEAVE", "SICK", "HOLIDAY"] else f"<span style='color: #D97706; font-weight: 800;'>SWAP ({shift_val})</span>"
                                partner_badge = f" &nbsp;|&nbsp; <span style='color: #0066CC; font-weight: 800;'>🔄 Swapped with: {partner_name}</span>" if partner_name else ""
                                
                                col_info, col_btn = st.columns([4.2, 1.8])
                                with col_info:
                                    st.markdown(f"""
                                    <div style="padding: 6px 10px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; margin-bottom: 6px; font-size: {font_size};">
                                        <strong>Date {d}:</strong> Status: {type_badge}{partner_badge}
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col_btn:
                                    if st.button("🔄 Revert to Original", key=f"rev_clean_{emp}_{d}", use_container_width=True):
                                        base_rosters = generate_infinite_rosters()
                                        base_df = base_rosters.get(clr_month, clr_df)
                                        b_idx = base_df[base_df[base_df.columns[0]] == emp].index
                                        b_val = str(base_df.loc[b_idx[0], d]).strip() if len(b_idx) > 0 and pd.notna(base_df.loc[b_idx[0], d]) else ""
                                        
                                        clr_df.loc[emp_idx[0], d] = b_val if b_val != 'nan' else ""
                                        st.session_state["sheets_dict"][clr_month] = clr_df
                                        save_rosters(st.session_state["sheets_dict"])
                                        
                                        if partner_name:
                                            if clr_month in st.session_state["swap_meta"]:
                                                to_delete = []
                                                for tk, tm in st.session_state["swap_meta"][clr_month].items():
                                                    for ce, cd in tm.get("cells", []):
                                                        if ce == emp_name_upper and cd == str(d):
                                                            to_delete.append(tk)
                                                for tk in to_delete:
                                                    del st.session_state["swap_meta"][clr_month][tk]
                                                save_swap_meta(st.session_state["swap_meta"])
                                                
                                        st.success(f"Reverted Date {d} for {emp} back to default!")
                                        st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                if not total_records_found:
                    st.success(f"✅ No leaves, holidays, or shift swaps recorded for any staff member in {clr_month}.")

            st.write("---")
            st.markdown("#### 🔄 Reset Monthly Swap Quotas")
            st.caption("If employees are incorrectly showing as having reached their 2-swap limit, use this tool to clear the swap tracking history for a specific month.")
            
            swap_reset_month = custom_select("Select Month to Reset Swaps:", existing_sheets_set, "swap_reset_month_sel", icon="🗓️", default_idx=default_m_idx)
            if st.button("⚠️ Force Reset Swap Quotas for Selected Month", type="secondary"):
                if "swap_data" in st.session_state:
                    st.session_state["swap_data"][swap_reset_month] = {}
                    st.session_state["swap_meta"][swap_reset_month] = {}
                    save_swaps(st.session_state["swap_data"])
                    save_swap_meta(st.session_state["swap_meta"])
                    st.success(f"Swap quotas for {swap_reset_month} have been successfully reset to 0/2 for all employees.")
                else:
                    st.info(f"No swap history found for {swap_reset_month}. Employees are currently at 0/2.")

        elif curr_settings_sub == "Banner":
            st.markdown("#### App Display Settings & Corporate Banner")
            
            st.markdown("##### 🔠 Global App Font Size")
            font_options = {"Small": "13px", "Medium": "14px", "Large": "16px", "Extra Large": "18px"}
            current_font_name = [k for k,v in font_options.items() if v == st.session_state.get("app_font_size", "14px")][0]
            
            c_font1, c_font2 = st.columns([1, 2])
            with c_font1:
                selected_font_name = custom_select("Select App Font Size:", list(font_options.keys()), "font_size_sel", icon="🔠", default_idx=list(font_options.keys()).index(current_font_name))
                if font_options[selected_font_name] != st.session_state.get("app_font_size"):
                    st.session_state["app_font_size"] = font_options[selected_font_name]
                    st.rerun()
            
            st.write("---")
            
            st.markdown("##### 🖼️ Dashboard Banner Customization")
            st.info("Recommended dimensions: 1920×400px. Aspect ratio is strictly preserved.")
            
            if st.session_state.get("banner_b64"):
                st.markdown("**Current Active Banner:**")
                active_b_src = st.session_state["banner_b64"]
                if not active_b_src.startswith("data:image"):
                    active_b_src = f"data:image/png;base64,{active_b_src}"
                st.markdown(f'<div style="border: 1px solid {cal_palette["border"]}; border-radius: 12px; overflow: hidden; margin-bottom: 12px;"><img src="{active_b_src}" style="width: 100%; height: auto; display: block;" /></div>', unsafe_allow_html=True)

            uploaded_b = st.file_uploader("Upload Corporate Banner Image (.png, .jpg, .jpeg)", type=["png", "jpg", "jpeg"], key="cfg_banner")
            if uploaded_b is not None:
                b_bytes = uploaded_b.getvalue()
                b_b64 = f"data:{uploaded_b.type or 'image/png'};base64,{base64.b64encode(b_bytes).decode('utf-8')}"
                
                st.markdown("**New Banner Preview:**")
                st.markdown(f'<div style="border: 2px dashed {cal_palette["accent"]}; border-radius: 12px; overflow: hidden; padding: 4px; margin-bottom: 12px;"><img src="{b_b64}" style="width: 100%; height: auto; display: block;" /></div>', unsafe_allow_html=True)
                
                if st.button("💾 Save Banner to Dashboard", type="primary", use_container_width=True):
                    st.session_state["banner_b64"] = b_b64
                    with open(BANNER_CACHE_PATH, "w", encoding="utf-8") as f:
                        f.write(b_b64)
                    st.success("Banner updated successfully! Navigating to Dashboard...")
                    navigate_to("Dashboard")

            if st.session_state.get("banner_b64") and st.button("🗑️ Reset Banner to Default", type="secondary"):
                st.session_state["banner_b64"] = None
                if os.path.exists(BANNER_CACHE_PATH):
                    os.remove(BANNER_CACHE_PATH)
                st.rerun()
                
            st.write("---")
            
            st.markdown("##### ⚠️ Rebuild Calendar Data Matrix")
            st.error("Clicking this button will completely regenerate the Shift Calendar applying all new Staff Rules (e.g. Network Engineer General shifts). Previous manual shift swaps and leaves marked may be lost.")
            if st.button("🔄 Force Rebuild Roster Data"):
                if os.path.exists(ROSTER_STORAGE_PATH):
                    os.remove(ROSTER_STORAGE_PATH)
                st.session_state["sheets_dict"] = generate_infinite_rosters()
                save_rosters(st.session_state["sheets_dict"])
                st.success("Rosters completely rebuilt applying new Staff rules!")
                st.rerun()
