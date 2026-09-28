import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import base64
from datetime import datetime
import io
import calendar

# Import from our modular files
from database import *
from styles import get_app_styles

# ==============================================================================
# 1. PAGE CONFIGURATION & INITIALIZATION
# ==============================================================================
st.set_page_config(
    page_title="TASL Shift & Attendance Calendar",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
# 2. DESIGN SYSTEM & CSS INJECTION
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

st.markdown(get_app_styles(cal_palette, font_size), unsafe_allow_html=True)

def render_styled_html_table(df, month_name=None):
    """Renders a gorgeous, professional HTML table with light gray background and crisp black grid borders"""
    base_rosters_dict = generate_infinite_rosters(st.session_state.get("staff_registry"))
    base_df = base_rosters_dict.get(month_name, df) if month_name else df
    
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
        
        emp_name = row[emp_col_name]
        base_row = None
        if month_name:
            b_match = base_df[base_df[base_df.columns[0]] == emp_name]
            if not b_match.empty:
                base_row = b_match.iloc[0]
                
        for col in df.columns:
            val = row[col] if pd.notna(row[col]) else ""
            val_str = str(val).strip()
            if val_str == 'nan': val_str = ""
            
            cell_bg = ""
            cell_extra = ""
            
            if col != emp_col_name and base_row is not None and col in base_row.index:
                b_val = str(base_row[col]).strip() if pd.notna(base_row[col]) else ""
                if b_val == 'nan': b_val = ""
                
                if val_str != b_val:
                    if val_str in ["LEAVE", "SICK"]:
                        cell_bg = "background-color: #FEE2E2; color: #DC2626;"
                    elif val_str == "HOLIDAY":
                        cell_bg = "background-color: #D1FAE5; color: #059669;"
                    else:
                        cell_bg = "background-color: #DBEAFE; color: #1D4ED8;"
                        cell_extra = ' <span style="font-size:0.75rem; font-weight:800;" title="Swapped Shift">(S)</span>'
            
            html += f'<td style="padding: 8px 12px; border: 1px solid #000000; font-weight: 600; {cell_bg}">{val_str}{cell_extra}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

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
    ("AEP Tracker", "🪪 AEP"),
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

            today_real_date = datetime.now().date()
            compliance_alerts = []
            
            for staff in st.session_state["staff_registry"]:
                # Evaluate dynamic status
                res_date_str = staff.get('last_day', '')
                is_active = staff["status"] == "Active"
                if res_date_str:
                    try:
                        res_d = datetime.strptime(res_date_str, "%Y-%m-%d").date()
                        if today_real_date > res_d:
                            is_active = False
                    except: pass

                if is_active:
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
    
    sub_c1, sub_c2, sub_c3 = st.columns(3)
    with sub_c1:
        if st.button("📅 Attendance Grid", use_container_width=True, type="primary" if st.session_state.get("roster_sub") == "Calendar Grid" else "secondary"):
            nav_roster("Calendar Grid")
    with sub_c2:
        if st.button("⚙️ Leave / Swaps", use_container_width=True, type="primary" if st.session_state.get("roster_sub") == "Actions" else "secondary"):
            nav_roster("Actions")
    with sub_c3:
        if st.button("🌴 Quota Report", use_container_width=True, type="primary" if st.session_state.get("roster_sub") == "Report" else "secondary"):
            nav_roster("Report")
            
    st.divider()
    curr_roster_sub = st.session_state.get("roster_sub", "Calendar Grid")
    
    if curr_roster_sub == "Calendar Grid":
        st.markdown(f"#### Monthly Shift & Attendance Calendar — **{selected_month}**")
        st.caption("A = Day Shift | B = Night Shift | G = General Shift | LEAVE = Ordinary Leave | SICK = Sick Leave | HOLIDAY = General Holiday | (S) = Swapped Shift")
        render_styled_html_table(active_df, month_name=selected_month)
        
    elif curr_roster_sub == "Actions":
        st.markdown("#### ⚙️ Attendance & Leave Action Center")
        
        c_act1, c_act2 = st.columns([2, 3])
        with c_act1:
            current_system_month = datetime.now().strftime("%B %Y")
            act_month_idx = existing_sheets.index(current_system_month) if current_system_month in existing_sheets else default_idx
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
                    st.toast("✅ Leave assigned successfully!", icon="🎉")
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
            
            def count_employee_swaps(month_name, employee_name):
                if month_name not in sheets_dict:
                    return 0
                m_df = sheets_dict[month_name]
                base_rosters_dict = generate_infinite_rosters(st.session_state.get("staff_registry"))
                b_df = base_rosters_dict.get(month_name, m_df)
                
                emp_r_idx = m_df[m_df[m_df.columns[0]] == employee_name].index
                b_r_idx = b_df[b_df[b_df.columns[0]] == employee_name].index
                
                if len(emp_r_idx) == 0 or len(b_r_idx) == 0:
                    return 0
                    
                curr_row = m_df.loc[emp_r_idx[0]]
                base_row = b_df.loc[b_r_idx[0]]
                d_cols = [str(c) for c in m_df.columns[1:]]
                
                mod_count = 0
                for d in d_cols:
                    if d in base_row.index:
                        c_val = str(curr_row[d]).strip() if pd.notna(curr_row[d]) else ""
                        b_val = str(base_row[d]).strip() if pd.notna(base_row[d]) else ""
                        if c_val == 'nan': c_val = ""
                        if b_val == 'nan': b_val = ""
                        if c_val != b_val and c_val not in ["LEAVE", "SICK", "HOLIDAY"]:
                            mod_count += 1
                return min(2, mod_count)

            emp1_swaps = count_employee_swaps(act_month, swap_emp1)
            emp2_swaps = count_employee_swaps(act_month, swap_emp2)
            
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
                    
                    st.toast(f"✅ Success! Shifts successfully swapped between {swap_emp1} and {swap_emp2}.", icon="🎉")
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
            render_styled_html_table(pd.DataFrame(report_data))

# ==============================================================================
# VIEW 3: COMPLIANCE TRACKER (AEP)
# ==============================================================================
elif current_view == "AEP Tracker":
    st.subheader("🪪 AEP")
    st.info("Update compliance dates for all personnel. Staff with AEP passes expiring within 45 days will be automatically flagged on the Dashboard.")
    
    comp_data = []
    today_real_date = datetime.now().date()
    for s in st.session_state["staff_registry"]:
        # Evaluate dynamic active status
        res_date_str = s.get('last_day', '')
        is_active = s["status"] == "Active"
        if res_date_str:
            try:
                res_d = datetime.strptime(res_date_str, "%Y-%m-%d").date()
                if today_real_date > res_d:
                    is_active = False
            except: pass

        if is_active:
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
    
    for idx, staff in enumerate(st.session_state["staff_registry"]):
        res_date_str = staff.get('last_day', '')
        is_active = staff["status"] == "Active"
        if res_date_str:
            try:
                res_d = datetime.strptime(res_date_str, "%Y-%m-%d").date()
                if today_real_date > res_d:
                    is_active = False
            except: pass

        if is_active:
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
                        st.toast("✅ Compliance details updated successfully!", icon="💾")
                        st.success(f"Compliance dates updated for {staff['name']}!")
                        st.rerun()

# ==============================================================================
# VIEW 4: SETTINGS & HR MANAGEMENT (Password Protected)
# ==============================================================================
elif current_view == "Settings":
    st.subheader("⚙️ Enterprise System Configuration & HR Suite")

    if not st.session_state["settings_authenticated"]:
        st.markdown("### 🔒 Restricted Access")
        st.info("Please enter the administrator PIN to access Settings and HR Management.")
        pwd_input = st.text_input("Enter Admin PIN:", type="password", key="admin_pin_input")
        if st.button("Unlock Settings", type="primary"):
            if pwd_input == SETTINGS_PASSWORD:
                st.session_state["settings_authenticated"] = True
                st.toast("🔓 Admin access unlocked!", icon="✅")
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
                        st.toast("🎉 Staff registered successfully!", icon="🚀")
                        st.success(f"🎉 New personnel **{new_name.strip().upper()}** registered successfully!")
                        st.rerun()
                    else:
                        st.error("Please enter a valid staff name.")

            st.divider()
            st.markdown("#### Manage Current Staff (Photos, ID, Resignation)")
            
            for idx, staff in enumerate(st.session_state["staff_registry"]):
                # Determine dynamic status based on last working day
                today_real_date = datetime.now().date()
                res_date_str = staff.get('last_day', '')
                is_actually_resigned = False
                if res_date_str:
                    try:
                        res_d = datetime.strptime(res_date_str, "%Y-%m-%d").date()
                        if today_real_date > res_d:
                            is_actually_resigned = True
                    except: pass

                display_status = "Resigned" if (staff['status'] == "Resigned" or is_actually_resigned) else "Active"
                disp_id = f" ({staff.get('emp_id', '')})" if staff.get('emp_id') else ""
                
                with st.expander(f"👤 {staff['name']}{disp_id} — Status: {display_status}"):
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
                            st.toast("✅ Details updated successfully!", icon="💾")
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
                            st.toast("✅ Photo updated successfully!", icon="📸")
                            st.success(f"✅ Successfully updated photo for {staff['name']}!")
                            st.rerun()

                    st.divider()
                    
                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        res_date = st.date_input(f"Last Working Day (Resignation):", key=f"resign_{idx}", value=datetime.now() if not staff['last_day'] else datetime.strptime(staff['last_day'], "%Y-%m-%d"))
                    with col_s2:
                        st.write("")
                        st.write("")
                        if st.button("Save Last Working Day", key=f"btn_res_{idx}", type="secondary"):
                            future_date = res_date.date() if hasattr(res_date, 'date') else res_date
                            current_status = "Resigned" if datetime.now().date() > future_date else "Active"
                            
                            st.session_state["staff_registry"][idx]["status"] = current_status
                            st.session_state["staff_registry"][idx]["last_day"] = res_date.strftime("%Y-%m-%d")
                            save_staff_registry(st.session_state["staff_registry"])
                            st.toast("⚠️ Resignation schedule updated", icon="ℹ️")
                            st.success(f"Last working day for {staff['name']} set to {res_date.strftime('%Y-%m-%d')}.")
                            st.rerun()

        elif curr_settings_sub == "ClearLeave":
            st.markdown("#### 🗑️ Master Revert & Clear Center (All Employees)")
            st.info("Below is the complete list of all modified shifts (Leaves, Sick days, Holidays, and Swaps) across all employees for the selected month. Click 'Revert' on any item to restore it instantly.")
            
            existing_sheets_set = list(sheets_dict.keys())
            current_m_str = datetime.now().strftime("%B %Y")
            default_m_idx = existing_sheets_set.index(current_m_str) if current_m_str in existing_sheets_set else 0
            
            clr_month = custom_select("Select Month Roster:", existing_sheets_set, "clr_month_sel", icon="🗓️", default_idx=default_m_idx)
            
            if clr_month:
                clr_df = sheets_dict[clr_month]
                emp_col_name = clr_df.columns[0]
                emp_list = clr_df[emp_col_name].dropna().tolist()
                
                base_rosters = generate_infinite_rosters(st.session_state.get("staff_registry"))
                base_df = base_rosters.get(clr_month, clr_df)
                
                total_mods = 0
                
                for emp in emp_list:
                    emp_idx_curr = clr_df[clr_df[emp_col_name] == emp].index
                    emp_idx_base = base_df[base_df[base_df.columns[0]] == emp].index
                    
                    if len(emp_idx_curr) > 0 and len(emp_idx_base) > 0:
                        curr_row = clr_df.loc[emp_idx_curr[0]]
                        base_row = base_df.loc[emp_idx_base[0]]
                        date_cols = [str(c) for c in clr_df.columns[1:]]
                        
                        modifications = []
                        for d in date_cols:
                            if d in base_row.index:
                                c_val = str(curr_row[d]).strip() if pd.notna(curr_row[d]) else ""
                                b_val = str(base_row[d]).strip() if pd.notna(base_row[d]) else ""
                                
                                if c_val == 'nan': c_val = ""
                                if b_val == 'nan': b_val = ""
                                
                                if c_val != b_val:
                                    modifications.append((d, b_val, c_val))
                                    
                        if modifications:
                            total_mods += len(modifications)
                            st.markdown(f"##### 👤 {emp}")
                            for mod in modifications:
                                d, b_val, c_val = mod
                                disp_b = b_val if b_val else "OFF"
                                disp_c = c_val if c_val else "OFF"
                                
                                col_text, col_btn = st.columns([4.5, 1.5])
                                with col_text:
                                    st.markdown(f"""
                                    <div style="padding: 8px 12px; border-left: 4px solid #EF4444; background: #FFFFFF; border: 1px solid #CBD5E1; border-left-color: #EF4444; border-radius: 6px; margin-bottom: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                                        <span style="font-size: 1rem; font-weight: 800; color: #0F172A; margin-right: 10px;">Date {d}</span>
                                        <span style="color: #64748B; font-weight: 600; font-size: 0.9rem;">Original: <span style="text-decoration: line-through;">{disp_b}</span> &nbsp;➔&nbsp; <span style="color: #EF4444; font-weight: 800;">{disp_c}</span></span>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col_btn:
                                    if st.button("🔄 Revert", key=f"rev_{emp}_{d}", use_container_width=True):
                                        clr_df.loc[emp_idx_curr[0], d] = b_val if b_val else ""
                                        st.session_state["sheets_dict"][clr_month] = clr_df
                                        save_rosters(st.session_state["sheets_dict"])
                                        st.toast(f"✅ Reverted Date {d} for {emp}!", icon="🔄")
                                        st.success(f"Reverted Date {d} for {emp} back to {disp_b}!")
                                        st.rerun()
                                        
                if total_mods == 0:
                    st.success(f"✅ No modified shifts or leaves found in **{clr_month}**. All staff are strictly following the standard roster.")

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
                    st.toast("✅ Banner updated successfully!", icon="🖼️")
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
                st.session_state["sheets_dict"] = generate_infinite_rosters(st.session_state["staff_registry"])
                save_rosters(st.session_state["sheets_dict"])
                st.toast("🔄 Rosters completely rebuilt!", icon="⚙️")
                st.success("Rosters completely rebuilt applying new Staff rules!")
                st.rerun()
