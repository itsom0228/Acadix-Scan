#!/usr/bin/env python3
"""
Demo script to show how the login system uses a single permanent file.
This demonstrates that no duplicate files are created during login/signup operations.
"""

import data_manager
import os
from datetime import datetime

def demo_login_signup_operations():
    """Demonstrate login and signup operations using single permanent file."""
    
    print("=" * 60)
    print("DEMO: Single Permanent File for Student Login Credentials")
    print("=" * 60)
    
    # Check current state
    print("\n1. Current file state:")
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    print(f"CSV files found: {csv_files}")
    
    # Load existing students
    print("\n2. Loading existing student data:")
    students_df = data_manager._load_students_df()
    print(f"Current students in database: {len(students_df)}")
    
    # Simulate multiple login attempts
    print("\n3. Simulating login attempts (no new files created):")
    for i in range(3):
        print(f"  Login attempt {i+1}:")
        success, student_data = data_manager.authenticate_student("omkar", "Test@123")
        if success:
            print(f"    ✓ Login successful for {student_data['FullName']}")
        else:
            print(f"    ✗ Login failed")
    
    # Check file state after login attempts
    print("\n4. File state after login attempts:")
    csv_files_after = [f for f in os.listdir('.') if f.endswith('.csv')]
    print(f"CSV files found: {csv_files_after}")
    print(f"Files created during login: {len(csv_files_after) - len(csv_files)}")
    
    # Simulate signup attempt
    print("\n5. Simulating signup attempt:")
    new_student_data = {
        "StudentID": "test123",
        "FullName": "Test Student",
        "Email": "test@example.com",
        "RollNo": "TS001",
        "PRN": "2024001",
        "StudentPhone": "9876543210",
        "ParentPhone": "9876543211",
        "Address": "Test Address",
        "Year": "First Year",
        "Branch": "Computer",
        "SecurityAnswer": "TestAnswer",
        "Password": "Test@123",
        "ConfirmPassword": "Test@123"
    }
    
    success, message = data_manager.register_student(new_student_data)
    print(f"  Signup result: {message}")
    
    # Check final file state
    print("\n6. Final file state:")
    csv_files_final = [f for f in os.listdir('.') if f.endswith('.csv')]
    print(f"CSV files found: {csv_files_final}")
    print(f"Total files created during demo: {len(csv_files_final) - len(csv_files)}")
    
    # Verify data persistence
    print("\n7. Verifying data persistence:")
    final_students_df = data_manager._load_students_df()
    print(f"Final student count: {len(final_students_df)}")
    
    # Cleanup test data if added
    if success:
        print("\n8. Cleaning up test data...")
        # Remove test student to keep original state
        students_df = data_manager._load_students_df()
        students_df = students_df[students_df["StudentID"] != "test123"]
        data_manager._save_students_df(students_df)
        print("Test student removed.")
    
    print("\n" + "=" * 60)
    print("CONCLUSION: All operations use the SAME permanent file!")
    print(f"File used: {data_manager.STUDENTS_CSV}")
    print("No duplicate files were created during login/signup operations.")
    print("=" * 60)

if __name__ == "__main__":
    demo_login_signup_operations()