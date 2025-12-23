# commented non-used code
# from pandas import ExcelFile
# from pandas.core.interchange.dataframe_protocol import DataFrame

from sqlalchemy.orm import Session
from app.models import models
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid
import json
import datetime
import re

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

def format_date_value(value):
    """
    Convert various date formats to a consistent format
    """
    if not value:
        return None
        
    # If it's already a datetime object, format it
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.strftime("%Y-%m-%d")
        
    # If it's a string, try to parse it
    if isinstance(value, str):
        # Remove any extra whitespace
        value = value.strip()
        
        # Handle special cases like "#N/A", "NA", etc.
        if value.upper() in ["#N/A", "NA", "N/A", "NULL", ""]:
            return None
            
        # Try different date formats
        date_formats = [
            "%Y-%m-%d",       # 2023-01-31
            "%d-%m-%Y",       # 31-01-2023
            "%d/%m/%Y",       # 31/01/2023
            "%m/%d/%Y",       # 01/31/2023
            "%m/%d/%y",       # 01/31/23 (MM/DD/YY format)
            "%d-%b-%Y",       # 31-Jan-2023
            "%d %b %Y",       # 31 Jan 2023
            "%d.%m.%Y",       # 31.01.2023
            "%Y/%m/%d",       # 2023/01/31
        ]
        
        for date_format in date_formats:
            try:
                parsed_date = datetime.datetime.strptime(value, date_format)
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue
                
        # If we couldn't parse the date, return the original value
        return value
        
    # If it's not a string or datetime, return as is
    return value

def get_loan_records(db: Session, dataset_id: UUID = None, skip: int = 0, limit: int = 100) -> List[models.LoanRecord]:
    """
    Get loan records for a dataset
    """
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


# commented non-used code
# Added hvb @ 17.10.25
# abandoned, instead done with mapping based upload
# def create_loan_records_multisheet(db:Session, excel_data:dict[str, DataFrame],dataset_id: UUID):
#     """
#     Create loan records for a dataset with multiple sheets
#     """
#     try:
#             print("Creating loan records for a dataset with multiple sheets")
#
#             # Load dataframes
#             df_pool = excel_data["Pool"]
#             df_dpd = excel_data["DPD"]
#             df_collection = excel_data["Collection"]
#
#             # print column names
#             for name, df in excel_data.items():
#                 print(f"\n{name} columns:", list(df.columns))
#
#             # Perform joins
#             merged_df = df_pool.merge(df_dpd, left_on="AGMTNO", right_on="SZAGREEMENTNO", how="left")
#             merged_df = merged_df.merge(df_collection, left_on="SZAGREEMENTNO", right_on="SZAGREEMENTNO", how="left")
#
#             # Convert to JSON
#             result_json = merged_df.to_dict(orient="records")
#
#             print(result_json)
#
#     except Exception as e:
#         print(f"Error creating loan records: {e}")
#         import traceback
#         traceback.print_exc()
#         return []


def create_loan_records(db: Session, records: List[dict], dataset_id: UUID):
    """
    Create loan records for a dataset
    """
    try:
        print("\n==== CREATING LOAN RECORDS ====")
        print(f"Creating {len(records)} loan records for dataset {dataset_id}")
        
        # Ensure dataset_id is a UUID object
        if isinstance(dataset_id, str):
            try:
                dataset_id = UUID(dataset_id)
            except ValueError:
                print(f"Invalid dataset_id format: {dataset_id}")
                return []
        
        # Check if dataset exists
        dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
        if not dataset:
            print(f"Dataset {dataset_id} not found in database")
            return []
            
        print(f"Dataset exists in DB: {dataset is not None}")
        print(f"Dataset name: {dataset.name}, ID: {dataset.id}")
        
        # Check if records already exist for this dataset
        existing_count = db.query(models.LoanRecord).filter(models.LoanRecord.dataset_id == dataset_id).count()
        if existing_count > 0:
            print(f"Warning: {existing_count} records already exist for this dataset. Proceeding will add more records.")
        
        # Print sample of the first record for debugging
        if records and len(records) > 0:
            print(f"First record sample: {list(records[0].keys())[:10]}")
            print(f"First record values: {list(records[0].values())[:10]}")
        
        # Process records
        db_records = []
        total_created = 0
        
        print(f"Processing {len(records)} actual records from the dataset...")
        
        # Field mapping dictionary - maps CSV field names (lowercase) to database column names
        field_mapping = {
            # Core fields
            'agreement no': 'agreement_no',
            'agreement_no': 'agreement_no',
            'agreementno': 'agreement_no',
            'loan no': 'loan_id',
            'loan_no': 'loan_id',
            'loanno': 'loan_id',
            'loan id': 'loan_id',
            'loan_id': 'loan_id',
            'loanid': 'loan_id',
            'customer name': 'customer_name',
            'customer_name': 'customer_name',
            'customername': 'customer_name',
            'borrower name': 'customer_name',
            'borrower_name': 'customer_name',
            'borrowername': 'customer_name',
            'principal os amt': 'principal_os_amt',
            'principal_os_amt': 'principal_os_amt',
            'principal os': 'principal_os_amt',
            'principal_os': 'principal_os_amt',
            'principal outstanding': 'principal_os_amt',
            'principal_outstanding': 'principal_os_amt',
            'principal outstanding amt': 'principal_os_amt',
            'principal_outstanding_amt': 'principal_os_amt',
            'principal_outstanding_amt': 'principal_os_amt',
            'principal outstanding amount': 'principal_os_amt',
            'pos': 'principal_os_amt',  # Map POS to principal_os_amt as well
            'pos amount': 'pos_amount',
            'pos_amount': 'pos_amount',
            
            # Date fields
            'first disb date': 'first_disb_date',
            'first_disb_date': 'first_disb_date',
            'firstdisbdate': 'first_disb_date',
            'last disb date': 'last_disb_date',
            'last_disb_date': 'last_disb_date',
            'lastdisbdate': 'last_disb_date',
            'sanction date': 'sanction_date',
            'sanction_date': 'sanction_date',
            'sanctiondate': 'sanction_date',
            'date of npa': 'date_of_npa',
            'date_of_npa': 'date_of_npa',
            'dateofnpa': 'date_of_npa',
            'date of woff': 'date_of_woff',
            'date_of_woff': 'date_of_woff',
            'dateofwoff': 'date_of_woff',
            
            # Validation fields
            'npa write off': 'npa_write_off',
            'npa_write_off': 'npa_write_off',
            'npawriteoff': 'npa_write_off',
            'date woff gt npa date': 'date_woff_gt_npa_date',
            'date_woff_gt_npa_date': 'date_woff_gt_npa_date',
            'datewoffgtnpadate': 'date_woff_gt_npa_date',
            
            # DPD fields
            'dpd as on 31st jan 2025': 'dpd_as_on_31st_jan_2025',
            'dpd_as_on_31st_jan_2025': 'dpd_as_on_31st_jan_2025',
            'dpd as per string': 'dpd_as_per_string',
            'dpd_as_per_string': 'dpd_as_per_string',
            'dpdasperstring': 'dpd_as_per_string',
            'difference': 'difference',
            'dpd by skc': 'dpd_by_skc',
            'dpd_by_skc': 'dpd_by_skc',
            'dpd': 'dpd',
            'diff': 'diff',
            
            # Amount fields
            'principal os amt': 'principal_os_amt',
            'principal_os_amt': 'principal_os_amt',
            'principalosamt': 'principal_os_amt',
            'interest overdue amt': 'interest_overdue_amt',
            'interest_overdue_amt': 'interest_overdue_amt',
            'interestoverdueamt': 'interest_overdue_amt',
            'penal interest overdue': 'penal_interest_overdue',
            'penal_interest_overdue': 'penal_interest_overdue',
            'penalinterestoverdue': 'penal_interest_overdue',
            'chq bounce other charges amt': 'chq_bounce_other_charges_amt',
            'chq_bounce_other_charges_amt': 'chq_bounce_other_charges_amt',
            'chqbounceotherchargesamt': 'chq_bounce_other_charges_amt',
            'total balance amt': 'total_balance_amt',
            'total_balance_amt': 'total_balance_amt',
            'totalbalanceamt': 'total_balance_amt',
            'provision done till date': 'provision_done_till_date',
            'provision_done_till_date': 'provision_done_till_date',
            'provisiondonetilldate': 'provision_done_till_date',
            'carrying value as on date': 'carrying_value_as_on_date',
            'carrying_value_as_on_date': 'carrying_value_as_on_date',
            'carryingvalueasondate': 'carrying_value_as_on_date',
            'sanction amt': 'sanction_amt',
            'sanction_amt': 'sanction_amt',
            'sanctionamt': 'sanction_amt',
            'total amt disb': 'total_amt_disb',
            'total_amt_disb': 'total_amt_disb',
            'totalamtdisb': 'total_amt_disb',
            'pos amount': 'pos_amount',
            'pos_amount': 'pos_amount',
            'posamount': 'pos_amount',
            'disbursement amount': 'disbursement_amount',
            'disbursement_amount': 'disbursement_amount',
            'disbursementamount': 'disbursement_amount',
            
            # Validation flags
            'pos gt dis': 'pos_gt_dis',
            'pos_gt_dis': 'pos_gt_dis',
            'posgtdis': 'pos_gt_dis',
            
            # Classification and status fields
            'classification': 'classification',
            'june 24 pool': 'june_24_pool',
            'june_24_pool': 'june_24_pool',
            'june24pool': 'june_24_pool',
            'product type': 'product_type',
            'product_type': 'product_type',
            'producttype': 'product_type',
            'status': 'status',
            
            # Customer information
            'customer name': 'customer_name',
            'customer_name': 'customer_name',
            'customername': 'customer_name',
            'state': 'state',
            'bureau score': 'bureau_score',
            'bureau_score': 'bureau_score',
            'bureauscore': 'bureau_score',
            
            # Collection fields
            'm1 collection': 'm1_collection',
            'm1_collection': 'm1_collection',
            'm1collection': 'm1_collection',
            'm2 collection': 'm2_collection',
            'm2_collection': 'm2_collection',
            'm2collection': 'm2_collection',
            'm3 collection': 'm3_collection',
            'm3_collection': 'm3_collection',
            'm3collection': 'm3_collection',
            '3m col': 'm3_collection',
            '3m_col': 'm3_collection',
            '3mcol': 'm3_collection',
            '3 month collection': 'm3_collection',
            '3_month_collection': 'm3_collection',
            '3monthcollection': 'm3_collection',
            'collection_3m': 'm3_collection',
            'collection 3m': 'm3_collection',
            'm4 collection': 'm4_collection',
            'm4_collection': 'm4_collection',
            'm4collection': 'm4_collection',
            'm5 collection': 'm5_collection',
            'm5_collection': 'm5_collection',
            'm5collection': 'm5_collection',
            'm6 collection': 'm6_collection',
            'm6_collection': 'm6_collection',
            'm6collection': 'm6_collection',
            '6m col': 'm6_collection',
            '6m_col': 'm6_collection',
            '6mcol': 'm6_collection',
            '6 month collection': 'm6_collection',
            '6_month_collection': 'm6_collection',
            '6monthcollection': 'm6_collection',
            'collection_6m': 'm6_collection',
            'collection 6m': 'm6_collection',
            'm7 collection': 'm7_collection',
            'm7_collection': 'm7_collection',
            'm7collection': 'm7_collection',
            'm8 collection': 'm8_collection',
            'm8_collection': 'm8_collection',
            'm8collection': 'm8_collection',
            'm9 collection': 'm9_collection',
            'm9_collection': 'm9_collection',
            'm9collection': 'm9_collection',
            'm10 collection': 'm10_collection',
            'm10_collection': 'm10_collection',
            'm10collection': 'm10_collection',
            'm11 collection': 'm11_collection',
            'm11_collection': 'm11_collection',
            'm11collection': 'm11_collection',
            'm12 collection': 'm12_collection',
            'm12_collection': 'm12_collection',
            'm12collection': 'm12_collection',
            '12m col': 'm12_collection',
            '12m_col': 'm12_collection',
            '12mcol': 'm12_collection',
            '12 month collection': 'm12_collection',
            '12_month_collection': 'm12_collection',
            '12monthcollection': 'm12_collection',
            'collection_12m': 'm12_collection',
            'collection 12m': 'm12_collection',
            '1y col': 'm12_collection',
            '1y_col': 'm12_collection',
            '1ycol': 'm12_collection',
            '1 year collection': 'm12_collection',
            '1_year_collection': 'm12_collection',
            '1yearcollection': 'm12_collection',
            'total collection': 'total_collection',
            'total_collection': 'total_collection',
            'totalcollection': 'total_collection',
            'post npa collection': 'post_npa_collection',
            'post_npa_collection': 'post_npa_collection',
            'postnpacollection': 'post_npa_collection',
            'post woff collection': 'post_woff_collection',
            'post_woff_collection': 'post_woff_collection',
            'postwoffcollection': 'post_woff_collection',
            
            # Auto-generated bucket fields
            'auto dpd bucket': 'auto_dpd_bucket',
            'auto_dpd_bucket': 'auto_dpd_bucket',
            'auto pos bucket': 'auto_pos_bucket',
            'auto_pos_bucket': 'auto_pos_bucket',
            'auto model year skc bucket': 'auto_model_year_skc_bucket',
            'auto_model_year_skc_bucket': 'auto_model_year_skc_bucket',
            'auto roi at booking bucket': 'auto_roi_at_booking_bucket',
            'auto_roi_at_booking_bucket': 'auto_roi_at_booking_bucket',
            'auto bureau score bucket': 'auto_bureau_score_bucket',
            'auto_bureau_score_bucket': 'auto_bureau_score_bucket',
            'auto current ltv bucket': 'auto_current_ltv_bucket',
            'auto_current_ltv_bucket': 'auto_current_ltv_bucket',
            
            # Legal fields
            'sec 17 order date 1': 'sec_17_order_date_1',
            'sec_17_order_date_1': 'sec_17_order_date_1',
            'sec 9 order date 1': 'sec_9_order_date_1',
            'sec_9_order_date_1': 'sec_9_order_date_1',
            'arbitration status': 'arbitration_status',
            'arbitration_status': 'arbitration_status',
            'action taken under s138 ni act': 'action_taken_under_s138_ni_act',
            'action_taken_under_s138_ni_act': 'action_taken_under_s138_ni_act',
        }
        
        # Helper function to clean and convert numeric values
        def clean_numeric(value):
            if value is None:
                return None
                
            # Convert to string if not already
            value_str = str(value).strip()
            
            # Handle special cases
            if value_str in ['', '-', ' - ', ' -   ', 'NA', 'N/A', '#N/A', 'None', 'null', 'NULL', 'nan', 'NaN']:
                return None
                
            # Remove commas, spaces, and other non-numeric characters except decimal point
            # First handle percentage values
            if '%' in value_str:
                value_str = value_str.replace('%', '')
                try:
                    return float(value_str.replace(',', '').strip()) / 100.0
                except (ValueError, TypeError):
                    print(f"Warning: Could not convert percentage value '{value}' to numeric value")
                    return None
            
            # Handle currency symbols
            for symbol in ['$', '₹', '€', '£', '¥']:
                if symbol in value_str:
                    value_str = value_str.replace(symbol, '')
            
            # Remove commas and spaces
            value_str = value_str.replace(',', '').replace(' ', '')
            
            # Handle parentheses for negative numbers - e.g., (100) means -100
            if value_str.startswith('(') and value_str.endswith(')'):
                value_str = '-' + value_str[1:-1]
            
            try:
                return float(value_str)
            except (ValueError, TypeError):
                print(f"Warning: Could not convert '{value}' to numeric value")
                return None
        
        # Data type conversion functions
        type_converters = {
            'first_disb_date': format_date_value,
            'last_disb_date': format_date_value,
            'sanction_date': format_date_value,
            'date_of_npa': format_date_value,
            'date_of_woff': format_date_value,
            
            # Integer fields
            'dpd_as_on_31st_jan_2025': lambda v: int(clean_numeric(v)) if clean_numeric(v) is not None else None,
            'dpd_as_per_string': lambda v: int(clean_numeric(v)) if clean_numeric(v) is not None else None,
            'difference': lambda v: int(clean_numeric(v)) if clean_numeric(v) is not None else None,
            'dpd_by_skc': lambda v: int(clean_numeric(v)) if clean_numeric(v) is not None else None,
            'diff': lambda v: int(clean_numeric(v)) if clean_numeric(v) is not None else None,
            'dpd': lambda v: int(clean_numeric(v)) if clean_numeric(v) is not None else None,
            'bureau_score': lambda v: int(clean_numeric(v)) if clean_numeric(v) is not None else None,
            'sec_17_order_date_1': lambda v: int(clean_numeric(v)) if clean_numeric(v) is not None else None,
            'sec_9_order_date_1': lambda v: int(clean_numeric(v)) if clean_numeric(v) is not None else None,
            
            # Float/decimal fields
            'principal_os_amt': clean_numeric,
            'interest_overdue_amt': clean_numeric,
            'penal_interest_overdue': clean_numeric,
            'chq_bounce_other_charges_amt': clean_numeric,
            'total_balance_amt': clean_numeric,
            'provision_done_till_date': clean_numeric,
            'carrying_value_as_on_date': clean_numeric,
            'sanction_amt': clean_numeric,
            'total_amt_disb': clean_numeric,
            'pos_amount': clean_numeric,
            'disbursement_amount': clean_numeric,
            'm1_collection': clean_numeric,
            'm2_collection': clean_numeric,
            'm3_collection': clean_numeric,
            'm4_collection': clean_numeric,
            'm5_collection': clean_numeric,
            'm6_collection': clean_numeric,
            'm7_collection': clean_numeric,
            'm8_collection': clean_numeric,
            'm9_collection': clean_numeric,
            'm10_collection': clean_numeric,
            'm11_collection': clean_numeric,
            'm12_collection': clean_numeric,
            'total_collection': clean_numeric,
            'post_npa_collection': clean_numeric,
            'post_woff_collection': clean_numeric,
            
            # Boolean fields
            'date_woff_gt_npa_date': lambda v: bool(v) if isinstance(v, bool) else (v.lower() == 'true' if isinstance(v, str) else bool(v)),
            'pos_gt_dis': lambda v: bool(v) if isinstance(v, bool) else (v.lower() == 'true' if isinstance(v, str) else bool(v)),
        }
        
        for i, record in enumerate(records):
            try:
                # Store all fields in additional_fields
                additional_fields = {}
                
                # Initialize a record with dataset_id
                db_record_data = {
                    'dataset_id': dataset_id,
                }
                
                # Process each field in the record
                for key, value in record.items():
                    if key is None or value is None or (isinstance(value, str) and not value.strip()):
                        continue
                        
                    # Store original value in additional_fields
                    additional_fields[key] = value
                    
                    # Try to map this field to a database column
                    key_lower = key.lower() if isinstance(key, str) else ""
                    
                    if key_lower in field_mapping:
                        db_field = field_mapping[key_lower]
                        
                        # Apply type conversion if needed
                        if db_field in type_converters:
                            try:
                                converted_value = type_converters[db_field](value)
                                db_record_data[db_field] = converted_value
                                
                                # Special handling for principal_os_amt
                                if db_field == 'principal_os_amt':
                                    print(f"Setting principal_os_amt from field '{key}' with value '{value}' to {converted_value}")
                            except Exception as e:
                                print(f"Error converting {key} ({value}) to {db_field}: {e}")
                                # Still store the original value
                                db_record_data[db_field] = value
                        else:
                            # Store as is
                            db_record_data[db_field] = value
                
                # Make sure we have an agreement_no (fallback if not found in the record)
                if 'agreement_no' not in db_record_data or not db_record_data['agreement_no']:
                    # Try to find it in common field names
                    for field_name in ['Loan No.', 'Loan No', 'Agreement No', 'Loan ID', 'Agreement Number', 'loan_no', 'agreement_no', 'AGREEMENT_NO']:
                        if field_name in additional_fields and additional_fields[field_name]:
                            db_record_data['agreement_no'] = str(additional_fields[field_name])
                            break
                    
                    # If still not found, use a generated value
                    if 'agreement_no' not in db_record_data or not db_record_data['agreement_no']:
                        db_record_data['agreement_no'] = f"LOAN-{i+1:04d}"
                
                # Store the additional_fields as JSON
                db_record_data['additional_fields'] = additional_fields
                
                # Look for collection fields in the CSV data
                collection_field_patterns = {
                    'm3_collection': [
                        '3m col', '3m_col', '3mcol', '3 month collection', '3_month_collection',
                        '3monthcollection', 'collection_3m', 'collection 3m', 'm3 collection', 'm3_collection', 'm3collection',
                        '3m', '3m collection', 'post npa collection'
                    ],
                    'm6_collection': [
                        '6m col', '6m_col', '6mcol', '6 month collection', '6_month_collection',
                        '6monthcollection', 'collection_6m', 'collection 6m', 'm6 collection', 'm6_collection', 'm6collection',
                        '6m', '6m collection', '6m col', '6m collection'
                    ],
                    'm12_collection': [
                        '12m col', '12m_col', '12mcol', '12 month collection', '12_month_collection',
                        '12monthcollection', 'collection_12m', 'collection 12m', '1y col', '1y_col', '1ycol',
                        '1 year collection', '1_year_collection', '1yearcollection', 'm12 collection', 'm12_collection', 'm12collection',
                        '12m', '12m collection', '12m col', '12 m collection'
                    ],
                    'total_collection': [
                        'total collection', 'total_collection', 'totalcollection', 'total col', 'total_col', 'totalcol',
                        'total', 'tot collection', 'tot col'
                    ]
                }
                
                # For each collection field
                for db_field, patterns in collection_field_patterns.items():
                    # Look for the field in additional_fields (case-insensitive)
                    found_value = None
                    
                    # First try exact matches with our patterns
                    for pattern in patterns:
                        if pattern in additional_fields:
                            try:
                                value = additional_fields[pattern]
                                converted_value = clean_numeric(value)
                                if converted_value is not None:
                                    found_value = converted_value
                                    print(f"Found {db_field} in field '{pattern}': {found_value}")
                                    break
                            except Exception as e:
                                print(f"Error converting {pattern}: {e}")
                    
                    # If not found, try case-insensitive matching
                    if found_value is None:
                        for key in additional_fields.keys():
                            if not isinstance(key, str):
                                continue
                                
                            key_lower = key.lower()
                            for pattern in patterns:
                                if key_lower == pattern or pattern in key_lower:
                                    try:
                                        value = additional_fields[key]
                                        converted_value = clean_numeric(value)
                                        if converted_value is not None:
                                            found_value = converted_value
                                            print(f"Found {db_field} in field '{key}' (case-insensitive): {found_value}")
                                            break
                                    except Exception as e:
                                        print(f"Error converting {key}: {e}")
                            if found_value is not None:
                                break
                    
                    # Update the record if a value was found
                    if found_value is not None:
                        db_record_data[db_field] = found_value
                        print(f"Set {db_field} = {found_value}")
                    else:
                        print(f"Could not find {db_field} in CSV data")
                
                # Create the record object but don't commit yet
                db_record = models.LoanRecord(**db_record_data)
                db.add(db_record)
                db_records.append(db_record)
                total_created += 1
                
                if (i+1) % 10 == 0 or (i+1) == len(records):
                    print(f"Created {total_created} records so far")
                    
            except Exception as e:
                # Just log the error and continue with the next record
                print(f"Error creating record {i+1}: {e}")
                import traceback
                traceback.print_exc()
                # Expunge the failed record from the session
                try:
                    if 'db_record' in locals():
                        db.expunge(db_record)
                except Exception as expunge_error:
                    print(f"Error expunging failed record: {expunge_error}")
        
        # Commit all records at once
        try:
            # Flush first to detect any issues before committing
            db.flush()
            
            # Verify records are in the session
            session_records = [r for r in db.new if isinstance(r, models.LoanRecord) and r.dataset_id == dataset_id]
            print(f"Found {len(session_records)} records in session before commit")
            
            # Now commit
            db.commit()
            print(f"Committed all {total_created} records to database")
        except Exception as e:
            db.rollback()
            print(f"Error committing records: {e}")
            import traceback
            traceback.print_exc()
            
            # Try to commit each record individually as a fallback
            print("Attempting to commit records individually as fallback...")
            individual_success = 0
            for i, record in enumerate(records):
                try:
                    # Create a new record object with dataset_id
                    db_record_data = {
                        'dataset_id': dataset_id,
                    }
                    
                    # Extract agreement_no from the record with proper field mapping
                    agreement_no = None
                    for field_name in ['agreement no', 'agreement_no', 'agreementno', 'loan no', 'loan_no', 'loanno', 
                                      'Loan No.', 'Loan No', 'Agreement No', 'Loan ID', 'Agreement Number', 
                                      'AGREEMENT_NO', 'LOAN_NO']:
                        if field_name in record and record[field_name]:
                            agreement_no = str(record[field_name])
                            break
                        # Also check case-insensitive
                        field_name_lower = field_name.lower()
                        for k in record.keys():
                            if k.lower() == field_name_lower and record[k]:
                                agreement_no = str(record[k])
                                break
                    
                    # Only use fallback if absolutely necessary
                    if not agreement_no:
                        print(f"WARNING: Record {i+1} has no agreement number! Available fields: {list(record.keys())[:5]}")
                        agreement_no = f"FALLBACK-{i+1:04d}"
                    
                    db_record_data['agreement_no'] = agreement_no
                    
                    # Process each field in the record using the field mapping
                    for key, value in record.items():
                        if key is None or (value is None and key_lower != 'principal_os_amt') or (isinstance(value, str) and not value.strip() and key_lower != 'principal_os_amt'):
                            continue
                            
                        # Try to map this field to a database column
                        key_lower = key.lower() if isinstance(key, str) else ""
                        
                        # Check for principal_os_amt in various formats
                        if key_lower in ['principal os amt', 'principal_os_amt', 'principal outstanding', 'principal outstanding amt', 'pos', 'principal_os']:
                            try:
                                converted_value = clean_numeric(value)
                                print(f"Found principal_os_amt in field '{key}': Original value: '{value}', Converted: {converted_value}")
                                db_record_data['principal_os_amt'] = converted_value
                            except Exception as e:
                                print(f"Error converting principal_os_amt from '{key}': {e}")
                        
                        if key_lower in field_mapping:
                            db_field = field_mapping[key_lower]
                            
                            # Apply type conversion if needed
                            if db_field in type_converters:
                                try:
                                    converted_value = type_converters[db_field](value)
                                    db_record_data[db_field] = converted_value
                                except Exception as e:
                                    print(f"Error converting {key} ({value}) to {db_field}: {e}")
                                    # Still store the original value
                                    db_record_data[db_field] = value
                            else:
                                # Store as is
                                db_record_data[db_field] = value
                    
                    # Print debug info for principal_os_amt
                    if 'principal_os_amt' in db_record_data:
                        print(f"Record {i+1} principal_os_amt: {db_record_data['principal_os_amt']}")
                    else:
                        print(f"Record {i+1} missing principal_os_amt. Fields: {list(db_record_data.keys())}")
                        # Try to find it in the original record
                        for k in record.keys():
                            if k.lower() in ['principal os amt', 'principal_os_amt', 'principal outstanding amt', 'principal outstanding', 'principal_outstanding', 'principal_outstanding_amt', 'pos']:
                                try:
                                    value = record[k]
                                    converted_value = clean_numeric(value)
                                    db_record_data['principal_os_amt'] = converted_value
                                    print(f"Found principal_os_amt in field '{k}': Original value '{value}', Converted to {converted_value}")
                                    break
                                except Exception as e:
                                    print(f"Error converting principal_os_amt from '{k}': {e}")
                        
                        # If still not found, try to use pos_amount if available
                        if 'principal_os_amt' not in db_record_data and 'pos_amount' in db_record_data:
                            db_record_data['principal_os_amt'] = db_record_data['pos_amount']
                            print(f"Using pos_amount as principal_os_amt: {db_record_data['principal_os_amt']}")
                        
                        # If still not found, check for any field containing 'principal' and 'os' or 'outstanding'
                        if 'principal_os_amt' not in db_record_data:
                            for k in record.keys():
                                key_lower = k.lower()
                                if ('principal' in key_lower) and ('os' in key_lower or 'outstanding' in key_lower):
                                    try:
                                        value = record[k]
                                        converted_value = clean_numeric(value)
                                        db_record_data['principal_os_amt'] = converted_value
                                        print(f"Found principal_os_amt in fuzzy match field '{k}': {db_record_data['principal_os_amt']}")
                                        break
                                    except Exception as e:
                                        print(f"Error converting principal_os_amt from fuzzy match '{k}': {e}")
                    
                    # Special handling for collection fields
                    # Handle m3_collection
                    if 'm3_collection' not in db_record_data or db_record_data['m3_collection'] is None:
                        print(f"Record {i+1} missing m3_collection. Looking for alternative fields...")
                        for k in record.keys():
                            if k.lower() in ['3m col', '3m_col', '3m collection', '3m_collection', '3 month collection', '3_month_collection', 'collection_3m']:
                                try:
                                    value = record[k]
                                    converted_value = clean_numeric(value)
                                    db_record_data['m3_collection'] = converted_value
                                    print(f"Found m3_collection in field '{k}': Original value '{value}', Converted to {converted_value}")
                                    break
                                except Exception as e:
                                    print(f"Error converting m3_collection from '{k}': {e}")
                    
                    # Handle m6_collection
                    if 'm6_collection' not in db_record_data or db_record_data['m6_collection'] is None:
                        print(f"Record {i+1} missing m6_collection. Looking for alternative fields...")
                        for k in record.keys():
                            if k.lower() in ['6m col', '6m_col', '6m collection', '6m_collection', '6 month collection', '6_month_collection', 'collection_6m']:
                                try:
                                    value = record[k]
                                    converted_value = clean_numeric(value)
                                    db_record_data['m6_collection'] = converted_value
                                    print(f"Found m6_collection in field '{k}': Original value '{value}', Converted to {converted_value}")
                                    break
                                except Exception as e:
                                    print(f"Error converting m6_collection from '{k}': {e}")
                    
                    # Handle m12_collection
                    if 'm12_collection' not in db_record_data or db_record_data['m12_collection'] is None:
                        print(f"Record {i+1} missing m12_collection. Looking for alternative fields...")
                        for k in record.keys():
                            if k.lower() in ['12m col', '12m_col', '12m collection', '12m_collection', '12 month collection', '12_month_collection', 'collection_12m', '1y col', '1y_col', '1 year collection', '1_year_collection']:
                                try:
                                    value = record[k]
                                    converted_value = clean_numeric(value)
                                    db_record_data['m12_collection'] = converted_value
                                    print(f"Found m12_collection in field '{k}': Original value '{value}', Converted to {converted_value}")
                                    break
                                except Exception as e:
                                    print(f"Error converting m12_collection from '{k}': {e}")
                    
                    # Store the additional_fields as JSON
                    db_record_data['additional_fields'] = record
                    
                    # Look for collection fields in the CSV data
                    collection_field_patterns = {
                        'm3_collection': [
                            '3m col', '3m_col', '3mcol', '3 month collection', '3_month_collection',
                            '3monthcollection', 'collection_3m', 'collection 3m', 'm3 collection', 'm3_collection', 'm3collection',
                            '3m', '3m collection', 'post npa collection'
                        ],
                        'm6_collection': [
                            '6m col', '6m_col', '6mcol', '6 month collection', '6_month_collection',
                            '6monthcollection', 'collection_6m', 'collection 6m', 'm6 collection', 'm6_collection', 'm6collection',
                            '6m', '6m collection', '6m col', '6m collection'
                        ],
                        'm12_collection': [
                            '12m col', '12m_col', '12mcol', '12 month collection', '12_month_collection',
                            '12monthcollection', 'collection_12m', 'collection 12m', '1y col', '1y_col', '1ycol',
                            '1 year collection', '1_year_collection', '1yearcollection', 'm12 collection', 'm12_collection', 'm12collection',
                            '12m', '12m collection', '12m col', '12 m collection'
                        ],
                        'total_collection': [
                            'total collection', 'total_collection', 'totalcollection', 'total col', 'total_col', 'totalcol',
                            'total', 'tot collection', 'tot col'
                        ]
                    }
                    
                    # For each collection field
                    for db_field, patterns in collection_field_patterns.items():
                        # Look for the field in additional_fields (case-insensitive)
                        found_value = None
                        
                        # First try exact matches with our patterns
                        for pattern in patterns:
                            if pattern in record:
                                try:
                                    value = record[pattern]
                                    converted_value = clean_numeric(value)
                                    if converted_value is not None:
                                        found_value = converted_value
                                        print(f"Found {db_field} in field '{pattern}': {found_value}")
                                        break
                                except Exception as e:
                                    print(f"Error converting {pattern}: {e}")
                        
                        # If not found, try case-insensitive matching
                        if found_value is None:
                            for key in record.keys():
                                if not isinstance(key, str):
                                    continue
                                    
                                key_lower = key.lower()
                                for pattern in patterns:
                                    if key_lower == pattern or pattern in key_lower:
                                        try:
                                            value = record[key]
                                            converted_value = clean_numeric(value)
                                            if converted_value is not None:
                                                found_value = converted_value
                                                print(f"Found {db_field} in field '{key}' (case-insensitive): {found_value}")
                                                break
                                        except Exception as e:
                                            print(f"Error converting {key}: {e}")
                                if found_value is not None:
                                    break
                        
                        # Update the record if a value was found
                        if found_value is not None:
                            db_record_data[db_field] = found_value
                            print(f"Set {db_field} = {found_value}")
                        else:
                            print(f"Could not find {db_field} in CSV data")
                    
                    # Create and commit in its own transaction
                    db_record = models.LoanRecord(**db_record_data)
                    db.add(db_record)
                    db.commit()
                    individual_success += 1
                except Exception as individual_error:
                    db.rollback()
                    print(f"Error committing individual record {i+1}: {individual_error}")
            
            if individual_success > 0:
                print(f"Successfully committed {individual_success} records individually")
                total_created = individual_success
            else:
                print("Failed to commit any records. Returning empty list.")
                return []
            
        print(f"\n==== RECORD CREATION SUMMARY ====")
        print(f"Successfully created {total_created} records out of {len(records)}")
        
        # Verify records were created
        verification_count = db.query(models.LoanRecord).filter(models.LoanRecord.dataset_id == dataset_id).count()
        print(f"Verification: {verification_count} records exist in database for this dataset")
        
        # If verification fails, log a detailed error
        if verification_count == 0 and total_created > 0:
            print("ERROR: Records were supposedly created but verification shows 0 records in database!")
            print("This indicates a transaction issue or database constraint violation.")
            
            # Try one more time with a very simple record as a diagnostic
            try:
                test_record = models.LoanRecord(
                    dataset_id=dataset_id,
                    agreement_no=f"TEST-RECORD-{uuid.uuid4()}",
                    principal_os_amt=1000,
                    dpd_as_on_31st_jan_2025=0,
                    classification="Standard",
                    additional_fields={}
                )
                db.add(test_record)
                db.commit()
                print("Successfully created a test record. The issue may be with the data format.")
            except Exception as test_error:
                db.rollback()
                print(f"Failed to create even a test record: {test_error}")
                print("This suggests a fundamental database connection or permission issue.")
        
        # Return the successfully created records
        return db_records
    
    except Exception as e:
        print(f"Error creating loan records: {e}")
        import traceback
        traceback.print_exc()
        return []


def update_collection_fields(db: Session, dataset_id: UUID):
    """
    Update the collection fields (m3_collection, m6_collection, m12_collection, total_collection)
    for all loan records in a dataset using the data from additional_fields.
    """
    try:
        # Get all loan records for the dataset
        loan_records = db.query(models.LoanRecord).filter(
            models.LoanRecord.dataset_id == dataset_id
        ).all()
        
        print(f"Updating collection fields for {len(loan_records)} loan records in dataset {dataset_id}")
        
        # Collection field names to look for in additional_fields
        collection_field_patterns = {
            'm3_collection': [
                '3m col', '3m_col', '3mcol', '3 month collection', '3_month_collection',
                '3monthcollection', 'collection_3m', 'collection 3m', 'm3 collection', 'm3_collection', 'm3collection'
            ],
            'm6_collection': [
                '6m col', '6m_col', '6mcol', '6 month collection', '6_month_collection',
                '6monthcollection', 'collection_6m', 'collection 6m', 'm6 collection', 'm6_collection', 'm6collection'
            ],
            'm12_collection': [
                '12m col', '12m_col', '12mcol', '12 month collection', '12_month_collection',
                '12monthcollection', 'collection_12m', 'collection 12m', '1y col', '1y_col', '1ycol',
                '1 year collection', '1_year_collection', '1yearcollection', 'm12 collection', 'm12_collection', 'm12collection'
            ],
            'total_collection': [
                'total collection', 'total_collection', 'totalcollection', 'total col', 'total_col', 'totalcol'
            ]
        }
        
        # No sample values - we'll only use real data from the records
        
        # For each loan record
        updated_count = 0
        for i, record in enumerate(loan_records):
            # Get the additional_fields
            additional_fields = record.additional_fields if record.additional_fields else {}
            
            # Flag to track if any updates were made
            updated = False
            
            # For each collection field
            for db_field, patterns in collection_field_patterns.items():
                # Skip if the field already has a value
                current_value = getattr(record, db_field)
                if current_value is not None and float(current_value) > 0:
                    continue
                
                # Look for the field in additional_fields
                found_value = None
                for pattern in patterns:
                    # Check for exact match
                    if pattern in additional_fields:
                        try:
                            value = additional_fields[pattern]
                            converted_value = clean_numeric(value)
                            if converted_value is not None:
                                found_value = converted_value
                                print(f"Found {db_field} in field '{pattern}': {found_value}")
                                break
                        except Exception as e:
                            print(f"Error converting {pattern}: {e}")
                    
                    # Check for case-insensitive match
                    for key in additional_fields.keys():
                        if isinstance(key, str) and key.lower() == pattern:
                            try:
                                value = additional_fields[key]
                                converted_value = clean_numeric(value)
                                if converted_value is not None:
                                    found_value = converted_value
                                    print(f"Found {db_field} in field '{key}' (case-insensitive): {found_value}")
                                    break
                            except Exception as e:
                                print(f"Error converting {key}: {e}")
                
                # If no value found, skip this field
                if found_value is None:
                    print(f"No value found for {db_field}, skipping")
                    continue
                
                # Update the record if a value was found
                if found_value is not None:
                    setattr(record, db_field, found_value)
                    updated = True
            
            # Update the record in the database if changes were made
            if updated:
                db.add(record)
                updated_count += 1
                
                # Commit every 100 records to avoid large transactions
                if updated_count % 100 == 0:
                    db.commit()
                    print(f"Committed {updated_count} updated records")
        
        # Final commit
        if updated_count % 100 != 0:
            db.commit()
        
        print(f"Updated collection fields for {updated_count} loan records")
        return updated_count
    except Exception as e:
        db.rollback()
        print(f"Error updating collection fields: {e}")
        import traceback
        traceback.print_exc()
        return 0
