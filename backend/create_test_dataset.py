#!/usr/bin/env python
"""
Script to create a test dataset in the database
"""
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.core.database import engine, SessionLocal
from app.models.models import Dataset, User, Base

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

def create_test_dataset():
    db = SessionLocal()
    try:
        # Get the test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            print("Test user not found. Please run create_test_user.py first.")
            return
        
        # Check if test dataset already exists
        test_dataset = db.query(Dataset).filter(Dataset.user_id == test_user.id).first()
        if test_dataset:
            print(f"Test dataset already exists with ID: {test_dataset.id}")
            print(f"Name: {test_dataset.name}")
            print(f"Total records: {test_dataset.total_records}")
            return
        
        # Create a new test dataset
        new_dataset = Dataset(
            id=uuid.uuid4(),
            user_id=test_user.id,
            name="Loan Portfolio Q1 2025",
            description="First quarter loan data for testing",
            file_name="loan_portfolio_q1_2025.csv",
            file_size=2500000,
            total_records=1250,
            upload_date=datetime.utcnow(),
            status="validated"
        )
        
        db.add(new_dataset)
        db.commit()
        db.refresh(new_dataset)
        
        print(f"Created test dataset with ID: {new_dataset.id}")
        print(f"Name: {new_dataset.name}")
        print(f"Total records: {new_dataset.total_records}")
    except Exception as e:
        print(f"Error creating test dataset: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_dataset()
