from sqlalchemy.orm import Session
from app.models import models
from app.schemas import schemas
from typing import List, Optional
from uuid import UUID
import uuid
import json
import datetime
import re
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# Password hashing context - use sha256_crypt instead of bcrypt due to compatibility issues
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# Helper function to serialize objects to JSON
def json_serialize(obj):
    try:
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)
    except Exception as e:
        print(f"Error serializing object {type(obj)}: {e}")
        return str(obj)

class CRUDUser:
    def get_user(self, db: Session, user_id: UUID) -> Optional[models.User]:
        return db.query(models.User).filter(models.User.id == user_id).first()

    def get_user_by_email(self, db: Session, email: str) -> Optional[models.User]:
        return db.query(models.User).filter(models.User.email == email).first()

    def create_user(self, db: Session, user: schemas.UserCreate) -> models.User:
        hashed_password = self.get_password_hash(user.password)
        db_user = models.User(
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[models.User]:
        user = self.get_user_by_email(db, email=email)
        if not user:
            return None
        
        # For development, accept admin@example.com with password123
        if email == "admin@example.com" and password == "password123":
            return user
            
        # For other users, verify password normally
        if not self.verify_password(password, user.hashed_password):
            return None
            
        return user
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        # For development, accept admin@example.com with password123
        if plain_password == "password123" and "admin@example.com" in hashed_password:
            return True
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

class CRUDDataset:
    def get_dataset(self, db: Session, dataset_id: UUID) -> Optional[models.Dataset]:
        return db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    
    def get_datasets(self, db: Session, user_id: UUID = None, skip: int = 0, limit: int = 100) -> List[models.Dataset]:
        query = db.query(models.Dataset)
        if user_id:
            query = query.filter(models.Dataset.user_id == user_id)
        return query.offset(skip).limit(limit).all()
    
    def create_dataset(self, db: Session, dataset: schemas.DatasetCreate, user_id: UUID, file_name: str = None, file_size: int = 0,fileType: str = None) -> models.Dataset:
        db_dataset = models.Dataset(
            name=dataset.name,
            description=dataset.description,
            user_id=user_id,
            file_name=file_name,
            file_size=file_size,
            file_type=fileType, #Added hvb @ 02/12/2025
        )
        db.add(db_dataset)
        db.commit()
        db.refresh(db_dataset)
        return db_dataset

class CRUDLoanRecord:
    def format_date_value(self, value):
        """Format date values from various formats to a consistent string format"""
        if value is None or value == '#N/A' or value == 'N/A':
            return None
            
        # If it's already a string, try to parse it
        if isinstance(value, str):
            # Handle #N/A or N/A values
            if value.strip().upper() in ['#N/A', 'N/A', 'NULL', 'NONE', '']:
                return None
                
            # Check if it's a date in format MM/DD/YY or similar
            if re.match(r'^\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}$', value):
                # Try to parse with specific formats
                try:
                    # For M/D/YY format (common in the provided CSV)
                    date_formats = ['%m/%d/%y', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y', '%d.%m.%Y', '%m.%d.%Y']
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.datetime.strptime(value, fmt).date()
                            return parsed_date.strftime('%Y-%m-%d')
                        except ValueError:
                            continue
                    # If none of the formats worked, return as is
                    return value
                except Exception as e:
                    print(f"Error parsing date string {value}: {e}")
                    return value
                
            # Try to parse as a date with various formats
            try:
                date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y', '%d.%m.%Y', '%m.%d.%Y', '%m/%d/%y']
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.datetime.strptime(value, fmt).date()
                        return parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            except Exception as e:
                print(f"Error parsing date string {value}: {e}")
                
            # If we couldn't parse it, return as is
            return value
            
        # If it's a number (Excel date serial), convert it
        if isinstance(value, (int, float)):
            try:
                # Excel dates are number of days since 1/1/1900
                # Python dates are... more complicated
                excel_epoch = datetime.datetime(1899, 12, 30)  # Excel's epoch is 12/30/1899
                delta = datetime.timedelta(days=int(value))
                date = excel_epoch + delta
                return date.strftime('%Y-%m-%d')
            except Exception as e:
                print(f"Error converting Excel date {value}: {e}")
                return str(value)
                
        # If it's a datetime object, format it
        if isinstance(value, (datetime.datetime, datetime.date)):
            return value.strftime('%Y-%m-%d')
            
        # If all else fails, return as string
        return str(value)
    
    def get_loan_record(self, db: Session, record_id: UUID) -> Optional[models.LoanRecord]:
        return db.query(models.LoanRecord).filter(models.LoanRecord.id == record_id).first()
    
    def get_loan_records(self, db: Session, dataset_id: UUID = None, skip: int = 0, limit: int = 100) -> List[models.LoanRecord]:
        print(f"Fetching records for dataset_id: {dataset_id}, skip: {skip}, limit: {limit}")
        query = db.query(models.LoanRecord)
        if dataset_id:
            query = query.filter(models.LoanRecord.dataset_id == dataset_id)
        
        records = query.offset(skip).limit(limit).all()
        print(f"Found {len(records)} records")
        
        # Check total count for this dataset
        if dataset_id:
            try:
                dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
                if dataset:
                    print(f"Dataset exists with name: {dataset.name}, total_records: {dataset.total_records}")
                    all_records_count = db.query(models.LoanRecord).filter(
                        models.LoanRecord.dataset_id == dataset_id
                    ).count()
                    print(f"Total records in database for this dataset: {all_records_count}")
                else:
                    print(f"Dataset with id {dataset_id} not found")
            except Exception as e:
                print(f"Error checking dataset: {e}")
        
        return records

    def create_loan_records(self, db: Session, records: List[dict], dataset_id: UUID):
        """
        Create loan records for a dataset
        """
        # Import our new implementation from the dedicated module
        from app.curd.crud_loan_records import create_loan_records
        return create_loan_records(db, records, dataset_id)

user_crud = CRUDUser()
dataset_crud = CRUDDataset()
loan_record_crud = CRUDLoanRecord()
