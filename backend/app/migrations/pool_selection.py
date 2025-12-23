"""
Migration script to add pool selection tables
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def run_migration():
    """Create pool selection tables"""
    try:
        # Get database URL from environment
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")

        # Connect to the database
        engine = create_engine(database_url)
        
        # Create pool_selections table
        with engine.connect() as connection:
            logger.info("Creating pool_selections table...")
            connection.execute(text("""
            CREATE TABLE IF NOT EXISTS pool_selections (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                total_amount NUMERIC NOT NULL,
                account_count INTEGER NOT NULL,
                criteria JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
            """))
            
            logger.info("Creating pool_selection_records table...")
            connection.execute(text("""
            CREATE TABLE IF NOT EXISTS pool_selection_records (
                id SERIAL PRIMARY KEY,
                pool_selection_id INTEGER NOT NULL REFERENCES pool_selections(id) ON DELETE CASCADE,
                loan_record_id UUID NOT NULL REFERENCES loan_records(id) ON DELETE CASCADE,
                principal_os_amt NUMERIC NOT NULL
            )
            """))
            
            # Add collection_12m column to loan_records if it doesn't exist
            logger.info("Adding collection_12m column to loan_records if it doesn't exist...")
            connection.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'loan_records'
                    AND column_name = 'collection_12m'
                ) THEN
                    ALTER TABLE loan_records ADD COLUMN collection_12m NUMERIC;
                    
                    -- Populate collection_12m from m1-m12 columns
                    UPDATE loan_records
                    SET collection_12m = COALESCE(m1_collection, 0) + 
                                        COALESCE(m2_collection, 0) + 
                                        COALESCE(m3_collection, 0) + 
                                        COALESCE(m4_collection, 0) + 
                                        COALESCE(m5_collection, 0) + 
                                        COALESCE(m6_collection, 0) + 
                                        COALESCE(m7_collection, 0) + 
                                        COALESCE(m8_collection, 0) + 
                                        COALESCE(m9_collection, 0) + 
                                        COALESCE(m10_collection, 0) + 
                                        COALESCE(m11_collection, 0) + 
                                        COALESCE(m12_collection, 0);
                END IF;
            END
            $$;
            """))
            
            # Add account_number column to loan_records if it doesn't exist
            logger.info("Adding account_number column to loan_records if it doesn't exist...")
            connection.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'loan_records'
                    AND column_name = 'account_number'
                ) THEN
                    ALTER TABLE loan_records ADD COLUMN account_number VARCHAR(255);
                    
                    -- Copy loan_id or agreement_no to account_number as a fallback
                    UPDATE loan_records
                    SET account_number = COALESCE(loan_id, agreement_no);
                END IF;
            END
            $$;
            """))
            
            connection.commit()
            logger.info("Pool selection tables created successfully")
            
    except Exception as e:
        logger.error(f"Error creating pool selection tables: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()
