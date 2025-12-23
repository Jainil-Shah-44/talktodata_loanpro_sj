"""
Script to update the loan_records table schema with new columns.
Run this script to add the new columns to the existing table.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# Get database connection string
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# Create engine
engine = create_engine(DATABASE_URL)

# SQL statements to add new columns
alter_statements = [
    "ALTER TABLE loan_records ADD COLUMN IF NOT EXISTS loan_id VARCHAR(50)",
    "ALTER TABLE loan_records ADD COLUMN IF NOT EXISTS disbursement_date VARCHAR(50)",
    "ALTER TABLE loan_records ADD COLUMN IF NOT EXISTS pos_amount FLOAT",
    "ALTER TABLE loan_records ADD COLUMN IF NOT EXISTS disbursement_amount FLOAT",
    "ALTER TABLE loan_records ADD COLUMN IF NOT EXISTS dpd INTEGER",
    "ALTER TABLE loan_records ADD COLUMN IF NOT EXISTS status VARCHAR(50)",
    "ALTER TABLE loan_records ADD COLUMN IF NOT EXISTS has_validation_errors BOOLEAN DEFAULT FALSE",
    "ALTER TABLE loan_records ADD COLUMN IF NOT EXISTS validation_error_types JSONB",
    "ALTER TABLE loan_records ADD COLUMN IF NOT EXISTS additional_fields JSONB"
]

def update_schema():
    """Execute the alter statements to update the schema."""
    with engine.connect() as connection:
        for statement in alter_statements:
            print(f"Executing: {statement}")
            connection.execute(text(statement))
        connection.commit()
    print("Schema update completed successfully.")

if __name__ == "__main__":
    update_schema()
