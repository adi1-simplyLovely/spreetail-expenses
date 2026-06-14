import csv
import io
import re
from datetime import datetime, date
from dateutil import parser as date_parser
from sqlalchemy.orm import Session
from models import User, GroupMember, Expense, ExpenseSplit, Settlement
from utils.split_calculator import (
    calculate_equal_split, 
    calculate_percentage_split, 
    calculate_unequal_split, 
    calculate_share_split
)
from utils.currency import convert_to_inr

def normalize_date(date_str: str) -> date:
    """
    Normalizes messy dates (e.g., 'Mar-14', '15/04/2024') to standard Python date objects.
    Enforces DD-MM-YYYY as the primary format (Anomaly 15).
    """
    if not date_str or date_str.strip() == "":
        return None
    try:
        # dayfirst=True enforces DD-MM-YYYY primary format
        dt = date_parser.parse(date_str.strip(), dayfirst=True)
        return dt.date()
    except Exception:
        return None

def parse_split_details(details_str: str) -> dict:
    """
    Parses a string like 'Aisha:30;Rohan:30;Priya:40' into a dictionary.
    """
    if not details_str or details_str.strip() == "":
        return {}
        
    result = {}
    parts = details_str.split(";")
    for part in parts:
        if ":" in part:
            name, val = part.split(":")
            try:
                result[name.strip().title()] = float(val.strip())
            except ValueError:
                pass
    return result

def get_or_create_user(db: Session, name: str, group_id: int, joined_date: date) -> int:
    """
    Finds a user by name, creates them if missing, and ensures they are in the group.
    """
    name = name.strip().title()
    user = db.query(User).filter(User.name == name).first()
    
    if not user:
        # Create user with a dummy email
        email = f"{name.lower().replace(' ', '')}@example.com"
        user = User(name=name, email=email, password_hash="dummy")
        db.add(user)
        db.flush()
        
    # Check if they are in the group
    membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user.id
    ).first()
    
    if not membership:
        membership = GroupMember(
            group_id=group_id,
            user_id=user.id,
            joined_at=joined_date
        )
        db.add(membership)
        db.flush()
        
    return user.id


def process_csv_import(file_content: str, group_id: int, db: Session) -> dict:
    """
    The core 5-stage processing pipeline for the CSV import.
    Handles all 18 anomalies robustly.
    """
    report = {
        "total_rows": 0,
        "imported": 0,
        "skipped": 0,
        "flagged": 0,
        "anomalies": []
    }
    
    # Track seen combinations for Duplicate detection (Anomaly 01 - First row wins)
    seen_hashes = set()
    
    # Read CSV
    reader = csv.DictReader(io.StringIO(file_content))
    
    # Fetch member logic for dates (Anomaly 16)
    # We load them later, dynamically.
    
    for row_num, row in enumerate(reader, start=2): # Start 2 because of header
        report["total_rows"] += 1
        
        # --- STAGE 1: Normalize Data & Basic Extraction ---
        raw_date = row.get("Date", "")
        raw_desc = row.get("Description", "").strip()
        raw_paid_by = row.get("Paid By", "").strip().title()
        raw_amount = row.get("Amount", "0")
        currency = row.get("Currency", "INR").strip().upper()
        raw_split_type = row.get("Split Type", "").strip().lower()
        raw_split_details = row.get("Split Details", "")
        notes = row.get("Notes", "").strip().lower()
        
        # Parse Amount
        try:
            # Handle commas in numbers e.g. "1,500"
            amount = float(raw_amount.replace(",", ""))
        except ValueError:
            report["skipped"] += 1
            report["anomalies"].append(f"Row {row_num}: Invalid amount format. Skipped.")
            continue
            
        # Parse Date
        exp_date = normalize_date(raw_date)
        if not exp_date:
            report["skipped"] += 1
            report["anomalies"].append(f"Row {row_num}: Missing or invalid date format. Skipped.")
            continue
            
        # --- STAGE 2: Handle Structural Anomalies ---
        
        # Anomaly 01: Duplicate rows (First-row-wins)
        row_hash = f"{exp_date.isoformat()}|{raw_desc.lower()}|{raw_paid_by}|{amount}"
        if row_hash in seen_hashes:
            report["skipped"] += 1
            report["anomalies"].append(f"Row {row_num}: Duplicate entry detected ({raw_desc}). Skipped.")
            continue
        seen_hashes.add(row_hash)
        
        # Anomaly 10: Explicit notes saying "wrong" or "ignore"
        if "wrong" in notes or "ignore" in notes or "duplicate" in notes:
            report["skipped"] += 1
            report["anomalies"].append(f"Row {row_num}: Skipped due to explicit note ({notes}).")
            continue
            
        # --- STAGE 3: Handle Semantic Anomalies ---
        
        # Get/Create Payer
        payer_id = get_or_create_user(db, raw_paid_by, group_id, exp_date)
        
        # Anomaly 06: Settlements disguised as expenses ("paid back" + empty split type)
        is_settlement_disguise = False
        if "paid back" in raw_desc.lower() or "settled" in raw_desc.lower():
            if raw_split_type == "" or raw_split_type == "settlement":
                is_settlement_disguise = True
                
        if is_settlement_disguise:
            # We need to figure out who received the money. 
            # In descriptions like "Rohan paid back Aisha", we extract "Aisha".
            receiver_name = None
            if "paid back" in raw_desc.lower():
                parts = raw_desc.lower().split("paid back")
                if len(parts) > 1:
                    receiver_name = parts[1].strip().title()
                    
            if receiver_name:
                receiver_id = get_or_create_user(db, receiver_name, group_id, exp_date)
                
                # Save as Settlement
                settlement = Settlement(
                    group_id=group_id,
                    from_user_id=payer_id,
                    to_user_id=receiver_id,
                    amount=amount,
                    date=exp_date,
                    note=f"Imported: {raw_desc}"
                )
                db.add(settlement)
                
                # Save dummy expense
                dummy = Expense(
                    group_id=group_id,
                    description=raw_desc,
                    paid_by=payer_id,
                    amount=amount,
                    currency=currency,
                    amount_inr=convert_to_inr(amount, currency),
                    split_type="settlement",
                    date=exp_date,
                    is_settlement=True
                )
                db.add(dummy)
                
                report["imported"] += 1
                continue
                
        # Handle Missing Split Type
        if raw_split_type == "":
            raw_split_type = "equal"
            
        # --- STAGE 4: Handle Data Anomalies (Memberships, Overflows) ---
        
        # Determine who to split with
        # If no split details provided, assume all currently active members at that date
        split_details_dict = parse_split_details(raw_split_details)
        involved_user_names = list(split_details_dict.keys())
        
        # If equal split and no details, fetch active members
        if not involved_user_names and raw_split_type == "equal":
            # Fetch members active on this date
            active_memberships = db.query(GroupMember).filter(
                GroupMember.group_id == group_id,
                GroupMember.joined_at <= exp_date,
                (GroupMember.left_at == None) | (GroupMember.left_at > exp_date)
            ).all()
            involved_user_ids = [m.user_id for m in active_memberships]
        else:
            involved_user_ids = []
            for name in involved_user_names:
                # Anomaly 16: Check if user was active on this date
                u_id = get_or_create_user(db, name, group_id, exp_date)
                
                membership = db.query(GroupMember).filter(
                    GroupMember.group_id == group_id,
                    GroupMember.user_id == u_id
                ).first()
                
                if membership.left_at and membership.left_at <= exp_date:
                    # They left before this expense!
                    flag_msg = f"Row {row_num}: {name} was added to expense '{raw_desc}' but left on {membership.left_at}."
                    report["flagged"] += 1
                    report["anomalies"].append(flag_msg)
                    # We will flag it, but still import it (or we can skip. Let's flag and import).
                    
                involved_user_ids.append(u_id)
                
            # Replace names with IDs in split_details_dict for the calculator
            new_details_dict = {}
            for name, val in split_details_dict.items():
                u_id = db.query(User).filter(User.name == name).first().id
                new_details_dict[u_id] = val
            split_details_dict = new_details_dict

        # Calculate final INR amount
        amount_inr = convert_to_inr(amount, currency)
        
        # Perform Split Calculation
        splits = {}
        is_flagged = False
        flag_reason = ""
        
        try:
            if raw_split_type == "equal":
                splits = calculate_equal_split(amount_inr, involved_user_ids)
            elif raw_split_type == "percentage":
                # Anomaly 07: 110% triggers ValueError
                splits = calculate_percentage_split(amount_inr, split_details_dict)
            elif raw_split_type == "unequal":
                splits = calculate_unequal_split(split_details_dict)
            elif raw_split_type == "share":
                splits = calculate_share_split(amount_inr, split_details_dict)
            else:
                raise ValueError(f"Unknown split type: {raw_split_type}")
                
        except ValueError as e:
            is_flagged = True
            flag_reason = str(e)
            report["flagged"] += 1
            report["anomalies"].append(f"Row {row_num} Flagged: {flag_reason}")
            # If split fails completely, fallback to equal split among payer so money isn't lost
            splits = {payer_id: amount_inr}

        # --- STAGE 5: Save Output ---
        expense = Expense(
            group_id=group_id,
            description=raw_desc,
            paid_by=payer_id,
            amount=amount,
            currency=currency,
            amount_inr=amount_inr,
            split_type=raw_split_type,
            date=exp_date,
            is_settlement=False,
            is_flagged=is_flagged,
            flag_reason=flag_reason if is_flagged else None
        )
        db.add(expense)
        db.flush()
        
        for user_id, amount_owed in splits.items():
            split_record = ExpenseSplit(
                expense_id=expense.id,
                user_id=user_id,
                amount_owed=amount_owed
            )
            db.add(split_record)
            
        report["imported"] += 1

    # Commit all changes at the end
    db.commit()
    return report
