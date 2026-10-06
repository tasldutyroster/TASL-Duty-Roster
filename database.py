import pandas as pd
import json
import pickle
import os
from datetime import datetime, timedelta
import calendar
import shutil

# ==============================================================================
# CONSTANTS & FILE PATHS
# ==============================================================================
STAFF_REGISTRY_PATH = "staff_registry_storage.json"
ROSTER_STORAGE_PATH = "roster_storage_v2.pkl"
SWAPS_STORAGE_PATH = "swap_tracking.json"
BANNER_CACHE_PATH = "banner_cache.b64"
SETTINGS_PASSWORD = "0477"
BACKUP_DIR = "backups"

def create_backup(file_path):
    if not os.path.exists(file_path): return
    try:
        if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)
        file_name = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_part, ext_part = os.path.splitext(file_name)
        backup_path = os.path.join(BACKUP_DIR, f"{name_part}_backup_{timestamp}{ext_part}")
        shutil.copy2(file_path, backup_path)
        existing_backups = sorted([os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.startswith(name_part) and f.endswith(ext_part)])
        if len(existing_backups) > 10:
            for old_file in existing_backups[:-10]: os.remove(old_file)
    except Exception: pass

def load_staff_registry():
    registry = []
    if os.path.exists(STAFF_REGISTRY_PATH):
        try:
            with open(STAFF_REGISTRY_PATH, "r", encoding="utf-8") as f: registry = json.load(f)
        except: registry = []
    today_date = datetime.now().date()
    updated = False
    for staff in registry:
        last_day_str = staff.get("last_day", "").strip()
        if last_day_str:
            try:
                ld = datetime.strptime(last_day_str, "%Y-%m-%d").date()
                if today_date > ld and staff.get("status") != "Resigned":
                    staff["status"] = "Resigned"
                    updated = True
            except: pass
    if updated: save_staff_registry(registry)
    return registry

def save_staff_registry(registry):
    create_backup(STAFF_REGISTRY_PATH)
    with open(STAFF_REGISTRY_PATH, "w", encoding="utf-8") as f: json.dump(registry, f, indent=4)

def load_swaps():
    if os.path.exists(SWAPS_STORAGE_PATH):
        try:
            with open(SWAPS_STORAGE_PATH, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def save_swaps(swap_data):
    create_backup(SWAPS_STORAGE_PATH)
    with open(SWAPS_STORAGE_PATH, "w", encoding="utf-8") as f: json.dump(swap_data, f, indent=4)

def load_rosters():
    if os.path.exists(ROSTER_STORAGE_PATH):
        try:
            with open(ROSTER_STORAGE_PATH, "rb") as f: return pickle.load(f)
        except: return {}
    return {}

def save_rosters(sheets_dict):
    create_backup(ROSTER_STORAGE_PATH)
    with open(ROSTER_STORAGE_PATH, "wb") as f: pickle.dump(sheets_dict, f)

# ==============================================================================
# CORE ROSTER GENERATOR (NEW OCTOBER ONGOING PLAN)
# ==============================================================================
def generate_infinite_rosters(staff_registry):
    sheets_dict = {}
    shift_cycle = ['B', 'B', '', 'A', 'A', 'G', '', '']
    ref_date = datetime(2026, 10, 1).date()
    
    # Map locked directly to the new October Excel sheet pattern
    anchor_map = {
        "MAHESH": 0,
        "AJITH": 1,
        "BALU": 2,      
        "SHINE": 3,
        "NAVANEETH": 4,
        "AMAL": 5, 
        # Slot 6 is the vacant row shown between Amal and Nandakishor
        "NANDAKISHOR": 7 
    }
    
    # Exact top-to-bottom visual row order from the Excel sheet
    display_order = [0, 1, 2, 3, 4, 5, 6, 7] 
    
    emp_to_slot = {}
    slot_index_counter = 8
    
    for staff in staff_registry:
        emp_name = staff["name"].strip().upper()
        assigned_slot = None
        
        replaced_name = staff.get("replaced_emp", "").strip().upper()
        if replaced_name:
            for key, val in anchor_map.items():
                if key in replaced_name:
                    assigned_slot = val
                    break
                    
        if assigned_slot is None:
            for key, val in anchor_map.items():
                if key in emp_name:
                    assigned_slot = val
                    break
                    
        if assigned_slot is not None:
            emp_to_slot[emp_name] = assigned_slot
        else:
            emp_to_slot[emp_name] = slot_index_counter
            slot_index_counter += 1

    today = datetime.now()
    start_date = (today.replace(day=1) - timedelta(days=180)).replace(day=1)
    
    for i in range(8, slot_index_counter):
        display_order.append(i)
    
    # BUILD MATRICES
    for month_offset in range(12):
        m = (start_date.month + month_offset - 1) % 12 + 1
        y = start_date.year + (start_date.month + month_offset - 1) // 12
        
        month_name = datetime(y, m, 1).strftime("%B %Y")
        days_in_month = calendar.monthrange(y, m)[1]
        month_start = datetime(y, m, 1).date()
        
        month_data = []
        
        # Render all 8 rows to permanently match the Excel structure
        for s_idx in display_order:
            slot_staff_list = [s for s in staff_registry if emp_to_slot.get(s["name"].strip().upper()) == s_idx]
            row_label = "VACANT"
            designation = "Officer"
            
            if slot_staff_list:
                valid_staff = None
                for s in slot_staff_list:
                    ld_str = s.get("last_day", "")
                    if ld_str:
                        try:
                            ld = datetime.strptime(ld_str, "%Y-%m-%d").date()
                            if ld < month_start:
                                continue 
                        except: pass
                    valid_staff = s
                
                if valid_staff:
                    row_label = valid_staff["name"].strip().upper()
                    designation = valid_staff.get("designation", "Officer")
            
            # Keep rows 0-7 always visible. Hide any dynamically created slots > 7 if vacant.
            if s_idx >= 8 and row_label == "VACANT":
                continue
                
            row = {"Employee": row_label}
            
            for day in range(1, days_in_month + 1):
                current_date = datetime(y, m, day).date()
                if designation == "Network Engineer":
                    shift = "G" if current_date.weekday() < 5 else ""
                else:
                    # The exact mathematical sequence extracted from the new October plan
                    day_diff = (current_date - ref_date).days
                    shift_idx = (5 - s_idx + day_diff) % 8
                    shift = shift_cycle[shift_idx]
                row[str(day)] = shift if shift is not None else ""
                
            month_data.append(row)
            
        if month_data:
            df = pd.DataFrame(month_data)
        else:
            cols = ["Employee"] + [str(d) for d in range(1, days_in_month + 1)]
            df = pd.DataFrame(columns=cols)
            
        sheets_dict[month_name] = df
        
    return sheets_dict