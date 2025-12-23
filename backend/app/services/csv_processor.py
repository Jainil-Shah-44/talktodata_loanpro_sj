import io
import pandas as pd
from typing import List, Dict, Any

def process_csv_file(file_content: bytes) -> List[Dict[Any, Any]]:
    """
    Process a CSV file and return a list of dictionaries representing the data.
    
    Args:
        file_content: The content of the CSV file as bytes
        
    Returns:
        A list of dictionaries where each dictionary represents a row in the CSV
    """
    try:
        # Convert bytes to string
        content_str = file_content.decode('utf-8')
        
        # Read CSV using pandas
        df = pd.read_csv(io.StringIO(content_str))
        
        # Clean column names (remove spaces, lowercase)
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
        
        # Handle missing values
        df = df.fillna('')
        
        # Convert to list of dictionaries
        records = df.to_dict('records')
        
        return records
    except Exception as e:
        # Log the error
        print(f"Error processing CSV file: {str(e)}")
        raise Exception(f"Failed to process CSV file: {str(e)}")
