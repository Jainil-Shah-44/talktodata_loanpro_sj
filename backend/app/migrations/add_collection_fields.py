"""
Migration script to add collection fields to loan_records table
"""
from sqlalchemy import create_engine, Column, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import MetaData
from sqlalchemy.dialects.postgresql import JSONB
import logging
import os
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Now we can import from app
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create engine
try:
    DATABASE_URL = settings.DATABASE_URL
except Exception as e:
    # Fallback to direct connection if settings import fails
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/talktodata_loanpro"
    logger.warning(f"Using fallback database URL due to error: {str(e)}")

logger.info(f"Connecting to database: {DATABASE_URL.split('@')[-1]}")
engine = create_engine(DATABASE_URL)

# Create metadata
metadata = MetaData()
metadata.bind = engine

def run_migration():
    """Add collection fields to loan_records table"""
    logger.info("Starting migration to add collection fields to loan_records table")
    
    conn = engine.connect()
    transaction = conn.begin()
    
    try:
        # Check if columns already exist
        result = conn.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'loan_records' 
            AND column_name LIKE 'm%_collection'
        """)
        
        existing_columns = [row[0] for row in result]
        logger.info(f"Existing collection columns: {existing_columns}")
        
        # Add columns that don't exist
        columns_to_add = []
        for i in range(1, 13):
            column_name = f"m{i}_collection"
            if column_name not in existing_columns:
                columns_to_add.append(column_name)
        
        # Also check for total_collection, post_npa_collection, post_woff_collection
        for column_name in ["total_collection", "post_npa_collection", "post_woff_collection"]:
            if column_name not in existing_columns:
                columns_to_add.append(column_name)
        
        # Add columns
        for column_name in columns_to_add:
            logger.info(f"Adding column {column_name} to loan_records table")
            conn.execute(f"""
                ALTER TABLE loan_records 
                ADD COLUMN IF NOT EXISTS {column_name} NUMERIC
            """)
        
        transaction.commit()
        logger.info("Migration completed successfully")
        return True
    except Exception as e:
        transaction.rollback()
        logger.error(f"Migration failed: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
