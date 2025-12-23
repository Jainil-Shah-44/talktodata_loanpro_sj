"""
Test script to verify data upload and display process
"""
import os
import sys
import pandas as pd
import json
from sqlalchemy.orm import Session
from uuid import UUID

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the necessary modules
from backend.app.database.session import SessionLocal
from backend.app.models import models
from backend.app.curd import crud

def test_data_upload():
    """Test data upload and display process"""
    # Create a sample DataFrame with the exact field names from the Excel file
    data = {
        'Loan No.': ['3019CD0247432', '3019CD0247433', '3019CD0247434'],
        'DPD': [90, 120, 60],
        'Classification': ['W/off', 'NPA', 'Standard'],
        'Principal O/S': [10000, 20000, 30000],
        'Disbursement Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'Sanction Date': ['2023-12-01', '2023-12-02', '2023-12-03'],
        'Date of NPA': ['2024-03-01', '2024-03-02', '2024-03-03'],
        'Date of Write-off': ['2024-04-01', '2024-04-02', '2024-04-03'],
        'Product Type': ['Consumer Durable', 'Personal Loan', 'Home Loan'],
        'Property Value': [20000, 40000, 60000],
        'LTV': [50, 60, 70],
        'State': ['AP', 'TN', 'KA'],
        'No. of EMI Paid': [12, 18, 24],
        'Balance Tenor': [12, 6, 0],
        'Legal Status': ['None', 'Arbitration', 'NI Act'],
        'Post NPA Collection': [1000, 2000, 3000],
        '6M Collection': [500, 1000, 1500],
        '12M Collection': [1000, 2000, 3000]
    }
    
    df = pd.DataFrame(data)
    
    # Convert DataFrame to records
    records = df.to_dict('records')
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Create a test dataset
        dataset = crud.dataset.create_dataset(
            db,
            models.DatasetCreate(name="Test Dataset", description="Test Dataset"),
            user_id=UUID("00000000-0000-0000-0000-000000000000"),
            file_name="test.xlsx",
            file_size=1000
        )
        
        # Create loan records
        loan_records = crud.loan_record.create_loan_records(db, records, dataset.id)
        
        # Get the loan records
        db_records = db.query(models.LoanRecord).filter(
            models.LoanRecord.dataset_id == dataset.id
        ).all()
        
        # Print the loan records
        print(f"Created {len(db_records)} loan records")
        
        # Check if the additional_fields JSON contains the original field names
        for record in db_records:
            additional_fields = json.loads(record.additional_fields)
            print(f"Record {record.id}:")
            print(f"  agreement_no: {record.agreement_no}")
            print(f"  classification: {record.classification}")
            print(f"  principal_os_amt: {record.principal_os_amt}")
            print(f"  product_type: {record.product_type}")
            print(f"  state: {record.state}")
            print(f"  dpd_as_on_31st_jan_2025: {record.dpd_as_on_31st_jan_2025}")
            print(f"  Additional fields: {list(additional_fields.keys())[:5]}...")
            
            # Check if the key fields are in the additional_fields
            key_fields = ['Loan No.', 'DPD', 'Classification', 'Principal O/S', 'Product Type', 'State']
            for field in key_fields:
                if field in additional_fields:
                    print(f"  Found key field {field}: {additional_fields[field]}")
                else:
                    print(f"  Missing key field: {field}")
            
            # Only print the first record
            break
        
    finally:
        # Clean up
        db.query(models.LoanRecord).filter(
            models.LoanRecord.dataset_id == dataset.id
        ).delete()
        db.query(models.Dataset).filter(
            models.Dataset.id == dataset.id
        ).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    test_data_upload()
