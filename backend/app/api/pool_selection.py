from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc
import json
from typing import Dict, Any, List, Optional
import logging

from app.core.database import get_db
from app.core.auth.dependencies import get_current_user
from app.models import models
from app.models.pool_selection import PoolSelection, PoolSelectionRecord
from app.services.query_executor import QueryExecutor

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check():
    """Simple health check endpoint to verify the router is accessible"""
    return {"status": "ok", "router": "pool_selection"}

@router.post("/filter")
async def filter_loan_pool(
    dataset_id: str,
    filter_criteria: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Filter loan records based on specified criteria and return matching records.
    This is used for the initial filtering step.
    """
    try:
        logger.info(f"Filter request received with dataset_id: {dataset_id}")
        logger.info(f"Filter criteria: {filter_criteria}")
        
        # First, check if the dataset exists
        dataset_check = db.execute(
            text("SELECT COUNT(*) as count FROM datasets WHERE id = :dataset_id"),
            {"dataset_id": dataset_id}
        ).fetchone()
        
        if dataset_check and dataset_check.count == 0:
            logger.warning(f"Dataset {dataset_id} not found in database!")
        else:
            logger.info(f"Dataset {dataset_id} exists in database.")
        
        # Check field types in loan_records table
        try:
            field_info = {}
            for field_name in filter_criteria.keys():
                field_type_query = f"""
                SELECT data_type FROM information_schema.columns 
                WHERE table_name = 'loan_records' AND column_name = :column_name
                """
                field_type = db.execute(text(field_type_query), {"column_name": field_name}).fetchone()
                if field_type:
                    field_info[field_name] = field_type[0]
                    logger.info(f"Field '{field_name}' is type '{field_type[0]}'")
                else:
                    field_info[field_name] = "not found"
                    logger.warning(f"Field '{field_name}' not found in loan_records table")
                    
                # Check for special field mapping
                if field_name == "dpd":
                    dpd_field_type = db.execute(
                        text(field_type_query), 
                        {"column_name": "dpd_as_per_string"}
                    ).fetchone()
                    logger.info(f"Field 'dpd_as_per_string' is type '{dpd_field_type[0] if dpd_field_type else 'not found'}'")
        except Exception as e:
            logger.error(f"Error checking field types: {str(e)}")
        
        # Build query conditions based on filter criteria
        conditions = []
        params = {"dataset_id": dataset_id}
        
        # Add dataset filter
        conditions.append("dataset_id = :dataset_id")
        
        # Process each filter criteria
        for idx, (field, criteria) in enumerate(filter_criteria.items()):
            operator = criteria.get("operator", "=")
            param_name = f"param_{idx}"
            
            # Special handling for between operator
            if operator == "between":
                if "min_value" in criteria and criteria["min_value"] is not None and \
                   "max_value" in criteria and criteria["max_value"] is not None:
                    min_param = f"{param_name}_min"
                    max_param = f"{param_name}_max"
                    
                    # Special handling for DPD field (use dpd_as_per_string for filtering)
                    actual_field = "dpd_as_per_string" if field == "dpd" else field
                    conditions.append(f"{actual_field} BETWEEN :{min_param} AND :{max_param}")
                    params[min_param] = criteria["min_value"]
                    params[max_param] = criteria["max_value"]
                continue
            
            # Handle all other operators that use 'value'
            if "value" not in criteria or criteria["value"] is None:
                continue
            
            # Special handling for DPD field (use dpd_as_per_string for filtering)
            actual_field = "dpd_as_per_string" if field == "dpd" else field
                
            if operator == ">=":
                conditions.append(f"{actual_field} >= :{param_name}")
            elif operator == ">":
                conditions.append(f"{actual_field} > :{param_name}")
            elif operator == "<=":
                conditions.append(f"{actual_field} <= :{param_name}")
            elif operator == "<":
                conditions.append(f"{actual_field} < :{param_name}")
            elif operator == "=":
                conditions.append(f"{actual_field} = :{param_name}")
                
            params[param_name] = criteria["value"]
        
        # Build complete SQL query
        where_clause = " AND ".join(conditions)
        sql_query = f"""
        SELECT 
            id, 
            account_number, 
            customer_name,
            principal_os_amt,
            total_amt_disb,
            dpd_as_per_string as dpd,
            collection_12m,
            state,
            product_type
        FROM loan_records
        WHERE {where_clause}
        ORDER BY collection_12m DESC
        LIMIT 1000
        """
        
        logger.info(f"Executing SQL query: {sql_query}")
        logger.info(f"With parameters: {params}")
        
        # Print the actual SQL that would be executed
        try:
            from sqlalchemy.dialects import postgresql
            # Create a SQL statement
            stmt = text(sql_query)
            # Compile it with parameters
            compiled_stmt = stmt.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True}
            )
            # Format the SQL with parameters for logging
            compiled_query = str(compiled_stmt)
            logger.info(f"Compiled SQL with params: {compiled_query}")
        except Exception as e:
            logger.error(f"Error compiling SQL query for logging: {str(e)}")
            # This is just for logging, so continue with the main query execution
        
        # Execute the query
        result = db.execute(text(sql_query), params)
        records = result.fetchall()
        logger.info(f"Query returned {len(records)} records")
        
        # Check if there are records matching each individual condition
        for idx, (field, criteria) in enumerate(filter_criteria.items()):
            # For each filter, check how many records would match just this filter
            single_condition = ["dataset_id = :dataset_id"]
            single_params = {"dataset_id": dataset_id}
            
            operator = criteria.get("operator", "=")
            param_name = f"single_{idx}"
            
            # Special handling for DPD field
            actual_field = "dpd_as_per_string" if field == "dpd" else field
            
            if operator == "between" and "min_value" in criteria and "max_value" in criteria:
                single_condition.append(
                    f"{actual_field} BETWEEN :{param_name}_min AND :{param_name}_max"
                )
                single_params[f"{param_name}_min"] = criteria["min_value"]
                single_params[f"{param_name}_max"] = criteria["max_value"]
            elif "value" in criteria and criteria["value"] is not None:
                single_condition.append(f"{actual_field} {operator} :{param_name}")
                single_params[param_name] = criteria["value"]
            
            # Only check if we added a condition
            if len(single_condition) > 1:
                single_query = f"""
                SELECT COUNT(*) as count FROM loan_records
                WHERE {' AND '.join(single_condition)}
                """
                
                try:
                    single_result = db.execute(text(single_query), single_params).fetchone()
                    logger.info(f"Filter condition '{field} {operator}': matches {single_result.count} records")
                except Exception as e:
                    logger.error(f"Error checking individual filter '{field}': {str(e)}")
        
        # Check for any records in this dataset
        try:
            total_count = db.execute(
                text("SELECT COUNT(*) as count FROM loan_records WHERE dataset_id = :dataset_id"),
                {"dataset_id": dataset_id}
            ).fetchone()
            logger.info(f"Total records in dataset {dataset_id}: {total_count.count}")
        except Exception as e:
            logger.error(f"Error checking total records: {str(e)}")
        
        # Convert to list of dictionaries for JSON response
        column_names = result.keys()
        records_list = []
        
        # Log each record for debugging (limit to first 5)
        for i, record in enumerate(records):
            if i < 5:  # Log just the first few records to avoid overwhelming logs
                logger.info(f"Record {i+1}: {dict(zip(column_names, record))}")
            records_list.append(dict(zip(column_names, record)))
        
        # Calculate total principal outstanding amount
        total_pos = sum(float(record["principal_os_amt"]) for record in records_list) if records_list else 0
        
        return {
            "success": True,
            "filtered_count": len(records_list),
            "total_principal": total_pos,
            "records": records_list
        }
        
    except Exception as e:
        logger.error(f"Error filtering loan pool: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error filtering loan pool: {str(e)}")

@router.post("/optimize")
async def optimize_loan_selection(
    dataset_id: str,
    target_amount: float = Body(...),
    filter_criteria: Dict[str, Any] = Body(...),
    optimization_field: str = Body(...),  # e.g., "collection_12m"
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Optimize the selection of loans to reach a target amount while maximizing a specific field
    (like 12-month collection) from a filtered pool of loans.
    """
    try:
        # First, get the filtered pool
        filter_result = await filter_loan_pool(
            dataset_id=dataset_id, 
            filter_criteria=filter_criteria, 
            db=db, 
            current_user=current_user
        )
        
        # Get all records from the filtered pool
        all_records = filter_result.get("records", [])
        
        if not all_records:
            return {
                "success": False,
                "message": "No records match the filter criteria"
            }
            
        # Sort by the optimization field in descending order
        sorted_records = sorted(all_records, key=lambda x: x[optimization_field] if x[optimization_field] is not None else 0, reverse=True)
        
        # Knapsack-like algorithm to select records
        selected_records = []
        current_total = 0
        
        # First pass - greedy selection of records with highest optimization value
        for record in sorted_records:
            principal_amount = float(record["principal_os_amt"])
            if current_total + principal_amount <= target_amount:
                selected_records.append(record)
                current_total += principal_amount
        
        # If we need more precise targeting, we can do a second pass or other optimization
        # This is a simplified version
                
        return {
            "success": True,
            "target_amount": target_amount,
            "selected_amount": current_total,
            "difference": target_amount - current_total,
            "selected_count": len(selected_records),
            "optimization_field": optimization_field,
            "selected_records": selected_records
        }
        
    except Exception as e:
        logger.error(f"Error optimizing loan selection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error optimizing loan selection: {str(e)}")

@router.post("/save")
async def save_selection(
    dataset_id: str,
    name: str = Body(...),
    description: str = Body(None),
    records: List[Dict[str, Any]] = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Save a selection of loans as a named pool for future reference.
    """
    try:
        # Create new pool selection entry
        pool_selection = PoolSelection(
            name=name,
            description=description,
            dataset_id=dataset_id,
            user_id=current_user.id,
            total_amount=sum(float(record["principal_os_amt"]) for record in records),
            account_count=len(records)
        )
        db.add(pool_selection)
        db.flush()  # Flush to get the ID
        
        # Add records to the pool selection
        for record in records:
            pool_record = PoolSelectionRecord(
                pool_selection_id=pool_selection.id,
                loan_record_id=record["id"],
                principal_os_amt=record["principal_os_amt"]
            )
            db.add(pool_record)
        
        db.commit()
        
        return {
            "success": True,
            "pool_id": pool_selection.id,
            "name": name,
            "total_amount": pool_selection.total_amount,
            "account_count": pool_selection.account_count
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving pool selection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving pool selection: {str(e)}")

@router.get("/list")
async def list_selections(
    dataset_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    List all saved pool selections for the current user.
    """
    try:
        query = db.query(PoolSelection).filter(PoolSelection.user_id == current_user.id)
        
        if dataset_id:
            query = query.filter(PoolSelection.dataset_id == dataset_id)
            
        selections = query.all()
        
        return {
            "success": True,
            "selections": [
                {
                    "id": selection.id,
                    "name": selection.name,
                    "description": selection.description,
                    "dataset_id": selection.dataset_id,
                    "total_amount": selection.total_amount,
                    "account_count": selection.account_count,
                    "created_at": selection.created_at
                }
                for selection in selections
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing pool selections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing pool selections: {str(e)}")

@router.get("/{selection_id}")
async def get_selection(
    selection_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get details of a specific pool selection, including all selected records.
    """
    try:
        selection = db.query(PoolSelection).filter(
            PoolSelection.id == selection_id,
            PoolSelection.user_id == current_user.id
        ).first()
        
        if not selection:
            raise HTTPException(status_code=404, detail="Pool selection not found")
            
        # Get records in this selection
        records_query = """
        SELECT lr.*
        FROM loan_records lr
        JOIN pool_selection_records psr ON lr.id = psr.loan_record_id
        WHERE psr.pool_selection_id = :selection_id
        """
        
        result = db.execute(text(records_query), {"selection_id": selection_id})
        records = [dict(record) for record in result.fetchall()]
        
        return {
            "success": True,
            "selection": {
                "id": selection.id,
                "name": selection.name,
                "description": selection.description,
                "dataset_id": selection.dataset_id,
                "total_amount": selection.total_amount,
                "account_count": selection.account_count,
                "created_at": selection.created_at,
                "records": records
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pool selection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting pool selection: {str(e)}")
