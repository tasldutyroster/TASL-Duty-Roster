import os
import json
import base64
from datetime import datetime
import pandas as pd
import numpy as np
import calendar

BANNER_CACHE_PATH = "banner_cache.b64"
STAFF_STORAGE_PATH = "staff_registry_storage.json"
ROSTER_STORAGE_PATH = "roster_storage_v2.pkl"  
SWAP_STORAGE_PATH = "swap_tracking.json"    
SETTINGS_PASSWORD = "0477"  

DEFAULT_STAFF = [
    {"name": "MAHESH", "emp_id": "", "designation": "Officer", "aep_no": "", "pcc_expiry": "", "avsec_date": "", "avsec_validity": "", "photo": None, "status": "Active", "last_day": "", "training_start": "", "training_end": "", "aep_issue": "", "aep_expiry": ""},
    {"name": "AJITH", "emp_id": "", "designation": "Officer", "aep_no": "", "pcc_expiry": "", "avsec_date": "", "avsec_validity": "", "photo": None, "status": "Active", "last_day": "", "training_start": "", "training_end": "", "aep_issue": "", "aep_expiry": ""},
    {"name": "BALU", "emp_id": "", "designation": "Officer", "aep_no": "", "pcc_expiry": "", "avsec_date": "", "avsec_validity": "", "photo": None, "status": "Active", "last_day": "", "training_start": "", "training_end": "", "aep_issue": "", "aep_expiry": ""},
    {"name": "SHINE", "emp_id": "", "designation": "Officer", "aep_no": "", "pcc_expiry": "", "avsec_date": "", "avsec_validity": "", "photo": None, "status": "Active", "last_day": "", "training_start": "", "training_end": "", "aep_issue": "", "aep_expiry": ""},
    {"name": "NAVANEETH", "emp_id": "", "designation": "Officer", "aep_no": "", "pcc_expiry": "", "avsec_date": "", "avsec_validity": "", "photo": None, "status": "Active", "last_day": "", "training_start": "", "training_end": "", "aep_issue": "", "aep_expiry": ""},
    {"name": "AMAL", "emp_id": "", "designation": "Officer", "aep_no": "", "pcc_expiry": "", "avsec_date": "", "avsec_validity": "", "photo": None, "status": "Active", "last_day": "", "training_start": "", "training_end": "", "aep_issue": "", "aep_expiry": ""},
    {"name": "SHYAM", "emp_id": "", "designation": "Officer", "aep_no": "", "pcc_expiry": "", "avsec_date": "", "avsec_validity": "", "photo": None, "status": "Active", "last_day": "", "training_start": "", "training_end": "", "aep_issue": "", "aep_expiry": ""},
    {"name": "SIVA", "emp_id": "", "designation": "Officer", "aep_no": "", "pcc_expiry": "", "avsec_date": "", "avsec_validity": "", "photo": None, "status": "Active", "last_day": "", "training_start": "", "training_end": "", "aep_issue": "", "aep_expiry": ""}
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

def generate_infinite_rosters(staff_registry=None):
    if staff_registry is None:
        staff_registry = load_staff_registry()
        
    staff_list = [s["name"] for s in staff_registry if s["status"] == "Active"]
    if not staff_list:
        staff_list = ["MAHESH", "AJITH", "BALU", "SHINE", "NAVANEETH", "AMAL", "SHYAM", "SIVA"]
        
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
            for s in staff_registry:
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