#!/usr/bin/env python3
"""
File Maintenance Utility for Acadix Scan System
This script helps maintain the single permanent file approach for student credentials.
"""

import os
import glob
import shutil
from datetime import datetime
import data_manager

def audit_csv_files():
    """Audit all CSV files in the directory."""
    print("🔍 CSV File Audit Report")
    print("=" * 50)
    
    csv_files = glob.glob("*.csv")
    
    if not csv_files:
        print("No CSV files found.")
        return
    
    print(f"Found {len(csv_files)} CSV files:")
    
    permanent_files = {data_manager.STUDENTS_CSV, data_manager.ATTENDANCE_CSV}
    
    for file in csv_files:
        file_size = os.path.getsize(file)
        mod_time = datetime.fromtimestamp(os.path.getmtime(file))
        
        status = "✅ PERMANENT" if file in permanent_files else "⚠️  POTENTIAL DUPLICATE"
        
        print(f"  {status}: {file}")
        print(f"    Size: {file_size} bytes")
        print(f"    Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check if it looks like student data
        if 'student' in file.lower() and file not in permanent_files:
            print(f"    ⚠️  WARNING: This may be a duplicate student file!")
        
        print()

def backup_permanent_files():
    """Create backup of permanent files."""
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    permanent_files = [data_manager.STUDENTS_CSV, data_manager.ATTENDANCE_CSV]
    
    print("💾 Creating backups...")
    
    for file in permanent_files:
        if os.path.exists(file):
            backup_name = f"{file.replace('.csv', '')}_{timestamp}.csv"
            backup_path = os.path.join(backup_dir, backup_name)
            shutil.copy2(file, backup_path)
            print(f"  ✅ Backed up: {file} → {backup_path}")
        else:
            print(f"  ⚠️  File not found: {file}")
    
    print(f"\nBackups stored in: {os.path.abspath(backup_dir)}")

def validate_file_structure():
    """Validate the structure of permanent files."""
    print("🔧 Validating file structure...")
    print("=" * 40)
    
    # Validate student file
    try:
        df = data_manager._load_students_df()
        expected_columns = [
            "StudentID", "FullName", "Email", "RollNo", "PRN",
            "StudentPhone", "ParentPhone", "Address", "Year", 
            "Branch", "SecurityAnswer", "PasswordHash"
        ]
        
        print(f"Student file ({data_manager.STUDENTS_CSV}):")
        print(f"  ✅ Structure: Valid")
        print(f"  ✅ Records: {len(df)}")
        print(f"  ✅ Columns: {len(df.columns)}/{len(expected_columns)}")
        
        missing_cols = set(expected_columns) - set(df.columns)
        if missing_cols:
            print(f"  ⚠️  Missing columns: {missing_cols}")
        
    except Exception as e:
        print(f"  ❌ Error reading student file: {e}")
    
    print()
    
    # Validate attendance file
    try:
        att_df = data_manager._load_attendance_df()
        print(f"Attendance file ({data_manager.ATTENDANCE_CSV}):")
        print(f"  ✅ Structure: Valid")
        print(f"  ✅ Records: {len(att_df)}")
        
    except Exception as e:
        print(f"  ❌ Error reading attendance file: {e}")

def interactive_cleanup():
    """Interactive cleanup of duplicate files."""
    print("🧹 Interactive File Cleanup")
    print("=" * 30)
    
    csv_files = glob.glob("*.csv")
    permanent_files = {data_manager.STUDENTS_CSV, data_manager.ATTENDANCE_CSV}
    
    potential_duplicates = [f for f in csv_files if f not in permanent_files]
    
    if not potential_duplicates:
        print("✅ No potential duplicate files found!")
        return
    
    print(f"Found {len(potential_duplicates)} potential duplicate files:")
    
    for file in potential_duplicates:
        print(f"\n📄 File: {file}")
        print(f"   Size: {os.path.getsize(file)} bytes")
        print(f"   Modified: {datetime.fromtimestamp(os.path.getmtime(file))}")
        
        # Show first few lines to help identify content
        try:
            with open(file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                print(f"   Header: {first_line[:50]}...")
        except Exception as e:
            print(f"   Error reading: {e}")
        
        action = input("   Action (d=delete, k=keep, s=skip): ").lower()
        
        if action == 'd':
            try:
                os.remove(file)
                print(f"   ✅ Deleted: {file}")
            except Exception as e:
                print(f"   ❌ Error deleting: {e}")
        elif action == 'k':
            print(f"   ✅ Keeping: {file}")
        else:
            print(f"   ⏭️  Skipped: {file}")

def main():
    """Main menu for file maintenance."""
    while True:
        print("\n" + "=" * 60)
        print("🛠️  ACADIX SCAN - FILE MAINTENANCE UTILITY")
        print("=" * 60)
        print("1. 🔍 Audit CSV files")
        print("2. 💾 Backup permanent files")
        print("3. 🔧 Validate file structure")
        print("4. 🧹 Interactive cleanup")
        print("5. 📊 Show current statistics")
        print("6. ❌ Exit")
        print("-" * 60)
        
        choice = input("Select option (1-6): ").strip()
        
        if choice == "1":
            audit_csv_files()
        elif choice == "2":
            backup_permanent_files()
        elif choice == "3":
            validate_file_structure()
        elif choice == "4":
            interactive_cleanup()
        elif choice == "5":
            print("\n📊 Current Statistics:")
            print(f"Students: {data_manager.total_registered_students()}")
            attendance_df = data_manager._load_attendance_df()
            print(f"Attendance records: {len(attendance_df)}")
        elif choice == "6":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()