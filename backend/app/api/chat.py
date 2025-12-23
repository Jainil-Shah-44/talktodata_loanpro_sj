from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from uuid import UUID
import json
import re
import logging
from app.core.database import get_db
from app.core.auth.dependencies import get_current_user
from app.models import models
from app.services.llm_service import LLMService
from app.services.schema_mapper import SchemaMapper
from app.services.query_executor import QueryExecutor
from typing import Dict, Any, Optional, List

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()
llm_service = LLMService(provider="huggingface")  # Default to Hugging Face
schema_mapper = SchemaMapper()


async def get_direct_amount_response(query, dataset_id, db, query_type):
    """
    Get direct amount responses from the database without using LLM.
    
    Args:
        query: The user's query
        dataset_id: Dataset ID
        db: Database session
        query_type: 'max', 'min', or 'avg'
        
    Returns:
        Direct response string with actual database values
    """
    from sqlalchemy import text
    
    # Determine which columns to query based on the user's query
    amount_columns = {
        'sanction_amt': 'sanctioned amount',
        'total_amt_disb': 'disbursed amount',
        'principal_os_amt': 'principal outstanding',
        'carrying_value_as_on_date': 'carrying value'
    }
    
    # Determine specific column to focus on if mentioned in the query
    target_column = None
    
    # Check for specific terms in the query
    if 'sanction' in query.lower():
        target_column = 'sanction_amt'
    elif 'disbursed' in query.lower() or 'disburse' in query.lower():
        target_column = 'total_amt_disb'
    elif 'outstanding' in query.lower() or 'principal' in query.lower():
        target_column = 'principal_os_amt'
    elif 'carrying' in query.lower() or 'value' in query.lower():
        target_column = 'carrying_value_as_on_date'
    # For generic 'loan amount' with no specifics, prefer disbursed amount
    elif 'loan' in query.lower() and 'amount' in query.lower():
        target_column = 'total_amt_disb'
    
    # If no specific column is targeted, query all columns
    results = {}
    columns_to_query = [target_column] if target_column else amount_columns.keys()
    
    for col in columns_to_query:
        try:
            # Build SQL based on query type
            if query_type == 'max':
                sql = text(f"SELECT MAX({col}) FROM loan_records WHERE dataset_id = :dataset_id AND {col} IS NOT NULL")
            elif query_type == 'min':
                sql = text(f"SELECT MIN({col}) FROM loan_records WHERE dataset_id = :dataset_id AND {col} IS NOT NULL AND {col} > 0")
            else:  # avg
                sql = text(f"SELECT AVG({col}) FROM loan_records WHERE dataset_id = :dataset_id AND {col} IS NOT NULL")
                
            result = db.execute(sql, {"dataset_id": dataset_id}).fetchone()
            
            if result and result[0] is not None:
                results[col] = float(result[0])
                print(f"Found {query_type} value for {col}: {results[col]}")
        except Exception as e:
            print(f"Error querying {query_type} value for {col}: {e}")
    
    # If we found any values
    if results:
        # Choose the appropriate column based on query type
        if query_type == 'max':
            selected_col = max(results, key=results.get)
            value = results[selected_col]
        elif query_type == 'min':
            selected_col = min(results, key=results.get)
            value = results[selected_col]
        else:  # avg
            # Prefer principal_os_amt for averages
            if 'principal_os_amt' in results:
                selected_col = 'principal_os_amt'
            else:
                selected_col = next(iter(results))
            value = results[selected_col]
        
        # Get the friendly name for the column
        friendly_name = amount_columns.get(selected_col, 'loan amount')
        
        # Generate the appropriate response based on query type
        if query_type == 'max':
            return f"The maximum {friendly_name} in the dataset is ₹{value:,.2f}."
        elif query_type == 'min':
            return f"The minimum {friendly_name} in the dataset is ₹{value:,.2f}."
        else:  # avg
            return f"The average {friendly_name} in the dataset is ₹{value:,.2f}."
    
    # If we couldn't find any values, return None so the LLM can handle it
    return None

# Prompt templates
CHAT_QUERY_TEMPLATE = """
You are a friendly, helpful assistant named Talk2Data that helps loan officers analyze their loan portfolio data.

Your personality:
- You speak in simple, conversational language - like you're chatting with a friend
- You avoid technical jargon and explain things in plain English
- You're concise and get straight to the point
- You focus on insights, not technical details

The database contains loan records with this structure:
{schema}

Quick dataset facts:
- {stats[total_records]} total loans
- ₹{stats[total_pos]:,.2f} total principal outstanding
- {stats[avg_dpd]:.2f} days average DPD
- ₹{stats[total_collection]:,.2f} total collection amount

The user is asking: "{user_query}"

CRITICAL INSTRUCTIONS TO PREVENT HALLUCINATIONS:
1. Respond with ONLY ONE short, friendly paragraph in conversational language
2. DO NOT explain how you got the answer or mention data processing/SQL
3. DO NOT number your response or use bullet points
4. DO NOT mention "here's what I found" or similar phrases - just give the answer directly
5. If you need SQL to answer, include it at the end in ```sql tags (this will be removed and only logged)
6. EXTREMELY IMPORTANT: Your response must ONLY mention data that will actually appear in the query results
7. NEVER make up data or mention states/values that aren't in your SQL query results
8. If you're listing multiple items (like states), your SQL query MUST return ALL those items
9. Always use ORDER BY in your SQL queries when ranking or comparing items
10. If unsure about data, write a query that returns exactly what you need - don't guess or hallucinate

SPECIAL INSTRUCTIONS FOR MAX/MIN/AVG QUERIES:
- For maximum values, use: SELECT MAX(column_name) as max_value FROM loan_records WHERE dataset_id = '{dataset_id}'
- For minimum values, use: SELECT MIN(column_name) as min_value FROM loan_records WHERE dataset_id = '{dataset_id}'
- For average values, use: SELECT AVG(column_name) as avg_value FROM loan_records WHERE dataset_id = '{dataset_id}'
- Always check for NULL values: WHERE column_name IS NOT NULL AND dataset_id = '{dataset_id}'

Remember to include dataset_id = '{dataset_id}' in any SQL queries.

DEBUG INFO: Any technical details or explanations should only appear in SQL comments using -- prefix, which will only be visible in logs, not to the user.
"""

@router.post("/{dataset_id}/chat")
async def chat_with_data(
    dataset_id: str,
    query: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Chat with the loan data for a specific dataset."""
    try:
        # Validate dataset exists and belongs to user
        dataset_uuid = UUID(dataset_id)
        dataset = db.query(models.Dataset).filter(
            models.Dataset.id == dataset_uuid,
            models.Dataset.user_id == current_user.id
        ).first()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Get schema information with state code mappings
        schema = schema_mapper.get_schema_description()
        
        # Get dataset statistics
        dataset_stats = schema_mapper.get_dataset_statistics(str(dataset_uuid))
        
        # Special handling for direct amount queries that don't need LLM
        direct_query_result = None
        
        # Check if this is a query about maximum/minimum/average amounts that we can handle directly
        if any(term in query.lower() for term in ['maximum', 'max', 'highest']) and \
           any(term in query.lower() for term in ['loan', 'amount', 'sanction', 'disbursed', 'outstanding', 'principal']):
            
            logger.warning(f"DIRECT HANDLING: Bypassing LLM for maximum amount query: {query}")
            direct_query_result = await get_direct_amount_response(query, str(dataset_uuid), db, 'max')
            
        elif any(term in query.lower() for term in ['minimum', 'min', 'lowest', 'smallest']) and \
             any(term in query.lower() for term in ['loan', 'amount', 'sanction', 'disbursed', 'outstanding', 'principal']):
            
            logger.warning(f"DIRECT HANDLING: Bypassing LLM for minimum amount query: {query}")
            direct_query_result = await get_direct_amount_response(query, str(dataset_uuid), db, 'min')
            
        elif any(term in query.lower() for term in ['average', 'avg', 'mean']) and \
             any(term in query.lower() for term in ['loan', 'amount', 'sanction', 'disbursed', 'outstanding', 'principal']):
            
            logger.warning(f"DIRECT HANDLING: Bypassing LLM for average amount query: {query}")
            direct_query_result = await get_direct_amount_response(query, str(dataset_uuid), db, 'avg')
        
        # Use the direct result or generate a response using LLM
        if direct_query_result:
            llm_response = direct_query_result
        else:
            # Generate response using LLM
            prompt = CHAT_QUERY_TEMPLATE.format(
                schema=schema,
                stats=dataset_stats,
                user_query=query,
                dataset_id=dataset_id
            )
            llm_response = await llm_service.generate_response(prompt)
        
        # Extract SQL query if present
        sql_query = None
        query_results = None
        sql_match = re.search(r"```sql\n(.*?)\n```", llm_response, re.DOTALL)
        if sql_match:
            sql_query = sql_match.group(1)
            
            # Log the SQL query instead of including it in the response
            print(f"SQL Query for dataset {dataset_id}: {sql_query}")
            logger.info(f"SQL Query for dataset {dataset_id}: {sql_query}")
            
            # Check for common errors in the SQL query
            if ('state' in query.lower() and any(term in query.lower() for term in ['loan amount', 'amount', 'total', 'sum', 'balance'])):
                # Get our valid amount columns that actually exist in the database
                valid_amount_columns = ['principal_os_amt', 'total_amt_disb', 'sanction_amt', 'carrying_value_as_on_date']
                
                # Completely rewrite the query rather than trying to fix the LLM's query
                # This avoids complex syntax errors
                if 'principal' in query.lower() or 'outstanding' in query.lower():
                    amount_column = 'principal_os_amt'
                    amount_desc = 'principal outstanding'
                elif 'disbursed' in query.lower() or 'disburse' in query.lower():
                    amount_column = 'total_amt_disb'
                    amount_desc = 'disbursed amount'
                elif 'sanction' in query.lower() or 'approved' in query.lower():
                    amount_column = 'sanction_amt'
                    amount_desc = 'sanctioned amount'
                else:
                    # Default to total_amt_disb for generic loan amount queries
                    amount_column = 'total_amt_disb'
                    amount_desc = 'loan amount'
                
                # Create a correct SQL query from scratch
                new_sql = f"SELECT state, SUM({amount_column}) as loan_amount FROM loan_records "
                new_sql += f"WHERE dataset_id = '{dataset_id}' AND state IS NOT NULL "
                new_sql += f"GROUP BY state ORDER BY loan_amount DESC"
                
                logger.warning(f"Replaced problematic SQL query with a correctly formatted one for {amount_desc}.")
                logger.warning(f"Original: {sql_query}")
                logger.warning(f"New: {new_sql}")
                
                # Use our hand-crafted query instead of the LLM's query
                sql_query = new_sql
            
            # Remove the SQL query from the response
            llm_response = re.sub(r"```sql\n.*?\n```", "", llm_response, flags=re.DOTALL)
            
            # Execute the SQL query if it's present
            if sql_query:
                query_results = QueryExecutor.execute_query(sql_query, str(dataset_uuid))
                
                # If query execution was successful, enhance the response with the results
                if "success" in query_results and query_results["success"]:
                    # Log query execution details
                    logger.info(f"Query execution successful: {len(query_results['rows'])} rows returned")
                    
                    # Log the actual query results for debugging
                    result_preview = "\n"
                    for i, row in enumerate(query_results['rows'][:5]):
                        result_preview += f"Row {i+1}: {row}\n"
                    logger.info(f"Query result preview: {result_preview}")
                    
                    # Validation for different types of queries
                    
                    # 1. State validation - Check for hallucinated state data
                    if 'state' in query_results['columns']:
                        # Get all states that actually exist in the results
                        actual_states = set()
                        for row in query_results['rows']:
                            state_code = row.get('state')
                            if state_code:
                                actual_states.add(state_code)
                        
                        # Get state codes and full names for easy lookup
                        state_codes = set(schema_mapper.state_mapping.keys())
                        state_full_names = set(schema_mapper.state_mapping.values())
                        
                        # Count mentions of states in the response
                        mentioned_states = []
                        for state_code in state_codes:
                            if state_code.lower() in llm_response.lower():
                                mentioned_states.append(state_code)
                        
                        for state_name in state_full_names:
                            if state_name.lower() in llm_response.lower():
                                # Find the code for this state name
                                code = next((code for code, name in schema_mapper.state_mapping.items() 
                                            if name.lower() == state_name.lower()), None)
                                if code and code not in mentioned_states:
                                    mentioned_states.append(code)
                        
                        # Check if response mentions states not in the results
                        hallucinated_states = []
                        for state in mentioned_states:
                            if state not in actual_states:
                                hallucinated_states.append(state)
                        
                        # If hallucination detected or this is a direct query about states, override the response with factual data
                        if hallucinated_states or len(mentioned_states) > len(actual_states) or \
                           ('state' in query.lower() and any(term in query.lower() for term in ['loan amount', 'sum', 'total'])):
                            
                            if hallucinated_states:
                                logger.warning(f"Detected AI hallucination - response mentioned states not in results: {hallucinated_states}")
                            else:
                                logger.warning(f"Handling direct state amount query: {query}")
                            
                            # Format actual state data
                            state_data = []
                            for row in query_results['rows']:
                                state_code = row.get('state')
                                if state_code:
                                    # Get full state name
                                    state_name = schema_mapper.state_mapping.get(state_code, state_code)
                                    # If mapping exists, use it, otherwise use the original code
                                    if state_name is None:
                                        state_name = state_code
                                    
                                    # Look for amount columns
                                    amount_value = None
                                    amount_col = None
                                    
                                    # Try to find the most relevant amount column
                                    amount_column_priorities = [
                                        'loan_amount', 'amount', 'sum', 'total', 'principal', 'sanction'
                                    ]
                                    
                                    for priority_term in amount_column_priorities:
                                        for col in query_results['columns']:
                                            if priority_term in col.lower():
                                                amount_col = col
                                                amount_value = row.get(col)
                                                break
                                        if amount_col:
                                            break
                                    
                                    # If we still don't have an amount column, take any numeric column
                                    if amount_value is None:
                                        for col in query_results['columns']:
                                            if col != 'state' and row.get(col) is not None and isinstance(row.get(col), (int, float)) or \
                                               (isinstance(row.get(col), str) and row.get(col).replace('.', '').isdigit()):
                                                amount_col = col
                                                try:
                                                    amount_value = float(row.get(col))
                                                except (ValueError, TypeError):
                                                    continue
                                                break
                                    
                                    # Format the data if we have an amount
                                    if amount_value is not None:
                                        try:
                                            amount_float = float(amount_value)
                                            state_data.append(f"{state_name}: ₹{amount_float:,.2f}")
                                        except (ValueError, TypeError):
                                            state_data.append(f"{state_name}: {amount_value}")
                            
                            if state_data:
                                # Override with factual response
                                llm_response = f"The data shows the following amounts by state: {', '.join(state_data)}"
                            else:
                                # Check if we have states but all amounts are NULL
                                has_states_with_null_amounts = False
                                if not state_data and len(actual_states) > 0:
                                    # Log the raw data for debugging
                                    logger.warning(f"Query returned states but no valid amounts: {query_results['rows']}")
                                    
                                    # Check if any of the columns seem to be amount-related but are NULL
                                    amount_like_columns = []
                                    for col in query_results['columns']:
                                        if any(term in col.lower() for term in ['amount', 'sum', 'total', 'principal', 'sanction']):
                                            amount_like_columns.append(col)
                                    
                                    if amount_like_columns:
                                        has_states_with_null_amounts = True
                                        logger.warning(f"Found amount-like columns with NULL values: {amount_like_columns}")
                                
                                # Generic override if we can't format properly
                                if has_states_with_null_amounts:
                                    # Try to find any other numeric data we can show
                                    state_with_other_data = []
                                    for row in query_results['rows']:
                                        state_code = row.get('state')
                                        if state_code:
                                            state_name = schema_mapper.state_mapping.get(state_code, state_code)
                                            if state_name is None:
                                                state_name = state_code
                                            
                                            # Try to find any non-NULL numeric column
                                            for col in query_results['columns']:
                                                if col != 'state' and col not in amount_like_columns and row.get(col) is not None:
                                                    try:
                                                        value = float(row.get(col))
                                                        state_with_other_data.append(f"{state_name}: {col}={value:,.2f}")
                                                        break
                                                    except (ValueError, TypeError):
                                                        continue
                                    
                                    if state_with_other_data:
                                        # We found some other numeric data to show
                                        llm_response = f"No loan amount data available, but found other information by state: {', '.join(state_with_other_data)}"
                                    else:
                                        # We have states but all amount values are NULL
                                        state_list = []
                                        for code in actual_states:
                                            name = schema_mapper.state_mapping.get(code, code)
                                            if name is not None:
                                                state_list.append(name)
                                            else:
                                                state_list.append(code)
                                        
                                        llm_response = f"The database contains the following states, but all loan amount values are NULL: {', '.join(state_list)}"
                                else:
                                    # General case - no state data found
                                    state_list = []
                                    for code in actual_states:
                                        name = schema_mapper.state_mapping.get(code, code)
                                        if name is not None:
                                            state_list.append(name)
                                        else:
                                            state_list.append(code)
                                    
                                    if state_list:
                                        llm_response = f"The data contains these states but no amount information was found: {', '.join(state_list)}"
                                    else:
                                        llm_response = "No state data was found in the query results."
                        
                        logger.warning(f"Response overridden with factual data.")
                    
                    # 2. Max/Min/Average validation - Check if the query is about max/min/avg values
                    max_amount_keywords = ['maximum', 'max', 'highest', 'largest', 'biggest']
                    min_amount_keywords = ['minimum', 'min', 'lowest', 'smallest']
                    avg_amount_keywords = ['average', 'avg', 'mean']
                    
                    # Check if query is about loan amounts
                    amount_keywords = ['loan amount', 'principal', 'balance', 'outstanding', 'disbursement', 'amount']
                    
                    is_max_query = any(keyword in query.lower() for keyword in max_amount_keywords) and any(amount in query.lower() for amount in amount_keywords)
                    is_min_query = any(keyword in query.lower() for keyword in min_amount_keywords) and any(amount in query.lower() for amount in amount_keywords)
                    is_avg_query = any(keyword in query.lower() for keyword in avg_amount_keywords) and any(amount in query.lower() for amount in amount_keywords)
                    
                    # Special case for "What's the maximum loan amount?" type queries
                    if ('maximum' in query.lower() and 'loan' in query.lower() and 'amount' in query.lower()) or \
                       ('max' in query.lower() and 'loan' in query.lower() and 'amount' in query.lower()) or \
                       ('show' in query.lower() and 'max' in query.lower() and 'loan' in query.lower()):
                        is_max_query = True
                        logger.info(f"Detected direct maximum loan amount query: {query}")
                        
                    # Add extra logging to trace the execution path
                    logger.warning(f"Query '{query}' classified as max_query: {is_max_query}, min_query: {is_min_query}, avg_query: {is_avg_query}")
                    
                    if 'minimum' in query.lower() and 'loan' in query.lower() and 'amount' in query.lower():
                        is_min_query = True
                        logger.info(f"Detected direct minimum loan amount query: {query}")
                        
                    if 'average' in query.lower() and 'loan' in query.lower() and 'amount' in query.lower():
                        is_avg_query = True
                        logger.info(f"Detected direct average loan amount query: {query}")
                    
                    # If it's a max/min/avg query, validate the response against the actual data
                    if is_max_query or is_min_query or is_avg_query:
                        logger.info(f"Processing {'max' if is_max_query else 'min' if is_min_query else 'avg'} query: {query}")
                        
                        # For max loan amount queries, let's directly execute the correct query
                        if is_max_query and ('loan amount' in query.lower() or ('loan' in query.lower() and 'amount' in query.lower())):
                            # Execute a direct SQL query to get the max loan amount
                            from sqlalchemy import text
                            
                            # Use columns that actually exist in the database
                            amount_columns = ['sanction_amt', 'total_amt_disb', 'principal_os_amt', 'carrying_value_as_on_date']
                            
                            max_values = {}
                            for col in amount_columns:
                                try:
                                    # Execute SQL query directly
                                    sql = text(f"SELECT MAX({col}) FROM loan_records WHERE dataset_id = :dataset_id AND {col} IS NOT NULL")
                                    result = db.execute(sql, {"dataset_id": str(dataset_uuid)}).fetchone()
                                    
                                    if result and result[0] is not None:
                                        max_values[col] = float(result[0])
                                        logger.info(f"Found max value for {col}: {max_values[col]}")
                                except Exception as e:
                                    logger.error(f"Error querying max value for {col}: {e}")
                            
                            # If we found any valid max values
                            if max_values:
                                # Find the highest value among all columns
                                max_column = max(max_values, key=max_values.get)
                                max_value = max_values[max_column]
                                
                                # Get a friendly column name for the response
                                friendly_column_names = {
                                    'sanction_amt': 'sanctioned loan amount',
                                    'total_amt_disb': 'disbursed loan amount',
                                    'principal_os_amt': 'principal outstanding amount',
                                    'carrying_value_as_on_date': 'carrying value'
                                }
                                
                                friendly_name = friendly_column_names.get(max_column, 'loan amount')
                                
                                # Override the response with the correct value
                                llm_response = f"The maximum {friendly_name} in the dataset is ₹{max_value:,.2f}."
                                logger.warning(f"FIXED DATA: Directly calculated max {max_column} as ₹{max_value} - If you still see 1,00,00,000.00 check the frontend!")
                                
                                # Explicitly prevent any overriding of this response
                                query_results = None  # This prevents the general validation logic from changing our response
                        
                        # For min loan amount queries, use the same approach as max queries
                        elif is_min_query and ('loan amount' in query.lower() or ('loan' in query.lower() and 'amount' in query.lower())):
                            # Execute a direct SQL query to get the min loan amount
                            from sqlalchemy import text
                            
                            # Use columns that actually exist in the database
                            amount_columns = ['sanction_amt', 'total_amt_disb', 'principal_os_amt', 'carrying_value_as_on_date']
                            
                            min_values = {}
                            for col in amount_columns:
                                try:
                                    # Execute SQL query directly
                                    sql = text(f"SELECT MIN({col}) FROM loan_records WHERE dataset_id = :dataset_id AND {col} IS NOT NULL AND {col} > 0")
                                    result = db.execute(sql, {"dataset_id": str(dataset_uuid)}).fetchone()
                                    
                                    if result and result[0] is not None:
                                        min_values[col] = float(result[0])
                                        logger.info(f"Found min value for {col}: {min_values[col]}")
                                except Exception as e:
                                    logger.error(f"Error querying min value for {col}: {e}")
                            
                            # If we found any valid min values
                            if min_values:
                                # Find the lowest value among all columns
                                min_column = min(min_values, key=min_values.get)
                                min_value = min_values[min_column]
                                
                                # Get a friendly column name for the response
                                friendly_column_names = {
                                    'sanction_amt': 'sanctioned loan amount',
                                    'total_amt_disb': 'disbursed loan amount',
                                    'principal_os_amt': 'principal outstanding amount',
                                    'carrying_value_as_on_date': 'carrying value'
                                }
                                
                                friendly_name = friendly_column_names.get(min_column, 'loan amount')
                                
                                # Override the response with the correct value
                                llm_response = f"The minimum {friendly_name} in the dataset is ₹{min_value:,.2f}."
                                logger.warning(f"Directly calculated min {min_column} as ₹{min_value}")
                        
                        # For avg loan amount queries, use the same approach
                        elif is_avg_query and ('loan amount' in query.lower() or ('loan' in query.lower() and 'amount' in query.lower())):
                            # Execute a direct SQL query to get the avg loan amount
                            from sqlalchemy import text
                            
                            # Use columns that actually exist in the database
                            amount_columns = ['sanction_amt', 'total_amt_disb', 'principal_os_amt', 'carrying_value_as_on_date']
                            
                            avg_values = {}
                            for col in amount_columns:
                                try:
                                    # Execute SQL query directly
                                    sql = text(f"SELECT AVG({col}) FROM loan_records WHERE dataset_id = :dataset_id AND {col} IS NOT NULL")
                                    result = db.execute(sql, {"dataset_id": str(dataset_uuid)}).fetchone()
                                    
                                    if result and result[0] is not None:
                                        avg_values[col] = float(result[0])
                                        logger.info(f"Found avg value for {col}: {avg_values[col]}")
                                except Exception as e:
                                    logger.error(f"Error querying avg value for {col}: {e}")
                            
                            # If we found any valid avg values
                            if avg_values:
                                # Use the principal_os_amt as the default if available, otherwise use the first available
                                if 'principal_os_amt' in avg_values:
                                    avg_column = 'principal_os_amt'
                                    avg_value = avg_values[avg_column]
                                else:
                                    avg_column = next(iter(avg_values))
                                    avg_value = avg_values[avg_column]
                                
                                # Get a friendly column name for the response
                                friendly_column_names = {
                                    'sanction_amt': 'sanctioned loan amount',
                                    'total_amt_disb': 'disbursed loan amount',
                                    'principal_os_amt': 'principal outstanding amount',
                                    'carrying_value_as_on_date': 'carrying value'
                                }
                                
                                friendly_name = friendly_column_names.get(avg_column, 'loan amount')
                                
                                # Override the response with the correct value
                                llm_response = f"The average {friendly_name} in the dataset is ₹{avg_value:,.2f}."
                                logger.warning(f"Directly calculated avg {avg_column} as ₹{avg_value}")
                        
                        # For other queries, validate the response against the query results
                        else:
                            # Extract amount mentioned in response
                            amount_pattern = r'₹\s*([\d,]+\.?\d*)'  # Match Indian Rupee symbol followed by a number
                            amount_matches = re.findall(amount_pattern, llm_response)
                            
                            # If an amount is mentioned in the response
                            if amount_matches:
                                mentioned_amount = amount_matches[0].replace(',', '')
                                logger.info(f"Response mentions amount: ₹{mentioned_amount}")
                                
                                # Find the actual max/min/avg amount in the query results
                                amount_columns = [col for col in query_results['columns'] if any(term in col.lower() for term in ['amount', 'principal', 'balance', 'outstanding', 'pos', 'loan'])]
                                
                                if amount_columns and query_results['rows']:
                                    # Get the first amount column
                                    amount_col = amount_columns[0]
                                    logger.info(f"Using column {amount_col} for validation")
                                    
                                    # Calculate the actual value
                                    values = [float(row[amount_col]) for row in query_results['rows'] if row[amount_col] is not None]
                                    
                                    if values:
                                        logger.info(f"Found {len(values)} non-null values to analyze")
                    
                    # Format the results for display - but don't mention SQL or queries
                    result_text = "\n\n"
                    
                    # Get the number of rows
                    num_rows = len(query_results["rows"])
                    
                    # If there are too many rows, limit the display
                    max_rows_to_display = 10
                    rows_to_display = query_results["rows"][:max_rows_to_display]
                    
                    # Format as a table if there are multiple rows
                    if num_rows > 0:
                        # Get column widths
                        col_widths = {}
                        for col in query_results["columns"]:
                            col_widths[col] = len(str(col))
                            for row in rows_to_display:
                                col_widths[col] = max(col_widths[col], len(str(row.get(col, ""))))
                        # Create header
                        header = " | ".join(f"{col:{col_widths[col]}}" for col in query_results["columns"])
                        separator = "-+-".join("-" * col_widths[col] for col in query_results["columns"])
                        result_text += f"{header}\n{separator}\n"
                        # Create rows
                        for row in rows_to_display:
                            row_text = " | ".join(f"{str(row.get(col, '')):{col_widths[col]}}" for col in query_results["columns"])
                            result_text += f"{row_text}\n"
                        # Add note if there are more rows
                        if num_rows > max_rows_to_display:
                            result_text += f"\n... and {num_rows - max_rows_to_display} more rows"
                    # If the query is about collection rates by product type, always use factual summary
                    if (
                        "collection rate" in query.lower() and
                        "product type" in query.lower() and
                        query_results and
                        "product_type" in query_results["columns"]
                    ):
                        # Use the factual summary
                        llm_response = generate_collection_rate_summary(query_results["rows"])
                    else:
                        llm_response += result_text
        
        return {
            "type": "success",
            "query": query,
            "response": llm_response,
            "query_results": query_results
        }
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return {
            "type": "error",
            "message": f"An error occurred: {str(e)}"
        }

@router.post("/settings")
async def update_llm_settings(
    settings: Dict[str, Any] = Body(...),
    current_user: models.User = Depends(get_current_user)
):
    """Update LLM provider settings."""
    try:
        # Check if user is admin
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Only administrators can change LLM settings")
        
        provider = settings.get("provider")
        api_key = settings.get("api_key")
        model = settings.get("model")
        
        if not provider:
            raise HTTPException(status_code=400, detail="Provider is required")
        
        # Update LLM service settings
        llm_service.change_provider(provider, api_key, model)
        
        return {
            "type": "success",
            "message": f"LLM provider changed to {provider}",
            "current_settings": {
                "provider": llm_service.provider,
                "model": llm_service.model
            }
        }
        
    except Exception as e:
        print(f"Error updating LLM settings: {e}")
        return {
            "type": "error",
            "message": f"An error occurred: {str(e)}"
        }

def generate_collection_rate_summary(results):
    if not results:
        return "No collection data found for any product type."

    lines = []
    for row in results:
        product = row["product_type"]
        principal = row["total_principal"]
        collected = row["total_collected"]
        if principal > 0:
            rate = (collected / principal) * 100
        else:
            rate = 0
        lines.append(
            f"{product}: ₹{collected:,.2f} collected out of ₹{principal:,.2f} principal ({rate:.1f}%)"
        )
    return "The collection rates by product type for the given dataset are as follows:\n" + "\n".join(lines)
