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
    
    def create_dataset(self, db: Session, dataset: schemas.DatasetCreate, user_id: UUID, file_name: str = None, file_size: int = 0) -> models.Dataset:
        db_dataset = models.Dataset(
            name=dataset.name,
            description=dataset.description,
            user_id=user_id,
            file_name=file_name,
            file_size=file_size
        )
        db.add(db_dataset)
        db.commit()
        db.refresh(db_dataset)
        return db_dataset

class CRUDLoanRecord:
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
        """Create loan records from a list of dictionaries"""
        print(f"\n==== CREATING LOAN RECORDS ====\nCreating {len(records)} loan records for dataset {dataset_id}")
        
        # Ensure dataset_id is a UUID object
        if isinstance(dataset_id, str):
            dataset_id = UUID(dataset_id)
            
        print(f"Dataset ID type: {type(dataset_id)}")
        print(f"Dataset ID: {dataset_id}")
        
        # Check if dataset exists
        dataset_check = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
        print(f"Dataset exists in DB: {dataset_check is not None}")
        if dataset_check:
            print(f"Dataset name: {dataset_check.name}, ID: {dataset_check.id}")
        else:
            print("WARNING: Dataset does not exist in database!")
            return []
            
        # Create a list to hold all successfully created records
        db_records = []
        
        # Try creating a simple test record first
        try:
            print("Creating test record...")
            test_record = {
                'dataset_id': dataset_id,
                'agreement_no': 'TEST-RECORD',
                'principal_os_amt': 1000.0,
                'dpd_as_on_31st_jan_2025': 0,
                'classification': 'Standard',
                'additional_fields': '{}'
            }
            
            db_test = models.LoanRecord(**test_record)
            db.add(db_test)
            db.commit()
            db.refresh(db_test)
            print(f"Test record created successfully with ID: {db_test.id}")
            db_records.append(db_test)
        except Exception as e:
            db.rollback()
            print(f"Failed to create test record: {e}")
            import traceback
            traceback.print_exc()
        
        # Process records in small batches for better error handling
        batch_size = 10
        total_created = 0
        
        # Process records one by one for maximum reliability
        for i, record in enumerate(records):
            try:
                # Create a simplified record with essential fields
                simple_record = {
                    'dataset_id': dataset_id,
                    'agreement_no': f"LOAN-{i+1:04d}",  # Default value
                    'principal_os_amt': 0.0,
                    'dpd_as_on_31st_jan_2025': 0,
                    'classification': 'Standard'
                }
                
                # Store original fields
                additional_fields = {}
                
                # Process each field in the record
                for key, value in record.items():
                    if key is None or value is None:
                        continue
                        
                    # Store original value
                    additional_fields[key] = value
                    
                    key_lower = key.lower() if isinstance(key, str) else ""
                    
                    # Map agreement number
                    if key_lower in ['loan no.', 'loan no', 'agreement no', 'loan id', 'agreement number'] or 'loan' in key_lower or 'agreement' in key_lower:
                        if str(value).strip().upper() != 'Y':
                            simple_record['agreement_no'] = str(value)
                    
                    # Map principal outstanding
                    elif key_lower in ['principal o/s', 'principal outstanding', 'pos amount'] or 'principal' in key_lower:
                        try:
                            simple_record['principal_os_amt'] = float(value)
                        except (ValueError, TypeError):
                            pass
                    
                    # Map DPD
                    elif key_lower in ['dpd', 'days past due', 'overdue days'] or 'dpd' in key_lower:
                        try:
                            if isinstance(value, (int, float)):
                                simple_record['dpd_as_on_31st_jan_2025'] = int(float(value))
                            elif isinstance(value, str) and value.strip().replace('.', '', 1).isdigit():
                                simple_record['dpd_as_on_31st_jan_2025'] = int(float(value))
                            elif isinstance(value, str) and re.search(r'\d+', value):
                                match = re.search(r'\d+', value)
                                simple_record['dpd_as_on_31st_jan_2025'] = int(match.group())
                            elif isinstance(value, str) and ('w/off' in value.lower() or 'write-off' in value.lower()):
                                simple_record['dpd_as_on_31st_jan_2025'] = 999
                                simple_record['classification'] = 'Write-off'
                        except (ValueError, TypeError):
                            pass
                            
                    # Map classification
                    elif key_lower in ['classification', 'asset classification', 'loan classification']:
                        simple_record['classification'] = str(value)
                        
                    # Map other fields directly if they match column names
                    elif key_lower in ['product_type', 'customer_name', 'state', 'bureau_score', 
                                     'total_collection', 'loan_id', 'disbursement_date', 
                                     'pos_amount', 'disbursement_amount', 'status']:
                        simple_record[key_lower] = value
                
                # Convert additional_fields to JSON string
                try:
                    simple_record['additional_fields'] = json.dumps(additional_fields, default=json_serialize)
                except Exception as e:
                    print(f"Error converting additional_fields to JSON: {e}")
                    simple_record['additional_fields'] = '{}'
                
                # Create and save the record
                db_record = models.LoanRecord(**simple_record)
                db.add(db_record)
                db.commit()
                db.refresh(db_record)
                
                db_records.append(db_record)
                total_created += 1
                
                if (i+1) % 10 == 0 or (i+1) == len(records):
                    print(f"Created {total_created} records so far")
                    
            except Exception as e:
                db.rollback()
                print(f"Error creating record {i+1}: {e}")
        
        print(f"\n==== RECORD CREATION SUMMARY ====\nSuccessfully created {total_created} records out of {len(records)}")
        
        # Verify records were created
        verification_count = db.query(models.LoanRecord).filter(models.LoanRecord.dataset_id == dataset_id).count()
        print(f"Verification: {verification_count} records exist in database for this dataset")
        
        return db_records

user_crud = CRUDUser()
dataset_crud = CRUDDataset()
loan_record_crud = CRUDLoanRecord()
