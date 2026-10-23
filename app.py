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
    st
