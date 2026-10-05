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
SETTINGS_PASSWORD = "123" # <--- Change to your preferred PIN if needed
SETTINGS_PASSWORD = "123"

BACKUP_DIR = "backups"

# ==============================================================================
# AUTO-BACKUP HELPER
# ==============================================================================
def create_backup(file_path):
"""Creates a secure backup of the specified file inside the backups directory."""
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
# DATA LOADERS & SAVERS (WITH PERMANENT STATUS LOCK & AUTO-BACKUP)
# DATA LOADERS & SAVERS
# ==============================================================================
def load_staff_registry():
registry = []
if os.path.exists(STAFF_REGISTRY_PATH):
try:
with open(STAFF_REGISTRY_PATH, "r", encoding="utf-8") as f:
registry = json.load(f)
except:
registry = []

    # Permanently enforce 'Resigned' status if last_day has passed
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
# CORE ROSTER GENERATOR (EXACT SHIFT CYCLE & AUTO-REPLACEMENT SLOT MAPPING)
# CORE ROSTER GENERATOR (SEAMLESS SLOT INHERITANCE FOR REPLACEMENTS)
# ==============================================================================
def generate_infinite_rosters(staff_registry):
sheets_dict = {}
shift_cycle = ['B', 'B', '', 'A', 'A', 'G', '', '']
ref_date = datetime(2025, 11, 1).date()

    # Group staff into persistent slot rows based on explicit replacement mapping
roster_slots = {}
sorted_staff = sorted(staff_registry, key=lambda x: x.get('training_start', '2000-01-01'))

slot_index = 0
for staff in sorted_staff:
replaced_emp = staff.get("replaced_emp", "").strip().upper()
assigned_to_existing_slot = False

if replaced_emp:
for s_idx, slot_occupants in roster_slots.items():
if any(occ["name"].strip().upper() == replaced_emp for occ in slot_occupants):
roster_slots[s_idx].append(staff)
assigned_to_existing_slot = True
break

if not assigned_to_existing_slot:
roster_slots[slot_index] = [staff]
slot_index += 1

today = datetime.now()
start_date = (today.replace(day=1) - timedelta(days=180)).replace(day=1)

for month_offset in range(12):
m = (start_date.month + month_offset - 1) % 12 + 1
y = start_date.year + (start_date.month + month_offset - 1) // 12

month_name = datetime(y, m, 1).strftime("%B %Y")
days_in_month = calendar.monthrange(y, m)[1]

month_data = []

        # Process each structural roster slot row
for s_idx, occupants in roster_slots.items():
            for staff in occupants:
                emp_name = staff["name"].strip().upper()
                designation = staff.get("designation", "Officer")
                last_day_str = staff.get("last_day", "")
                training_start_str = staff.get("training_start", "")
                
                valid_for_month = True
                month_start = datetime(y, m, 1).date()
                month_end = datetime(y, m, days_in_month).date()
            month_start = datetime(y, m, 1).date()
            month_end = datetime(y, m, days_in_month).date()
            
            # Build a combined row map for this slot across the month
            slot_row = {"Employee": ""}
            for day in range(1, days_in_month + 1):
                slot_row[str(day)] = ""

                if last_day_str:
                    try:
                        ld = datetime.strptime(last_day_str, "%Y-%m-%d").date()
                        if ld < month_start:
                            valid_for_month = False
                    except: pass
                    
                if training_start_str:
                    try:
                        ts = datetime.strptime(training_start_str, "%Y-%m-%d").date()
                        if ts > month_end:
                            valid_for_month = False
                    except: pass

                if not valid_for_month:
                    continue

                row = {"Employee": emp_name}
                base_offset = s_idx * 3
            active_occupant_found = False
            
            for day in range(1, days_in_month + 1):
                current_date = datetime(y, m, day).date()

                for day in range(1, days_in_month + 1):
                    current_date = datetime(y, m, day).date()
                # Determine who is active in this specific slot on this specific day
                active_staff_on_day = None
                for staff in occupants:
                    name = staff["name"].strip().upper()
                    last_day_str = staff.get("last_day", "")
                    training_start_str = staff.get("training_start", "")

                    # Check validity for this specific calendar day
                    is_valid = True
                    if training_start_str:
                        try:
                            ts = datetime.strptime(training_start_str, "%Y-%m-%d").date()
                            if current_date < ts:
                                is_valid = False
                        except: pass
                        
if last_day_str:
try:
ld = datetime.strptime(last_day_str, "%Y-%m-%d").date()
if current_date > ld:
                                row[str(day)] = ""
                                continue
                                is_valid = False
except: pass
                        
                    if is_valid:
                        active_staff_on_day = staff
                        break
                
                if active_staff_on_day:
                    active_occupant_found = True
                    slot_row["Employee"] = active_staff_on_day["name"].strip().upper()

                    designation = active_staff_on_day.get("designation", "Officer")
if designation == "Network Engineer":
shift = "G" if current_date.weekday() < 5 else ""
else:
absolute_day_index = (current_date - ref_date).days
                        shift_idx = (absolute_day_index + base_offset) % len(shift_cycle)
                        shift_idx = (absolute_day_index + (s_idx * 3)) % len(shift_cycle)
shift = shift_cycle[shift_idx]

                    row[str(day)] = shift if shift is not None else ""
                    
                month_data.append(row)
                    slot_row[str(day)] = shift if shift is not None else ""
                else:
                    slot_row[str(day)] = ""
            
            # If someone occupied this slot during this month, add the row
            if active_occupant_found and slot_row["Employee"]:
                month_data.append(slot_row)

if month_data:
df = pd.DataFrame(month_data)
else:
cols = ["Employee"] + [str(d) for d in range(1, days_in_month + 1)]
df = pd.DataFrame(columns=cols)

sheets_dict[month_name] = df

return sheets_dict
