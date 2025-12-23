from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import SessionLocal
import re
import json
import decimal
import datetime
from typing import Dict, List, Any, Tuple, Optional
from uuid import UUID

class QueryExecutor:
    """Service for safely executing SQL queries against the database."""
    
    @staticmethod
    def validate_query(sql_query: str, dataset_id: str) -> Tuple[bool, str]:
        """
        Validate that the SQL query is safe and only accesses the specified dataset.
        
        Args:
            sql_query: The SQL query to validate
            dataset_id: The dataset ID that should be filtered
            
        Returns:
            Tuple of (is_valid, message_or_query)
        """
        if not sql_query:
            return False, "Empty query"
        
        # Check for dangerous operations
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
        for keyword in dangerous_keywords:
            if re.search(r'\b' + keyword + r'\b', sql_query.upper()):
                return False, f"Dangerous operation detected: {keyword}"
        
        # Ensure the query only accesses the loan_records table
        if "loan_records" not in sql_query.lower():
            return False, "Query must access the loan_records table"
        
        # Ensure the query filters by the specified dataset_id
        dataset_filter = f"dataset_id = '{dataset_id}'"
        if dataset_filter not in sql_query:
            # Add the dataset filter if it's missing
            where_pos = sql_query.upper().find("WHERE")
            if where_pos == -1:
                # No WHERE clause, add one
                sql_query = sql_query.rstrip(";") + f" WHERE {dataset_filter};"
            else:
                # Add to existing WHERE clause
                sql_query = sql_query.rstrip(";") + f" AND {dataset_filter};"
        
        return True, sql_query
    
    @staticmethod
    def execute_query(sql_query: str, dataset_id: str) -> Dict[str, Any]:
        """
        Execute a SQL query against the database.
        
        Args:
            sql_query: The SQL query to execute
            dataset_id: The dataset ID to filter by
            
        Returns:
            Dictionary with query results or error message
        """
        # Validate the query
        is_valid, result = QueryExecutor.validate_query(sql_query, dataset_id)
        if not is_valid:
            return {"error": result}
        
        # Use the validated query
        validated_query = result
        
        # Execute the query
        db = SessionLocal()
        try:
            # Execute the query
            result = db.execute(text(validated_query))
            
            # Get column names
            columns = [str(col) for col in result.keys()]
            
            # Fetch all rows
            rows = []
            for row in result:
                # Convert row to dictionary with JSON-serializable values
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    # Handle special types
                    if isinstance(value, UUID):
                        value = str(value)
                    elif isinstance(value, decimal.Decimal):
                        value = float(value)
                    elif isinstance(value, datetime.datetime):
                        value = value.isoformat()
                    elif isinstance(value, datetime.date):
                        value = value.isoformat()
                    elif isinstance(value, bytes):
                        value = value.decode('utf-8', errors='replace')
                    row_dict[column] = value
                rows.append(row_dict)
            
            return {
                "success": True,
                "columns": columns,
                "rows": rows,
                "query": validated_query
            }
        except SQLAlchemyError as e:
            return {
                "error": f"Database error: {str(e)}",
                "query": validated_query
            }
        except Exception as e:
            return {
                "error": f"Error executing query: {str(e)}",
                "query": validated_query
            }
        finally:
            db.close()
