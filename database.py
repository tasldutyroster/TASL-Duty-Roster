import pandas as pd
import json
import pickle
import os
from datetime import datetime, timedelta
import calendar

# ==============================================================================
# CONSTANTS & FILE PATHS
# ==============================================================================
STAFF_REGISTRY_PATH = "staff_registry_storage.json"
ROSTER_STORAGE_PATH = "roster_storage_v2.pkl"
SWAPS_STORAGE_PATH = "swap_tracking.json"
BANNER_CACHE_PATH = "banner_cache.b64"
SETTINGS_PASSWORD = "0477" # Adjust your admin PIN here

# ==============================================================================
# DATA LOADERS & SAVERS
# ==============================================================================
def load_staff_registry():
    if os.path.exists(STAFF_REGISTRY_PATH):
        try:
            with open(STAFF_REGISTRY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_staff_registry(registry):
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
    with open(ROSTER_STORAGE_PATH, "wb") as f:
        pickle.dump(sheets_dict, f)

# ==============================================================================
# CORE ROSTER GENERATOR (WITH AUTO-REPLACEMENT)
# ==============================================================================
def generate_infinite_rosters(staff_registry):
    """
    Generates roster dataframes for the current month +/- 6 months.
    Automatically assigns new joinees to the slot of the resigned employee they are replacing.
    """
    sheets_dict = {}
    
    # 1. Group Staff into "Slots" to handle replacements seamlessly
    # A Slot is a continuous row on the roster. If Shyam resigns on Oct 1, 
    # and a new employee joins to replace him, they occupy the same Slot.
    roster_slots = {}
    
    # Sort staff so active/older staff get slots first, newer replacements map to them
    sorted_staff = sorted(staff_registry, key=lambda x: x.get('training_start', '2000-01-01'))
    
    slot_index = 0
    for staff in sorted_staff:
        designation = staff.get("designation", "Officer")
        emp_name = staff["name"].strip().upper()
        
        # Check if there is a slot with a resigned employee of the SAME designation
        assigned_to_existing_slot = False
        for s_idx, slot_occupants in roster_slots.items():
            last_occupant = slot_occupants[-1]
            
            # If the last occupant of this slot is resigning/resigned and designations match
            if last_occupant.get("status") == "Resigned" or last_occupant.get("last_day"):
                if last_occupant.get("designation", "Officer") == designation:
                    roster_slots[s_idx].append(staff)
                    assigned_to_existing_slot = True
                    break
        
        # If no slot was available to take over, create a new row/slot
        if not assigned_to_existing_slot:
            roster_slots[slot_index] = [staff]
            slot_index += 1

    # 2. Build the Matrices for each month
    today = datetime.now()
    start_date = (today.replace(day=1) - timedelta(days=180)).replace(day=1) # 6 months back
    
    for month_offset in range(12): # 12 months total coverage
        # Calculate month and year
        m = (start_date.month + month_offset - 1) % 12 + 1
        y = start_date.year + (start_date.month + month_offset - 1) // 12
        
        month_name = datetime(y, m, 1).strftime("%B %Y")
        days_in_month = calendar.monthrange(y, m)[1]
        
        month_data = []
        
        # 3. Process Each Roster Slot (Row)
        for s_idx, occupants in roster_slots.items():
            # Figure out who occupies this slot on THIS specific month
            # We iterate through the occupants of the slot and see who is active
            
            for staff in occupants:
                emp_name = staff["name"].strip().upper()
                designation = staff.get("designation", "Officer")
                last_day_str = staff.get("last_day", "")
                training_start_str = staff.get("training_start", "")
                
                # Check if they are active in this month at all
                valid_for_month = True
                month_start = datetime(y, m, 1).date()
                month_end = datetime(y, m, days_in_month).date()
                
                if last_day_str:
                    try:
                        ld = datetime.strptime(last_day_str, "%Y-%m-%d").date()
                        if ld < month_start:
                            valid_for_month = False # They left before this month started
                    except: pass
                    
                if training_start_str:
                    try:
                        ts = datetime.strptime(training_start_str, "%Y-%m-%d").date()
                        if ts > month_end:
                            valid_for_month = False # They join after this month ends
                    except: pass

                if not valid_for_month:
                    continue # Skip to the next person sharing this slot

                # Build the row for this person
                row = {"Employee": emp_name}
                
                # DEFAULT SHIFT LOGIC (Replace this block with your custom math if needed)
                for day in range(1, days_in_month + 1):
                    current_date = datetime(y, m, day).date()
                    
                    # If date is past their last day, leave it blank (the replacement will fill the next row)
                    if last_day_str:
                        try:
                            ld = datetime.strptime(last_day_str, "%Y-%m-%d").date()
                            if current_date > ld:
                                row[str(day)] = ""
                                continue
                        except: pass
                    
                    # Network Engineers get General Shift natively
                    if designation == "Network Engineer":
                        shift = "G" if current_date.weekday() < 5 else "OFF"
                    else:
                        # Standard A/B/OFF rotating logic based on slot index
                        # 0,1 = A, 2,3 = B, 4,5 = OFF (Basic placeholder rotation)
                        cycle = (current_date.toordinal() + s_idx * 2) % 6
                        if cycle < 2: shift = "A"
                        elif cycle < 4: shift = "B"
                        else: shift = "OFF"
                        
                    row[str(day)] = shift
                    
                month_data.append(row)
                
        # Create Dataframe
        if month_data:
            df = pd.DataFrame(month_data)
        else:
            cols = ["Employee"] + [str(d) for d in range(1, days_in_month + 1)]
            df = pd.DataFrame(columns=cols)
            
        sheets_dict[month_name] = df
        
    return sheets_dict
