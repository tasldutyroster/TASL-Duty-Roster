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
        pass

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
# CORE ROSTER GENERATOR (BULLETPROOF SHIFT ANCHORS)
# ==============================================================================
def generate_infinite_rosters(staff_registry):
    sheets_dict = {}
    shift_cycle = ['B', 'B', '', 'A', 'A', 'G', '', '']
    ref_date = datetime(2025, 11, 1).date()
    
    # --- 1. BULLETPROOF SHIFT ANCHORS ---
    # This guarantees Mahesh is ALWAYS slot 0, Ajith is ALWAYS slot 1, etc.
    # No matter how the JSON file gets sorted or modified, their math never breaks.
    anchor_map = {
        "MAHESH": 0, "AJITH": 1, "BALU": 2, "SHINE": 3,
        "NAVANEETH": 4, "AMAL": 5, "SHYAM": 6, "SIVA": 7
    }
    
    emp_to_slot = {}
    slot_index_counter = 8
    
    # Assign permanent base slots
    for staff in staff_registry:
        if not staff.get("replaced_emp"):
            emp_name = staff["name"].strip().upper()
            
            assigned_slot = None
            for anchor_key, anchor_val in anchor_map.items():
                if anchor_key in emp_name:
                    assigned_slot = anchor_val
                    break
                    
            if assigned_slot is not None:
                emp_to_slot[emp_name] = assigned_slot
            else:
                emp_to_slot[emp_name] = slot_index_counter
                slot_index_counter += 1

    # Assign replacements to inherit exact slots
    unmapped = [s for s in staff_registry if s.get("replaced_emp")]
    for staff in unmapped:
        emp_name = staff["name"].strip().upper()
        replaced_name = staff.get("replaced_emp", "").strip().upper()
        
        assigned_slot = None
        for existing_emp, s_idx in emp_to_slot.items():
            if replaced_name in existing_emp or existing_emp in replaced_name:
                assigned_slot = s_idx
                break
                
        if assigned_slot is None:
            for anchor_key, anchor_val in anchor_map.items():
                if anchor_key in replaced_name:
                    assigned_slot = anchor_val
                    break

        if assigned_slot is not None:
            emp_to_slot[emp_name] = assigned_slot
        else:
            emp_to_slot[emp_name] = slot_index_counter
            slot_index_counter += 1

    today = datetime.now()
    start_date = (today.replace(day=1) - timedelta(days=180)).replace(day=1)
    
    # --- 2. BUILD MATRICES ---
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
            
            # Completely exclude if left before month
            if ld_str:
                try:
                    ld = datetime.strptime(ld_str, "%Y-%m-%d").date()
                    if ld < month_start:
                        continue 
                except: pass
                
            # Completely exclude if joining after month
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
                
                if ts_str:
                    try:
                        ts = datetime.strptime(ts_str, "%Y-%m-%d").date()
                        if current_date < ts:
                            is_active_today = False
                    except: pass
                    
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
                    row[str(day)] = ""
            
            if has_active_days or (not ld_str and not ts_str):
                month_data.append(row)
                
        if month_data:
            df = pd.DataFrame(month_data)
        else:
            cols = ["Employee"] + [str(d) for d in range(1, days_in_month + 1)]
            df = pd.DataFrame(columns=cols)
            
        sheets_dict[month_name] = df
        
    return sheets_dict
