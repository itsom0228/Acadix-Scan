import os
import hashlib
from datetime import datetime
from typing import Dict, Optional, Tuple

import pandas as pd


# Permanent file paths - these should NEVER change to avoid duplicate files
STUDENTS_CSV = "student_details.csv"  # Single permanent student credentials file
ATTENDANCE_CSV = "attendance.csv"     # Single permanent attendance file
INTERNAL_MARKS_CSV = "internal_marks.csv"  # Single permanent internal marks file
ALERTS_CSV = "alerts.csv"  # Low attendance alerts

# File lock to prevent concurrent modifications (Unix only)
# import fcntl  # Not needed for Windows


def _ensure_files_exist() -> None:
    """Ensure the permanent CSV files exist. Only creates if they don't exist."""
    if not os.path.exists(STUDENTS_CSV):
        print(f"Creating new student database: {STUDENTS_CSV}")
        pd.DataFrame(
            columns=[
                "StudentID",
                "FullName",
                "Email",
                "RollNo",
                "PRN",
                "StudentPhone",
                "ParentPhone",
                "Address",
                "Year",
                "Branch",
                "Semester",
                "SecurityAnswer",
                "PasswordHash",
            ]
        ).to_csv(STUDENTS_CSV, index=False)
    else:
        print(f"Using existing student database: {STUDENTS_CSV}")

    if not os.path.exists(ATTENDANCE_CSV):
        print(f"Creating new attendance database: {ATTENDANCE_CSV}")
        pd.DataFrame(columns=["Date", "PRN", "RollNo", "Name", "Time", "Status"]).to_csv(
            ATTENDANCE_CSV, index=False
        )
    else:
        print(f"Using existing attendance database: {ATTENDANCE_CSV}")

    if not os.path.exists(INTERNAL_MARKS_CSV):
        print(f"Creating new internal marks database: {INTERNAL_MARKS_CSV}")
        pd.DataFrame(
            columns=[
                "PRN",
                "Name",
                "Year",
                "Branch",
                "Semester",
                "CA1",
                "CA2",
                "MidSem",
                "SemesterExam",
                "Obtained",
                "MaxTotal",
                "Total",
                "UpdatedAt",
            ]
        ).to_csv(INTERNAL_MARKS_CSV, index=False)
    else:
        print(f"Using existing internal marks database: {INTERNAL_MARKS_CSV}")

    if not os.path.exists(ALERTS_CSV):
        print(f"Creating new alerts database: {ALERTS_CSV}")
        pd.DataFrame(
            columns=[
                "AlertID",
                "PRN",
                "StudentPhone",
                "ParentPhone",
                "Target",
                "Message",
                "DateTime",
                "Sender",
            ]
        ).to_csv(ALERTS_CSV, index=False)
    else:
        print(f"Using existing alerts database: {ALERTS_CSV}")


def check_for_duplicate_files() -> None:
    """Check for and warn about potential duplicate CSV files."""
    import glob
    
    # Look for any CSV files that might be duplicates
    csv_files = glob.glob("*.csv")
    student_files = [f for f in csv_files if 'student' in f.lower()]
    
    if len(student_files) > 1:
        print("WARNING: Multiple student CSV files detected:")
        for file in student_files:
            print(f"  - {file}")
        print(f"Only {STUDENTS_CSV} should be used for student credentials!")
    
    return len(student_files) > 1


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _load_students_df() -> pd.DataFrame:
    """Load student data from the permanent CSV file."""
    _ensure_files_exist()
    check_for_duplicate_files()  # Check for potential duplicates
    
    try:
        df = pd.read_csv(STUDENTS_CSV, dtype=str).fillna("")
        if "Semester" not in df.columns:
            df["Semester"] = ""
        print(f"Loaded {len(df)} students from {STUDENTS_CSV}")
        return df
    except Exception as e:
        print(f"Error loading {STUDENTS_CSV}: {e}")
        print("Creating new DataFrame with proper structure")
        return pd.DataFrame(
            columns=[
                "StudentID",
                "FullName",
                "Email",
                "RollNo",
                "PRN",
                "StudentPhone",
                "ParentPhone",
                "Address",
                "Year",
                "Branch",
                "Semester",
                "SecurityAnswer",
                "PasswordHash",
            ]
        )


def _save_students_df(df: pd.DataFrame) -> None:
    df.to_csv(STUDENTS_CSV, index=False)


def _load_attendance_df() -> pd.DataFrame:
    _ensure_files_exist()
    try:
        return pd.read_csv(ATTENDANCE_CSV, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame(columns=["Date", "PRN", "RollNo", "Name", "Time", "Status"]).fillna("")


def _save_attendance_df(df: pd.DataFrame) -> None:
    df.to_csv(ATTENDANCE_CSV, index=False)


def _load_internal_marks_df() -> pd.DataFrame:
    _ensure_files_exist()
    try:
        df = pd.read_csv(INTERNAL_MARKS_CSV, dtype=str).fillna("")
        for col in ["SemesterExam", "Obtained", "MaxTotal"]:
            if col not in df.columns:
                df[col] = ""
        return df
    except Exception:
        return pd.DataFrame(
            columns=[
                "PRN",
                "Name",
                "Year",
                "Branch",
                "Semester",
                "CA1",
                "CA2",
                "MidSem",
                "SemesterExam",
                "Obtained",
                "MaxTotal",
                "Total",
                "UpdatedAt",
            ]
        ).fillna("")


def _save_internal_marks_df(df: pd.DataFrame) -> None:
    df.to_csv(INTERNAL_MARKS_CSV, index=False)


def validate_signup_fields(data: Dict[str, str]) -> Tuple[bool, str]:
    required_fields = [
        "StudentID",
        "FullName",
        "Email",
        "RollNo",
        "PRN",
        "StudentPhone",
        "ParentPhone",
        "Address",
        "Year",
        "Branch",
        "Semester",
        "SecurityAnswer",
        "Password",
        "ConfirmPassword",
    ]
    for key in required_fields:
        if not data.get(key, "").strip():
            return False, f"{key} cannot be empty."

    if "@" not in data["Email"]:
        return False, "Email must contain '@'."

    if data["Password"] != data["ConfirmPassword"]:
        return False, "Password and Confirm Password must match."

    pwd = data["Password"]
    has_upper = any(c.isupper() for c in pwd)
    has_lower = any(c.islower() for c in pwd)
    has_digit = any(c.isdigit() for c in pwd)
    has_symbol = any(c in "@#!$%^&*()-_=+[]{};:'\",.<>/?|`~" for c in pwd)
    if not (has_upper and has_lower and has_digit and has_symbol):
        return (
            False,
            "Password must contain uppercase, lowercase, number, and special symbol.",
        )

    # Unique StudentID
    students = _load_students_df()
    if not students[students["StudentID"] == data["StudentID"]].empty:
        return False, "Student ID already exists."

    return True, "OK"


def register_student(data: Dict[str, str]) -> Tuple[bool, str]:
    is_valid, msg = validate_signup_fields(data)
    if not is_valid:
        return False, msg

    students = _load_students_df()
    new_row = {
        "StudentID": data["StudentID"].strip(),
        "FullName": data["FullName"].strip(),
        "Email": data["Email"].strip(),
        "RollNo": data["RollNo"].strip(),
        "PRN": data["PRN"].strip(),
        "StudentPhone": data["StudentPhone"].strip(),
        "ParentPhone": data["ParentPhone"].strip(),
        "Address": data["Address"].strip(),
        "Year": data["Year"].strip(),
        "Branch": data["Branch"].strip(),
        "Semester": data.get("Semester", "").strip(),
        "SecurityAnswer": data["SecurityAnswer"].strip(),
        "PasswordHash": _hash_password(data["Password"]),
    }
    students = pd.concat([students, pd.DataFrame([new_row])], ignore_index=True)
    _save_students_df(students)
    return True, "Student registered successfully."


def authenticate_student(student_id: str, password: str) -> Tuple[bool, Optional[Dict[str, str]]]:
    students = _load_students_df()
    student = students[students["StudentID"] == str(student_id)].copy()
    if student.empty:
        return False, None
    row = student.iloc[0].to_dict()
    if row.get("PasswordHash") == _hash_password(password):
        return True, row
    return False, None


def forgot_password_flow(student_id: str, answer: str) -> Tuple[bool, Optional[Dict[str, str]]]:
    students = _load_students_df()
    student = students[students["StudentID"] == str(student_id)].copy()
    if student.empty:
        return False, None
    row = student.iloc[0].to_dict()
    if row.get("SecurityAnswer", "").strip().lower() == answer.strip().lower():
        return True, row
    return False, None


def get_student_by_id(student_id: str) -> Optional[Dict[str, str]]:
    students = _load_students_df()
    student = students[students["StudentID"] == str(student_id)].copy()
    if student.empty:
        return None
    return student.iloc[0].to_dict()


def get_student_by_name(name: str) -> Optional[Dict[str, str]]:
    students = _load_students_df()
    student = students[students["FullName"] == str(name)].copy()
    if student.empty:
        return None
    return student.iloc[0].to_dict()


def update_student_profile(student_id: str, updates: Dict[str, str]) -> Tuple[bool, str]:
    students = _load_students_df()
    idx = students.index[students["StudentID"] == str(student_id)]
    if len(idx) == 0:
        return False, "Student not found."

    i = idx[0]
    # Allow editing of most signup fields except immutable StudentID
    editable_fields = {
        "FullName",
        "Email",
        "RollNo",
        "PRN",
        "StudentPhone",
        "ParentPhone",
        "Address",
        "Year",
        "Branch",
        "Password",
        "SecurityAnswer",
        "Semester",
    }
    for key, value in updates.items():
        if key not in editable_fields:
            continue
        if key == "Password":
            students.at[i, "PasswordHash"] = _hash_password(value)
        elif key == "SecurityAnswer":
            students.at[i, "SecurityAnswer"] = value
        else:
            students.at[i, key] = value

    _save_students_df(students)
    return True, "Profile updated."


def total_registered_students() -> int:
    return len(_load_students_df().index)


def list_all_students() -> pd.DataFrame:
    return _load_students_df().copy()


# ---------------- Internal Marks APIs ----------------
def upsert_internal_marks(rows: pd.DataFrame) -> None:
    """Upsert internal marks records by unique key (PRN, Year, Branch, Semester)."""
    base = _load_internal_marks_df()
    if rows.empty:
        return

    # Normalize dtypes to string and compute Total if needed
    def _to_int_safe(val: str) -> int:
        try:
            return max(0, int(float(str(val).strip() or "0")))
        except Exception:
            return 0

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for _, r in rows.iterrows():
        prn = str(r.get("PRN", "")).strip()
        year = str(r.get("Year", "")).strip()
        branch = str(r.get("Branch", "")).strip()
        sem = str(r.get("Semester", "")).strip()
        name = str(r.get("Name", "")).strip()
        ca1 = _to_int_safe(r.get("CA1", "0"))
        ca2 = _to_int_safe(r.get("CA2", "0"))
        mid = _to_int_safe(r.get("MidSem", "0"))
        sem_exam = _to_int_safe(r.get("SemesterExam", "0"))
        max_total = _to_int_safe(r.get("MaxTotal", "100"))
        if max_total <= 0:
            max_total = 100

        # Clamp to max marks
        ca1 = min(ca1, 10)
        ca2 = min(ca2, 10)
        mid = min(mid, 20)
        obtained = ca1 + ca2 + mid + sem_exam
        if obtained > max_total:
            obtained = max_total
        total = obtained

        mask = (
            (base["PRN"] == prn)
            & (base["Year"] == year)
            & (base["Branch"] == branch)
            & (base["Semester"] == sem)
        )
        new_row = {
            "PRN": prn,
            "Name": name,
            "Year": year,
            "Branch": branch,
            "Semester": sem,
            "CA1": str(ca1),
            "CA2": str(ca2),
            "MidSem": str(mid),
            "SemesterExam": str(sem_exam),
            "Obtained": str(obtained),
            "MaxTotal": str(max_total),
            "Total": str(total),
            "UpdatedAt": now,
        }
        if mask.any():
            idx = base[mask].index[0]
            for k, v in new_row.items():
                base.at[idx, k] = v
        else:
            base = pd.concat([base, pd.DataFrame([new_row])], ignore_index=True)

    _save_internal_marks_df(base)


def get_internal_marks(year: str, branch: str, semester: str) -> pd.DataFrame:
    """Get internal marks for a specific branch and semester.
    
    If year is empty, returns marks for all years matching the branch and semester.
    """
    df = _load_internal_marks_df()
    if df.empty:
        return df
    if year:
        filtered = df[
            (df["Year"] == str(year)) & (df["Branch"] == str(branch)) & (df["Semester"] == str(semester))
        ].copy()
    else:
        # If year is empty, get all years for this branch and semester
        filtered = df[
            (df["Branch"] == str(branch)) & (df["Semester"] == str(semester))
        ].copy()
    return filtered


def get_student_internal_marks(prn: str) -> pd.DataFrame:
    df = _load_internal_marks_df()
    if df.empty:
        return df
    return df[df["PRN"] == str(prn)].copy()


def mark_attendance_if_absent(prn: str, roll_no: str, name: str, status: str = "Present") -> Tuple[bool, str]:
    # A single CSV with a Date column is used. "Sheet/tab" semantics are represented by filtering by Date.
    today = datetime.now().strftime("%d-%m-%Y")
    now_time = datetime.now().strftime("%H:%M:%S")
    df = _load_attendance_df()

    already = df[(df["Date"] == today) & (df["PRN"] == str(prn))]
    if not already.empty:
        return False, "Attendance already marked for today."

    new_row = {
        "Date": today,
        "PRN": str(prn),
        "RollNo": str(roll_no),
        "Name": str(name),
        "Time": now_time,
        "Status": status,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    _save_attendance_df(df)
    return True, "Attendance marked successfully."


def attendance_summary_for_date(date_str: str) -> Dict[str, int]:
    df = _load_attendance_df()
    students = _load_students_df()
    total = len(students.index)
    present = len(df[df["Date"] == date_str].index)
    absent = max(total - present, 0)
    return {"total": total, "present": present, "absent": absent}


def student_attendance_summary_for_date(date_str: str, student_prn: str) -> Dict[str, int]:
    """Get attendance summary for a specific student on a specific date"""
    df = _load_attendance_df()
    student_record = df[(df["Date"] == date_str) & (df["PRN"] == str(student_prn))]
    
    if not student_record.empty:
        status = student_record.iloc[0]["Status"]
        if status.lower() == "present":
            return {"present": 1, "absent": 0, "total": 1}
        else:
            return {"present": 0, "absent": 1, "total": 1}
    else:
        # No record means absent
        return {"present": 0, "absent": 1, "total": 1}


def attendance_in_range(days: int, student_prn: str = None) -> pd.DataFrame:
    # Returns records within the last `days` days including today
    # If student_prn is provided, filter for that student only
    if days <= 0:
        df = _load_attendance_df().copy()
    else:
        df = _load_attendance_df().copy()
        if df.empty:
            return df
        # Parse dates with known format
        df["_dt"] = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")
        cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(days=days - 1)
        df = df[df["_dt"] >= cutoff].drop(columns=["_dt"], errors="ignore")
    
    # Filter by student PRN if provided
    if student_prn:
        df = df[df["PRN"] == str(student_prn)].copy()
    
    return df


def editable_student_fields() -> Tuple[str, ...]:
    return (
        "StudentID",
        "FullName",
        "Email",
        "RollNo",
        "PRN",
        "StudentPhone",
        "ParentPhone",
        "Address",
        "Year",
        "Branch",
        "SecurityAnswer",
    )


def save_students_dataframe(updated_df: pd.DataFrame) -> None:
    # Persist the admin-edited DataFrame back to CSV, preserving column order
    cols = list(editable_student_fields()) + ["PasswordHash"]
    for col in cols:
        if col not in updated_df.columns:
            updated_df[col] = ""
    updated_df = updated_df[cols]
    updated_df.to_csv(STUDENTS_CSV, index=False)


def cleanup_duplicate_files() -> None:
    """Remove any accidental duplicate CSV files, keeping only the permanent ones."""
    import glob
    import os
    
    # Get all CSV files
    csv_files = glob.glob("*.csv")
    
    # Files to keep (permanent files)
    permanent_files = {STUDENTS_CSV, ATTENDANCE_CSV}
    
    duplicates_found = False
    for file in csv_files:
        if file not in permanent_files:
            # Check if it looks like a student or attendance duplicate
            if ('student' in file.lower() or 'attendance' in file.lower()):
                print(f"Found potential duplicate file: {file}")
                response = input(f"Do you want to remove {file}? (y/N): ").lower()
                if response == 'y':
                    try:
                        os.remove(file)
                        print(f"Removed duplicate file: {file}")
                        duplicates_found = True
                    except Exception as e:
                        print(f"Error removing {file}: {e}")
    
    if not duplicates_found:
        print("No duplicate files found. Using permanent files only.")
    
    return duplicates_found


def low_attendance_report(threshold_percent: int = 75, days: int = 30) -> pd.DataFrame:
    """Generate a report of students with attendance below the threshold percentage.
    
    Args:
        threshold_percent: Minimum attendance percentage required (default 75%)
        days: Number of days to consider for attendance calculation (default 30 days)
        
    Returns:
        DataFrame with columns: PRN, Name, Present, Total, Percentage
    """
    # Get all students
    students_df = _load_students_df()
    if students_df.empty:
        return pd.DataFrame()
    
    # Get attendance records for the specified period
    attendance_df = _load_attendance_df()
    if attendance_df.empty:
        # If no attendance records, all students have 0% attendance
        result = []
        for _, student in students_df.iterrows():
            result.append({
                "PRN": student["PRN"],
                "Name": student["FullName"],
                "Present": 0,
                "Total": days,
                "Percentage": 0.0,
                "StudentPhone": student["StudentPhone"],
                "ParentPhone": student["ParentPhone"],
                "Year": student["Year"],
                "Branch": student["Branch"],
                "Semester": student.get("Semester", ""),
            })
        return pd.DataFrame(result)
    
    # Calculate attendance for each student
    result = []
    for _, student in students_df.iterrows():
        prn = student["PRN"]
        student_attendance = attendance_in_range(days, prn)
        
        # Count present days
        present_count = len(student_attendance[student_attendance["Status"].str.lower() == "present"])
        
        # Calculate percentage
        percentage = (present_count / days) * 100 if days > 0 else 0
        
        # Add to result if below threshold
        if percentage < threshold_percent:
            result.append({
                "PRN": prn,
                "Name": student["FullName"],
                "Present": present_count,
                "Total": days,
                "Percentage": round(percentage, 2),
                "StudentPhone": student["StudentPhone"],
                "ParentPhone": student["ParentPhone"],
                "Year": student["Year"],
                "Branch": student["Branch"],
                "Semester": student.get("Semester", ""),
            })
    
    return pd.DataFrame(result)


def get_alerts_for_student(prn: str) -> pd.DataFrame:
    """Get all alerts for a specific student by PRN.
    
    Args:
        prn: Student PRN
        
    Returns:
        DataFrame containing alerts for the student
    """
    _ensure_files_exist()
    
    try:
        alerts_df = pd.read_csv(ALERTS_CSV, dtype=str).fillna("")
        # Filter alerts for the specific student
        student_alerts = alerts_df[alerts_df["PRN"] == str(prn)].copy()
        return student_alerts
    except Exception as e:
        print(f"Error loading alerts for student {prn}: {e}")
        return pd.DataFrame()


def send_alert(prn: str, target: str, message: str, sender: str = "system") -> bool:
    """Send an alert to a student or parent.
    
    Args:
        prn: Student PRN
        target: 'student' or 'parent'
        message: Alert message
        sender: Who sent the alert (default 'system')
        
    Returns:
        True if alert was recorded successfully
    """
    _ensure_files_exist()
    
    # Get student details
    student = None
    students_df = _load_students_df()
    student_row = students_df[students_df["PRN"] == str(prn)]
    if not student_row.empty:
        student = student_row.iloc[0].to_dict()
    
    if not student:
        error_message = f"Cannot send alert: Student with PRN {prn} not found"
        print(error_message)
        return False, error_message
    
    # Load alerts database
    try:
        alerts_df = pd.read_csv(ALERTS_CSV, dtype=str).fillna("")
    except Exception:
        alerts_df = pd.DataFrame(
            columns=[
                "AlertID",
                "PRN",
                "StudentPhone",
                "ParentPhone",
                "Target",
                "Message",
                "DateTime",
                "Sender",
            ]
        )
    
    # Generate alert ID
    import uuid
    alert_id = str(uuid.uuid4())
    
    # Create new alert record
    new_alert = {
        "AlertID": alert_id,
        "PRN": prn,
        "StudentPhone": student["StudentPhone"],
        "ParentPhone": student["ParentPhone"],
        "Target": target,
        "Message": message,
        "DateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Sender": sender,
    }
    
    # Add to alerts database
    alerts_df = pd.concat([alerts_df, pd.DataFrame([new_alert])], ignore_index=True)
    alerts_df.to_csv(ALERTS_CSV, index=False)
    
    success_message = f"Alert sent to {target} for student {student['FullName']} (PRN: {prn})"
    print(success_message)
    return True, success_message


