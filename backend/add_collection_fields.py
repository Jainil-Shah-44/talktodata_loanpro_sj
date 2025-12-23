"""
Migration script to add collection fields to loan_records table
"""
from sqlalchemy import create_engine, text
import logging
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Direct database connection
DATABASE_URL = "postgresql://doc_user:doc_password@localhost:5432/talktodata_loanpro"
logger.info(f"Connecting to database: {DATABASE_URL.split('@')[-1]}")

def run_migration():
    """Add collection fields to loan_records table"""
    logger.info("Starting migration to add collection fields to loan_records table")
    
    # Use direct psycopg2 connection for simplicity
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'loan_records' 
            AND (column_name LIKE 'm%_collection' 
                OR column_name = 'total_collection'
                OR column_name = 'post_npa_collection'
                OR column_name = 'post_woff_collection')
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
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
            cursor.execute(f"ALTER TABLE loan_records ADD COLUMN IF NOT EXISTS {column_name} NUMERIC")
        
        conn.commit()
        logger.info("Migration completed successfully")
        return True
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logger.error(f"Migration failed: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_migration()
