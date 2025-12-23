#!/usr/bin/env python
"""
Script to create a test user in the database with proper password hashing
"""
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import uuid
from datetime import datetime

from app.core.database import engine, SessionLocal
from app.models.models import User, Base

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Password hashing context
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_test_user():
    db = SessionLocal()
    try:
        # Check if test user already exists
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if test_user:
            print(f"Test user already exists with ID: {test_user.id}")
            return
        
        # Create a new test user with properly hashed password
        hashed_password = get_password_hash("password123")
        new_user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password=hashed_password,
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            created_at=datetime.utcnow()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"Created test user with ID: {new_user.id}")
        print(f"Email: test@example.com")
        print(f"Password: password123")
    except Exception as e:
        print(f"Error creating test user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
