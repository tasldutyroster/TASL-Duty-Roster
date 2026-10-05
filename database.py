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
SETTINGS_PASSWORD = "123"

BACKUP_DIR = "backups"

# ==============================================================================
# AUTO-BACKUP HELPER
# ==============================================================================
def create_backup(file_path):
    if not os.path.exists(file_path):
        return
    try:
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        
        file_name = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_part, ext_part = os.path.splitext(file_name)
        
        backup_filename = f"{name_part}_backup_{timestamp}{ext_part}"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        shutil.copy2(file_path, backup_path)
        
        existing_backups = sorted([
            os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) 
            if f.startswith(name_part) and f.endswith(ext_part)
        ])
        if len(existing_backups) > 10:
            for old_file in existing_backups[:-10]:
                os.remove(old_file)
                
    except Exception as e:
        print(f"Backup failed for {file_path}: {e}")

# ==============================================================================
# DATA LOADERS & SAVERS (WITH PERMANENT STATUS LOCK)
# ==============================================================================
def load_staff_registry():
    registry = []
    if os.path.exists(STAFF_REGISTRY_PATH):
        try:
            with open(STAFF_REGISTRY_PATH, "r", encoding="utf-8") as f:
                registry = json.load(f)
        except:
            registry = []
            
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
            
    if updated:
        save_staff_registry(registry)
        
    return registry

def save_staff_registry(registry):
    create_backup(STAFF_REGISTRY_PATH)
    with open(STAFF_REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=4)

def load_swaps():
    if os.path.exists(SWAPS_STORAGE_PATH):
        try:
            with open(SWAPS_STORAGE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_swaps(swap_data):
    create_backup(SWAPS_STORAGE_PATH)
    with open(SWAPS_STORAGE_PATH, "w", encoding="utf-8") as f:
        json.dump(swap_data, f, indent=4)

def load_rosters():
    if os.path.exists(ROSTER_STORAGE_PATH):
        try:
            with open(ROSTER_STORAGE_PATH, "rb") as f:
                return pickle.load(f)
        except:
            return {}
    return {}

def save_rosters(sheets_dict):
    create_backup(ROSTER_STORAGE_PATH)
    with open(ROSTER_STORAGE_PATH, "wb") as f:
        pickle.dump(sheets_dict, f)

# ==============================================================================
# CORE ROSTER GENERATOR (FLATTENED ROWS + INHERITED MATH)
# ==============================================================================
def generate_infinite_rosters(staff_registry):
    sheets_dict = {}
    shift_cycle = ['B', 'B', '', 'A', 'A', 'G', '', '']
    ref_date = datetime(2025, 11, 1).date()
    
    # 1. Map every employee to a permanent shift math slot
    emp_to_slot = {}
    slot_index_counter = 0
    
    # Base staff get original slots
    for staff in staff_registry:
        if not staff.get("replaced_emp"):
            emp_name = staff["name"].strip().upper()
            emp_to_slot[emp_name] = slot_index_counter
            slot_index_counter += 1
            
    # Replacements inherit the slot of the person they replaced
    unmapped = [s for s in staff_registry if s.get("replaced_emp")]
    max_iters = 10
    while unmapped and max_iters > 0:
        still_unmapped = []
        for staff in unmapped:
            emp_name = staff["name"].strip().upper()
            replaced_name = staff.get("replaced_emp", "").strip().upper()
            if replaced_name in emp_to_slot:
                emp_to_slot[emp_name] = emp_to_slot[replaced_name]
            else:
                still_unmapped.append(staff)
        unmapped = still_unmapped
        max_iters -= 1

    # Any remaining unmapped (due to typos in replaced_emp) get a new slot
    for staff in unmapped:
        emp_name = staff["name"].strip().upper()
        emp_to_slot[emp_name] = slot_index_counter
        slot_index_counter += 1

    today = datetime.now()
    start_date = (today.replace(day=1) - timedelta(days=180)).replace(day=1)
    
    # 2. Build Matrices Month by Month
    for month_offset in range(12):
        m = (start_date.month + month_offset - 1) % 12 + 1
        y = start_date.year + (start_date.month + month_offset - 1) // 12
        
        month_name = datetime(y, m, 1).strftime("%B %Y")
        days_in_month = calendar.monthrange(y, m)[1]
        month_start = datetime(y, m, 1).date()
        month_end = datetime(y, m, days_in_month).date()
        
        month_data = []
        
        for staff in staff_registry:
            emp_name = staff["name"].strip().upper()
            s_idx = emp_to_slot.get(emp_name, 0)
            designation = staff.get("designation", "Officer")
            
            ts_str = staff.get("training_start", "")
            ld_str = staff.get("last_day", "")
            
            # Remove entirely if they left BEFORE this month started
            if ld_str:
                try:
                    ld = datetime.strptime(ld_str, "%Y-%m-%d").date()
                    if ld < month_start:
                        continue 
                except: pass
                
            # Remove entirely if they join AFTER this month ends
            if ts_str:
                try:
                    ts = datetime.strptime(ts_str, "%Y-%m-%d").date()
                    if ts > month_end:
                        continue
                except: pass

            row = {"Employee": emp_name}
            has_active_days = False
            
            for day in range(1, days_in_month + 1):
                current_date = datetime(y, m, day).date()
                is_active_today = True
                
                # Check if joined yet
                if ts_str:
                    try:
                        ts = datetime.strptime(ts_str, "%Y-%m-%d").date()
                        if current_date < ts:
                            is_active_today = False
                    except: pass
                    
                # Check if already left
                if ld_str:
                    try:
                        ld = datetime.strptime(ld_str, "%Y-%m-%d").date()
                        if current_date > ld:
                            is_active_today = False
                    except: pass
                    
                if is_active_today:
                    has_active_days = True
                    if designation == "Network Engineer":
                        shift = "G" if current_date.weekday() < 5 else ""
                    else:
                        absolute_day_index = (current_date - ref_date).days
                        shift_idx = (absolute_day_index + (s_idx * 3)) % len(shift_cycle)
                        shift = shift_cycle[shift_idx]
                    row[str(day)] = shift if shift is not None else ""
                else:
                    row[str(day)] = "" # Empty for inactive days
            
            if has_active_days or (not ld_str and not ts_str):
                month_data.append(row)
                
        if month_data:
            df = pd.DataFrame(month_data)
        else:
            cols = ["Employee"] + [str(d) for d in range(1, days_in_month + 1)]
            df = pd.DataFrame(columns=cols)
            
        sheets_dict[month_name] = df
        
    return sheets_dict
