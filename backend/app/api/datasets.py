from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, status, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, text, create_engine, extract
from typing import List, Dict, Any,Optional
from uuid import UUID
import uuid
import io
import pandas as pd
from datetime import date, datetime
import logging
import json
import os
import math
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from decimal import Decimal
from app.core.database import get_db
from app.curd.crud import dataset_crud
from app.curd.crud_loan_records import create_loan_records, get_loan_records as fetch_loan_records, update_collection_fields
from app.schemas import schemas
from app.models import models
from app.schemas.schemas import UpdateFileType
from app.services.csv_processor import process_csv_file
from app.core.auth.dependencies import get_current_user, get_current_user_optional
from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile, Request

# Import the fixed writeoff summary function
from app.api.fixed_writeoff_summary import generate_writeoff_pool_summary

# Import mapping based excel file reader, HVB @ 18/10/2025
from app.services.excel_mapped_upload import fn_read_excel_map_base as read_excel_map,upload_to_postgres as db_upload

# Import new model & List type for filter criteria fix HVB @ 26/10/2025
from app.models.FilterCriteriaItem import FilterCriteriaItem

# Import profile config reader, HVB @ 20/11/2025
from app.services.mapping_config_builder import get_full_profile_config

# Import helper files from utils , Jainil @ 13/1/2026
from app.utils.additional_fields_helper import normalize_additional_fields,MONTH_KEY_REGEX,MONTH_MAP
from app.utils.Validation_helper import infer_npa_from_dpd36m,DPD36M_TOLERANCE_DAYS,DPD36M_THRESHOLD
from datetime import date
from calendar import monthrange
router = APIRouter()

#format date to dd-mm-yyyy
def fmt(d):
    return d.strftime("%d-%m-%Y") if d else "-"


# In-memory store for custom bucket configs per dataset
custom_buckets_store = {}

@router.get("/", response_model=List[schemas.Dataset])
def get_datasets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # For development, return all datasets if none exist for the user
    datasets = dataset_crud.get_datasets(db, user_id=current_user.id)
    if not datasets:
        # Return all datasets in the database
        datasets = db.query(models.Dataset).all()
    return datasets

#Added hvb @ 18/10/2025
@router.post("/upload-mapped", response_model=schemas.Dataset)
async def upload_mapped_dataset(
file: UploadFile = File(...),
    metadata: str = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    print("Upload mapped dataset")
    # Parse metadata if provided
    dataset_name = file.filename
    dataset_description = f"Uploaded file: {file.filename}"
    # mod hvb @ 20/11/2025 read mapping from db
    # mapping_name = "mapping2"
    mapping_name = "0"

    if metadata:
        try:
            metadata_dict = json.loads(metadata)
            if "name" in metadata_dict and metadata_dict["name"]:
                dataset_name = metadata_dict["name"]
            if "description" in metadata_dict and metadata_dict["description"]:
                dataset_description = metadata_dict["description"]
            if "mapping" in metadata_dict and metadata_dict["mapping"]:
                mapping_name = metadata_dict["mapping"]
        except Exception as e:
            print(f"Error parsing metadata: {e}")

    print(f"Upload mapped dataset with mapping : {mapping_name}")
    # Read the file
    contents = await file.read()
    file_size = len(contents)

    # Determine file type and read accordingly
    file_extension = file.filename.split('.')[-1].lower()

    # check if file type is xlsx
    try:
        if file_extension in ['xls', 'xlsx']:
             # remove this, no point of reading here!
             # df = pd.read_excel(io.BytesIO(contents))
            print("Upload mapped xls file")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a Excel file.")

        # mod hvb @ 20/11/2025 read mapping from db
        # get mappings from database in phase 2
        # if mapping_name == "mapping1":
        #     # mock mapping
        #     print("Setting mock mappings")
        # elif mapping_name == "mapping2":
        #     print(f"mapping not found in data for {mapping_name}")
        #     raise HTTPException(status_code=404, detail=f"mapping not found in data for {mapping_name}")

        try:
            mapping_profile_id = int(mapping_name)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid mapping id, {mapping_name}.")

        config = get_full_profile_config(db, mapping_profile_id)

        if not config:
            raise HTTPException(status_code=404, detail="Mapping profile not found")

        underlying_file_type = config["underlying_file_type"]

        # Create dataset record in a separate transaction
        try:
                dataset = dataset_crud.create_dataset(
                   db,
                   schemas.DatasetCreate(name=dataset_name, description=dataset_description),
                   user_id=current_user.id,
                   file_name=file.filename,
                   file_size=file_size,
                   fileType=underlying_file_type # added hvb @ 02/12/2025
                )
                db.commit()  # Commit the dataset creation immediately
        except Exception as e:
                db.rollback()  # Explicitly rollback on error
                print(f"Error creating dataset: {e}")
                raise HTTPException(status_code=500, detail=f"Error creating dataset: {str(e)}")

        print(f"Dataset created with id :{dataset.id}")

        # mod hvb @ 20/11/2025 read mapping from db
        # --- Example mapping for Excel with-out header and column as _alias_col_idx ---
        # mapping_config = {
        #     "sheets": {
        #         2: {
        #             "header_row": -1, "skip_rows": 2,
        #             "cols_to_read": "0,2,6,7,8,9,10,11,12,13,14,15,17,18,19,26,27,28,32,35,41,44,46,50,51,52,53,54,55,56,57",
        #             "alias": "Pool",
        #             "key_columns":[0]
        #            },
        #         3: {
        #             "header_row": -1, "skip_rows": 1, "cols_to_read": "0,2,5", "alias": "DPD",
        #             "extra": [{"4": "npa_date_by_skc"}],
        #             "key_columns": [0]
        #            },
        #         4: {
        #             "header_row": -1, "skip_rows": 1, "cols_to_read": "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14",
        #             "alias": "Collection",
        #             "extra": [{"5": "total_emi_paid"}],
        #             "key_columns": [0],
        #             "clean_columns" : [{7:"dt"},{8:"int"}]
        #            }
        #     },
        #     "relations": [
        #         {"left": 2, "right": 3, "left_col": 0, "right_col": 0, "how": "left"},
        #         {"left": 2, "right": 4, "left_col": 0, "right_col": 0, "how": "left"}
        #     ]
        # }

        mapping_config = config["mapping_config"]
        print("=== MAPPING CONFIG DEBUG ===")
        from pprint import pprint
        pprint(mapping_config)
        print("============================")

        if not mapping_config:
            raise HTTPException(status_code=404, detail="Mapping profile not found,from backend")

        column_mapping = config["database_config"]
        if not column_mapping:
            raise HTTPException(status_code=404, detail="Mapping profile don't have column config,from backend")

        try:
            merged_df = read_excel_map(contents, mapping_config)

            print(merged_df["additional_fields"].iloc[0])



            print("==== DEBUG merged_df columns ====")
            for c in merged_df.columns:
                print(c)
            print("================================")

            merged_df.drop(
                    columns=[
                        "__ts__dpd36m",
                        "__ts__collection36m",
                        "extra_data_json",
                    ],
                    inplace=True,
                    errors="ignore"
                )
          
           
        # 🔑 Promote Pool date columns into semantic columns
            if "date_of_npa" not in merged_df.columns:
                merged_df["date_of_npa"] = merged_df.get("_Pool_col_4")

            if "date_of_woff" not in merged_df.columns:
                merged_df["date_of_woff"] = merged_df.get("_Pool_col_5")

            # ===============================
            # COMPUTE COLLECTION METRICS
            # ===============================
          

            def normalize_date(val):
                if val is None:
                    return None

                if isinstance(val, date) and not isinstance(val, datetime):
                    return val

                if isinstance(val, datetime):
                    return val.date()

                if isinstance(val, pd.Timestamp):
                    return val.date()

                if isinstance(val, (int, float)):
                    try:
                        return pd.to_datetime(val, unit="D", origin="1899-12-30").date()
                    except Exception:
                        return None

                if isinstance(val, str):
                    try:
                        return pd.to_datetime(val, dayfirst=True).date()
                    except Exception:
                        return None

                return None


            def parse_month_key(key: str) -> date:
                """
                Converts 'apr_25' → 2025-04-30
                """
                mon, yy = key.split("_")
                year = 2000 + int(yy)
                month = MONTH_MAP[mon[:3]]
                return date(year, month, monthrange(year, month)[1])


            def is_post_event(d: date, event_date: date | None) -> bool:
                """
                Financial logic:
                If an event happens anytime in a month,
                the entire month counts as post-event.
                """
                if not event_date:
                    return False
                return d >= event_date.replace(day=1)


            def compute_collection_metrics(additional_fields, date_of_npa, date_of_woff):
                """
                Returns:
                (total_collection, post_npa_collection, post_woff_collection, m6, m12)
                """

                date_of_npa = normalize_date(date_of_npa)
                date_of_woff = normalize_date(date_of_woff)

                af = normalize_additional_fields(additional_fields)
                series = af.get("collection36m", {})

                if not isinstance(series, dict) or not series:
                    return 0, 0, 0, 0, 0

                parsed = []

                for k, v in series.items():
                    try:
                        dt = parse_month_key(k)
                        amt = float(v) if isinstance(v, (int, float)) else 0.0
                        parsed.append((dt, amt))
                    except Exception:
                        continue

                if not parsed:
                    return 0, 0, 0, 0, 0

                parsed.sort(key=lambda x: x[0])

                total = sum(v for _, v in parsed)

                post_npa = (
                    sum(v for d, v in parsed if is_post_event(d, date_of_npa))
                    if date_of_npa else None
                )

                post_woff = (
                    sum(v for d, v in parsed if is_post_event(d, date_of_woff))
                    if date_of_woff else None
                )

                m6 = sum(v for _, v in parsed[-6:])
                m12 = sum(v for _, v in parsed[-12:])

                return total, post_npa, post_woff, m6, m12


                
            
            metrics_df = merged_df.apply(
                lambda row: compute_collection_metrics(
                    row["additional_fields"],
                    row.get("date_of_npa"),
                    row.get("date_of_woff")
                ),
                axis=1,
                result_type="expand"
            )

            metrics_df.columns = [
                "total_collection",
                "post_npa_collection",
                "post_woff_collection",
                "m6_collection",
                "m12_collection"
            ]

            drop_cols = [
                c for c in merged_df.columns
                if c.startswith("dpd__") or c.startswith("collection__")
            ]

            merged_df.drop(columns=drop_cols, inplace=True)


            merged_df = pd.concat([merged_df, metrics_df], axis=1)
            
            print("SAMPLE additional_fields:", merged_df["additional_fields"].iloc[0])

            print(
                merged_df.loc[
                    merged_df["_Pool_col_0"] == 174800100937,
                    ["additional_fields", "total_collection", "m6_collection", "m12_collection"]
                ].iloc[0]
            )

           # ===============================
            # HARD VALIDATIONS (FINAL)
            # ===============================

            if merged_df.empty:
                raise HTTPException(400, "No records found after mapping")

            sample_af = merged_df["additional_fields"].iloc[0]

            if not isinstance(sample_af, dict):
                raise HTTPException(400, "additional_fields not created")

            # -------------------------------
            # Namespace presence
            # -------------------------------
            has_dpd = "dpd36m" in sample_af
            has_collection = "collection36m" in sample_af

            if not has_dpd and not has_collection:
                raise HTTPException(400, "DPD36M and Collection36M both missing")

            # -------------------------------
            # DPD36M sanity
            # -------------------------------
            if has_dpd:
                def invalid_dpd(af):
                    if not isinstance(af, dict):
                        return False

                    dpd = af.get("dpd36m")
                    if not isinstance(dpd, dict):
                        return False

                    return any(
                        v is not None and (v < 0 or v > 1000)
                        for v in dpd.values()
                    )

                if merged_df["additional_fields"].apply(invalid_dpd).any():
                    raise HTTPException(400, "Invalid DPD36M value (must be 0–1000)")

            # -------------------------------
            # Collection36M sanity
            # -------------------------------
            if has_collection:
                def invalid_collection(af):
                    if not isinstance(af, dict):
                        return False

                    col = af.get("collection36m")
                    if not isinstance(col, dict):
                        return False

                    return any(
                        v is not None and v < 0
                        for v in col.values()
                    )


                if merged_df["additional_fields"].apply(invalid_collection).any():
                    raise HTTPException(400, "Negative collection value")

            # -------------------------------
            # Logical collection consistency
            # -------------------------------
            # if has_collection:
            #     if (merged_df["post_npa_collection"] > merged_df["total_collection"]).any():
            #         raise HTTPException(400, "Post-NPA > Total Collection")

            #     if (merged_df["post_woff_collection"] > merged_df["post_npa_collection"]).any():
            #         raise HTTPException(400, "Post-WOFF > Post-NPA")
            mask = (
                merged_df["post_npa_collection"].notna() &
                merged_df["post_woff_collection"].notna()
            )

            if (merged_df.loc[mask, "post_woff_collection"]
                > merged_df.loc[mask, "post_npa_collection"]).any():
                raise HTTPException(400, "Post-WOFF > Post-NPA")


                 
            print(
                "DB UPLOAD COLUMNS (resolved):",
                sorted(
                    c for c in merged_df.columns
                    if c in column_mapping
                )
            )

            computed_cols = [
                "total_collection",
                "post_npa_collection",
                "post_woff_collection",
                "m6_collection",
                "m12_collection",
            ]

            print("🔍 COMPUTED COLUMNS CHECK:")
            for c in computed_cols:
                print(c, "→", c in merged_df.columns)

            print("🚀 FINAL COLUMN MAPPING USED FOR DB UPLOAD:")
            for src, tgt in column_mapping.items():
                print(f"{src} → {tgt} | present in df:", src in merged_df.columns)


            





        except Exception as read_error:
            try:
                # mod hvb @ 23/11/2025 shifted from mapping read to here.
                print(f"❌ Error processing Excel: {read_error}")
                db.refresh(dataset)  # Refresh to get the latest state
                dataset.status = "error"
                dataset.description = f"{dataset.description} (Error: {str(read_error)[:100]}...)"
                db.commit()
            except Exception as refresh_error:
                db.rollback()
                print(f"Error updating dataset status: {refresh_error}")

            raise HTTPException(status_code=500, detail=f"Error reading loan records: {str(read_error)}")
        # --- Example column mapping (for upload) ---
        # while reading column configs for excel, read column config for database
        # this is mock only config.

        # Structure of config is dataframe_column: database_column,
        # refer below,
        # {"df_column_name": "database_column_name"}
        # mod hvb @ 20/11/2025 read mapping from db
        # column_mapping = {
        #     "data_id": "dataset_id",
        #     "_Pool_col_0": "agreement_no",
        #     "_Pool_col_7": "product_type_skc",
        #     "_Pool_col_9": "principal_os_amt",
        #     # mod hvb @ 21/10/2025 required in other column
        #     # "_Pool_col_13": "dpd_as_on_31st_jan_2025",
        #     # mod hvb @ 05/11/2025 as this columns are required in summary, updating same values in both columns
        #     "_Pool_col_13": ["dpd_as_per_string","dpd"],
        #     "_Pool_col_14": "dpd_by_skc",
        #     # mod hvb @ 05/11/2025 database column `dpd` now pointed above so putting data in dpd_31
        #     # "_Pool_col_15": "dpd",
        #     "_Pool_col_15": "dpd_as_on_31st_jan_2025",
        #     # mod hvb @ 21/10/2025 required in other column
        #     # "_Pool_col_18": "state_by_skc",
        #     "_Pool_col_18": "state",
        #     "_Pool_col_32": "employment_type",
        #     "_Pool_col_44": "brand_name_skc",
        #     "_Pool_col_50": "m3_collection",
        #     #mod hvb @ 21/10/2025 required in other column
        #     # "_Pool_col_51": "m12_collection",
        #     # mod hvb @ 05/11/2025 collection_12m required in filter, m12_collection required in summary
        #     # "_Pool_col_51": "collection_12m",
        #     "_Pool_col_51": ["collection_12m","m12_collection"],
        #     "_Pool_col_52": "m6_collection",
        #     "_Pool_col_53": "total_collection",
        #     "_Pool_col_54": "post_npa_collection",
        #     "_Pool_col_55": "post_woff_collection",
        #     "_Pool_col_56": "auto_pos_bucket",
        #     "_Pool_col_57": "auto_dpd_bucket",
        #     "_DPD_col_2": "pos_amount",
        #     "_DPD_col_5": "diff",
        #     "_Collection_col_2": "no_of_emi_paid",
        #     "_Collection_col_3": "auto_model_year_skc_bucket",
        #     "_Collection_col_4": "emi_amt",
        #     "_Collection_col_6": "date_of_npa",
        #     "_Collection_col_7": "date_of_woff",
        #     "_Collection_col_8": "difference",
        #     # in sheet numbers were there so commented hvb @ 21/10/25
        #     # "_Pool_col_19": "last_disb_date",
        #     "_Pool_col_10": "interest_overdue_amt",
        #     "_Pool_col_11": "penal_interest_overdue",
        #     "_Pool_col_12": "chq_bounce_other_charges_amt",
        #     "_Pool_col_8": "total_amt_disb",
        #     "_Pool_col_6": "product_type",
        #     "_Pool_col_41": "vehicle_description",
        #     "_Pool_col_26": "current_tenor",
        #     "_Pool_col_27": "balance_tenor",
        #     "_Pool_col_28": "roi_at_booking",
        #     "_Pool_col_2": "customer_name",
        #     # we want this to be replaced with state by skc
        #     # "_Pool_col_17": "state",
        #     "_Pool_col_35": "bureau_score",
        #     "_Pool_col_46": "auto_current_ltv_bucket",
        #     "extra_data_json": "additional_fields",
        # }



        # --- Example DB Engine ---
        # (replace credentials with your actual DB)
        db_engine = db

        if merged_df is not None:
            # --- Upload merged data to Postgres ---
            try:
                upload_result = db_upload(
                    dataset.id,
                    merged_df,
                    db_engine=db_engine.bind,
                    table_name="loan_records",
                    #table_name="loan_data", #testing with temporary table
                    column_mapping=column_mapping,
                    truncate_before_insert=False, ## Pass this as True only when temporary table
                    # truncate_before_insert=True  ## Pass this as True only when temporary table
                    # create_new_table=True
                )

                if upload_result["status"]:
                    print(f'> Data successfully processed and uploaded count {upload_result["inserted"]} / {upload_result["total"]}')

                    # Update dataset with record count
                    dataset.total_records = upload_result["inserted"]
                    db.commit()
                else:
                    print("❌ Failed to insert excel data into the database.")
                    db.refresh(dataset)  # Refresh to get the latest state
                    dataset.status = "error"
                    msg = "Failed to insert excel data into the database."
                    if upload_result["message"]:
                        msg = upload_result["message"]
                    dataset.description = f"{dataset.description} (Error: {msg[:100]}...)"
                    db.commit()
                    raise HTTPException(status_code=500, detail=f"Error adding loan records: {msg}")
            except Exception as upload_error:
                try:
                    db.refresh(dataset)  # Refresh to get the latest state
                    dataset.status = "error"
                    dataset.description = f"{dataset.description} (Error: {str(upload_error)[:100]}...)"
                    db.commit()
                except Exception as refresh_error:
                    db.rollback()
                    print(f"Error updating dataset status: {refresh_error}")

                raise HTTPException(status_code=500, detail=f"Error reading loan records: {str(upload_error)}")
        else:
            print("❌ Failed to read Excel file.")

        return dataset

    except Exception as e:
        # Ensure transaction is rolled back
        db.rollback()

        # Log the error and return a more helpful message
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()

        # Provide more detailed error information
        error_detail = str(e)
        if "create_loan_records" in error_detail:
            error_detail = "Error creating loan records. Please check the file format and try again."
        elif "read_csv" in error_detail or "read_excel" in error_detail:
            error_detail = "Error reading file. Please check the file format and try again."
        elif "json" in error_detail.lower():
            error_detail = "Error processing JSON data. Please check the file format and try again."
        elif "InFailedSqlTransaction" in error_detail:
            error_detail = "Database transaction error. Please try again."

        raise HTTPException(status_code=500, detail=f"Error processing file: {error_detail}")

@router.post("/upload", response_model=schemas.Dataset)
async def upload_dataset(
    file: UploadFile = File(...),
    metadata: str = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Parse metadata if provided
    dataset_name = file.filename
    dataset_description = f"Uploaded file: {file.filename}"
    
    if metadata:
        try:
            metadata_dict = json.loads(metadata)
            if "name" in metadata_dict and metadata_dict["name"]:
                dataset_name = metadata_dict["name"]
            if "description" in metadata_dict and metadata_dict["description"]:
                dataset_description = metadata_dict["description"]
        except Exception as e:
            print(f"Error parsing metadata: {e}")
    
    # Read the file
    contents = await file.read()
    file_size = len(contents)
    
    # Determine file type and read accordingly
    file_extension = file.filename.split('.')[-1].lower()
    
    try:
        if file_extension == 'csv':
            # Try different encodings if utf-8 fails
            try:
                df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(io.StringIO(contents.decode('latin-1')))
                except:
                    df = pd.read_csv(io.StringIO(contents.decode('cp1252')))
        elif file_extension in ['xls', 'xlsx']:
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a CSV or Excel file.")
        
        # Print the first few rows of the DataFrame for debugging
        print(f"DataFrame head:\n{df.head(2)}")
        print(f"DataFrame columns: {df.columns.tolist()}")
        
        # Create dataset record in a separate transaction
        try:
            dataset = dataset_crud.create_dataset(
                db,
                schemas.DatasetCreate(name=dataset_name, description=dataset_description),
                user_id=current_user.id,
                file_name=file.filename,
                file_size=file_size
            )
            db.commit()  # Commit the dataset creation immediately
        except Exception as e:
            db.rollback()  # Explicitly rollback on error
            print(f"Error creating dataset: {e}")
            raise HTTPException(status_code=500, detail=f"Error creating dataset: {str(e)}")
        
        print("\n==== UPLOAD DATASET PROCESSING ====")
        print(f"Dataset name: {dataset_name}")
        print(f"File name: {file.filename}")
        print(f"File size: {file_size} bytes")
        print(f"DataFrame shape: {df.shape}")
        print(f"DataFrame columns: {df.columns.tolist()}")
        
        # SIMPLIFIED APPROACH: Convert DataFrame to records and preserve original column names
        # Replace NaN/NA values with None for JSON serialization
        try:
            print("Replacing NA values...")
            df = df.replace({pd.NA: None, pd.NaT: None, np.nan: None})
            print("NA values replaced successfully")
        except Exception as e:
            print(f"Error replacing NA values: {e}")
            # Try a simpler approach
            df = df.fillna(value=None)
            print("Used fillna as fallback")
        
        # Convert to records
        try:
            print("Converting DataFrame to records...")
            records = df.to_dict('records')
            print(f"Converted {len(records)} records successfully")
        except Exception as e:
            print(f"Error converting DataFrame to records: {e}")
            raise HTTPException(status_code=500, detail=f"Error converting data to records: {str(e)}")
        
        # Log the first record for debugging
        if records and len(records) > 0:
            print(f"First record sample: {list(records[0].keys())[:10]}")
            print(f"Sample values: {list(records[0].items())[:5]}")
            
            # Print the first 5 keys and values to help identify field names
            print("First 5 keys and values:")
            for i, (k, v) in enumerate(records[0].items()):
                if i < 5:
                    print(f"  {k}: {v}")
                else:
                    break
            
            # Look for key fields we need
            key_fields = ['Loan No.', 'DPD', 'Classification', 'Principal O/S', 'Product Type', 'State', 
                         'POST NPA COLLECTION', 'POST W OFF COLLECTION', 'Arbitration status']
            for field in key_fields:
                found = False
                for col in records[0].keys():
                    if field.lower() in col.lower() or col.lower() in field.lower():
                        print(f"Found similar field for {field}: {col} = {records[0][col]}")
                        found = True
                        break
                if not found:
                    print(f"Could not find field similar to: {field}")
                    
            # Create a mapping of expected field names to actual field names
            field_mapping = {}
            for expected_field in key_fields:
                for actual_field in records[0].keys():
                    if expected_field.lower() in actual_field.lower() or \
                       expected_field.lower().replace(' ', '_') in actual_field.lower() or \
                       actual_field.lower() in expected_field.lower() or \
                       actual_field.lower().replace('_', ' ') in expected_field.lower():
                        field_mapping[expected_field] = actual_field
                        break
            
            print(f"Field mapping: {field_mapping}")
            
            # Print all column names from the Excel file for reference
            print(f"All columns in Excel file: {df.columns.tolist()}")
            
            # Print a few sample rows to verify data
            print(f"Sample data (first 2 rows):")
            for i, row in df.head(2).iterrows():
                print(f"Row {i+1}:")
                for col in df.columns[:5]:  # Print first 5 columns
                    print(f"  {col}: {row[col]}")
                print("  ...")
                for col in df.columns[-5:]:  # Print last 5 columns
                    print(f"  {col}: {row[col]}")
                print("")
            
            # Check for specific important fields
            important_fields = ['DPD', 'Classification', 'Principal O/S']
            for field in important_fields:
                similar_fields = [col for col in df.columns if field.lower() in col.lower() or col.lower() in field.lower()]
                if similar_fields:
                    print(f"Found fields similar to {field}: {similar_fields}")
                    for similar_field in similar_fields:
                        print(f"  Sample value: {df[similar_field].iloc[0]}")
                else:
                    print(f"No fields similar to {field} found")
            
        # Create loan records in a separate transaction
        try:
            created_records = create_loan_records(db, records, dataset.id)
            
            # Update dataset with record count
            dataset.total_records = len(records)
            db.commit()
        except Exception as e:
            db.rollback()  # Explicitly rollback on error
            print(f"Error creating loan records: {e}")
            import traceback
            traceback.print_exc()
            
            # Try to update the dataset status to indicate an error
            try:
                db.refresh(dataset)  # Refresh to get the latest state
                dataset.status = "error"
                dataset.description = f"{dataset.description} (Error: {str(e)[:100]}...)"
                db.commit()
            except Exception as refresh_error:
                db.rollback()
                print(f"Error updating dataset status: {refresh_error}")
            
            raise HTTPException(status_code=500, detail=f"Error creating loan records: {str(e)}")
        
        return dataset
    except Exception as e:
        # Ensure transaction is rolled back
        db.rollback()
        
        # Log the error and return a more helpful message
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        
        # Provide more detailed error information
        error_detail = str(e)
        if "create_loan_records" in error_detail:
            error_detail = "Error creating loan records. Please check the file format and try again."
        elif "read_csv" in error_detail or "read_excel" in error_detail:
            error_detail = "Error reading file. Please check the file format and try again."
        elif "json" in error_detail.lower():
            error_detail = "Error processing JSON data. Please check the file format and try again."
        elif "InFailedSqlTransaction" in error_detail:
            error_detail = "Database transaction error. Please try again."
        
        raise HTTPException(status_code=500, detail=f"Error processing file: {error_detail}")

@router.get("/{dataset_id}/records", response_model=List[schemas.LoanRecord])
def get_loan_records(
    dataset_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all loan records for a dataset"""
    # Convert string to UUID
    try:
        dataset_uuid = UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")
    
    # Check if dataset exists
    dataset = dataset_crud.get_dataset(db, dataset_uuid)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Get loan records
    loan_records = fetch_loan_records(db, dataset_uuid, skip=skip, limit=limit)
    
    # Check if we have any records
    if not loan_records:
        print(f"No loan records found for dataset {dataset_id}")
    else:
        print(f"Found {len(loan_records)} loan records for dataset {dataset_id}")
        if len(loan_records) > 0:
            print(f"First record ID: {loan_records[0].id}")
            print(f"First record agreement_no: {loan_records[0].agreement_no}")
            
            # Check if principal_os_amt is None and try to extract it from additional_fields
            if loan_records[0].principal_os_amt is None:
                print("First record principal_os_amt is None, checking additional_fields")
                if hasattr(loan_records[0], 'additional_fields') and loan_records[0].additional_fields:
                    try:
                        additional_fields = loan_records[0].additional_fields
                        if isinstance(additional_fields, str):
                            additional_fields = json.loads(additional_fields)
                        
                        # Look for principal_os_amt in additional_fields
                        for key in additional_fields.keys():
                            if key.lower() in ['principal_os_amt', 'principal os amt', 'principal outstanding', 'pos']:
                                print(f"Found principal_os_amt in additional_fields: {key} = {additional_fields[key]}")
                    except Exception as e:
                        print(f"Error parsing additional_fields: {e}")
            else:
                print(f"First record principal_os_amt: {loan_records[0].principal_os_amt}")
    
    # Helper function to extract fields from additional_fields
    def extract_field_value(record, field_name, field_alternatives):
        # First check if the field exists directly in the record
        if hasattr(record, field_name) and getattr(record, field_name) is not None:
            return getattr(record, field_name)
            
        try:
            if hasattr(record, 'additional_fields') and record.additional_fields:
                additional_fields = record.additional_fields
                if isinstance(additional_fields, str):
                    additional_fields = json.loads(additional_fields)
                    
                # Check common field names
                for alt_field_name in field_alternatives:
                    if alt_field_name in additional_fields and additional_fields[alt_field_name] is not None:
                        # Try to convert to float
                        try:
                            value = additional_fields[alt_field_name]
                            if isinstance(value, str):
                                value = value.replace(',', '').strip()
                                if value and value not in ['-', 'NA', 'N/A']:
                                    return float(value)
                            else:
                                return float(value)
                        except (ValueError, TypeError):
                            pass
                            
                # Try case-insensitive match
                for alt_field_name in field_alternatives:
                    field_lower = alt_field_name.lower()
                    for key in additional_fields:
                        if key.lower() == field_lower and additional_fields[key] is not None:
                            try:
                                value = additional_fields[key]
                                if isinstance(value, str):
                                    value = value.replace(',', '').strip()
                                    if value and value not in ['-', 'NA', 'N/A']:
                                        return float(value)
                                else:
                                    return float(value)
                            except (ValueError, TypeError):
                                pass
        except Exception as e:
            print(f"Error extracting {field_name}: {e}")
            
        return None
    
    # Helper function to extract principal_os_amt from additional_fields
    def extract_principal_os_amt(record):
        if record.principal_os_amt is not None:
            return record.principal_os_amt
            
        try:
            if hasattr(record, 'additional_fields') and record.additional_fields:
                additional_fields = record.additional_fields
                if isinstance(additional_fields, str):
                    additional_fields = json.loads(additional_fields)
                    
                # Check common field names for principal outstanding
                principal_field_names = [
                    'principal_os_amt', 'principal os amt', 'principal_outstanding_amt',
                    'principal outstanding amt', 'pos', 'pos_amount', 'principal_os',
                    'principal outstanding', 'principal_outstanding', 'principal o/s',
                    'Principal O/S', 'Principal Outstanding', 'POS', 'Principal OS Amt',
                    'PRINCIPAL_OS_AMT', 'PRINCIPAL_OUTSTANDING'
                ]
                
                for field_name in principal_field_names:
                    if field_name in additional_fields and additional_fields[field_name] is not None:
                        # Try to convert to float
                        try:
                            value = additional_fields[field_name]
                            if isinstance(value, str):
                                value = value.replace(',', '').strip()
                                if value and value not in ['-', 'NA', 'N/A']:
                                    return float(value)
                            else:
                                return float(value)
                        except (ValueError, TypeError):
                            pass
                            
                # Try case-insensitive match
                for field_name in principal_field_names:
                    field_lower = field_name.lower()
                    for key in additional_fields:
                        if key.lower() == field_lower and additional_fields[key] is not None:
                            try:
                                value = additional_fields[key]
                                if isinstance(value, str):
                                    value = value.replace(',', '').strip()
                                    if value and value not in ['-', 'NA', 'N/A']:
                                        return float(value)
                                else:
                                    return float(value)
                            except (ValueError, TypeError):
                                pass
        except Exception as e:
            print(f"Error extracting principal_os_amt: {e}")
            
        return None
    
    # Convert to dict and add additional_fields as a parsed JSON object
    result = []
    for record in loan_records:
        # Define core fields that should always be included
        core_fields = ["id", "dataset_id", "agreement_no"]
        
        # Define optional fields to include if they exist
        optional_fields = [
            "principal_os_amt", "dpd_as_on_31st_jan_2025", "classification", 
            "product_type", "customer_name", "state", "bureau_score", 
            "total_collection", "created_at", "first_disb_date", "loan_id", 
            "disbursement_date", "pos_amount", "disbursement_amount", "dpd", "status",
            "npa_write_off", "date_woff_gt_npa_date", "dpd_as_per_string",
            "difference", "dpd_by_skc", "diff", "interest_overdue_amt",
            "penal_interest_overdue", "chq_bounce_other_charges_amt",
            "total_balance_amt", "provision_done_till_date", 
            "carrying_value_as_on_date", "sanction_amt", "total_amt_disb",
            "pos_gt_dis", "june_24_pool", "has_validation_errors",
            "validation_error_types", "sanction_date", "date_of_npa",
            "date_of_woff", "last_disb_date"
        ]
        
        # Create a dictionary with the record data
        # Start with core fields
        record_dict = {}
        for field in core_fields:
            record_dict[field] = getattr(record, field)
        
        # Add optional fields if they exist
        for field in optional_fields:
            try:
                # Special handling for numeric fields that need extraction from additional_fields
                if field == 'principal_os_amt':
                    principal_field_names = [
                        'principal_os_amt', 'principal os amt', 'principal_outstanding_amt',
                        'principal outstanding amt', 'pos', 'pos_amount', 'principal_os',
                        'principal outstanding', 'principal_outstanding', 'principal o/s',
                        'Principal O/S', 'Principal Outstanding', 'POS', 'Principal OS Amt',
                        'PRINCIPAL_OS_AMT', 'PRINCIPAL_OUTSTANDING'
                    ]
                    record_dict[field] = extract_field_value(record, field, principal_field_names)
                elif field == 'total_balance_amt':
                    total_balance_field_names = [
                        'total_balance_amt', 'total balance amt', 'total_balance_amount',
                        'total balance amount', 'total balanceamt', 'total_balanceamt',
                        'Total Balance Amt', 'Total Balance', 'Total_BalanceAmt',
                        'TOTAL_BALANCE_AMT', 'Total_Balance_Amount'
                    ]
                    record_dict[field] = extract_field_value(record, field, total_balance_field_names)
                else:
                    value = getattr(record, field)
                    record_dict[field] = value
            except (AttributeError, KeyError):
                # Skip fields that don't exist
                pass
        
        # Parse additional_fields if it exists
        if hasattr(record, 'additional_fields') and record.additional_fields:
            try:
                if isinstance(record.additional_fields, str):
                    import json
                    record_dict["additional_fields"] = json.loads(record.additional_fields)
                else:
                    record_dict["additional_fields"] = record.additional_fields
            except Exception as e:
                print(f"Error parsing additional_fields: {e}")
                record_dict["additional_fields"] = {}
        else:
            record_dict["additional_fields"] = {}
            
        result.append(record_dict)
    
    return result

@router.get("/{dataset_id}/debug_records")
def get_debug_loan_records(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """Get debug information about loan records for a dataset"""
    # Convert string to UUID
    try:
        dataset_uuid = UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")
    
    # Check if dataset exists
    dataset = dataset_crud.get_dataset(db, dataset_uuid)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Get loan records
    loan_records = fetch_loan_records(db, dataset_uuid)
    
    # Create debug response
    debug_info = {
        "dataset_id": str(dataset_uuid),
        "total_records": len(loan_records),
        "record_samples": []
    }
    
    # Add sample records
    for record in loan_records[:5]:  # Only include first 5 records
        record_info = {
            "id": str(record["id"]),
            "agreement_no": record["agreement_no"],
            "principal_os_amt": record["principal_os_amt"],
            "dpd_as_on_31st_jan_2025": record["dpd_as_on_31st_jan_2025"] if "dpd_as_on_31st_jan_2025" in record else None,
            "classification": record["classification"],
            "product_type": record["product_type"],
            "state": record["state"]
        }
        
        # Parse additional_fields
        if "additional_fields" in record and record["additional_fields"]:
            try:
                additional_fields = record["additional_fields"]
                if isinstance(additional_fields, str):
                    additional_fields = json.loads(additional_fields)
                    
                record_info["additional_fields_keys"] = list(additional_fields.keys())
                
                # Include key fields from additional_fields
                key_fields = ['Loan No.', 'DPD', 'Classification', 'Principal O/S', 'Product Type', 'State']
                for field in key_fields:
                    if field in additional_fields:
                        record_info[f"raw_{field.lower().replace(' ', '_').replace('/', '_')}"] = additional_fields[field]
            except (json.JSONDecodeError, TypeError, AttributeError) as e:
                record_info["additional_fields_error"] = f"Failed to parse additional_fields: {str(e)}"
        
        debug_info["record_samples"].append(record_info)
    
    return debug_info

@router.post("/{dataset_id}/create_samples", response_model=schemas.Dataset)
async def create_sample_records(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create sample records for testing"""
    # Convert string to UUID
    try:
        dataset_uuid = UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")
    
    # Check if dataset exists
    dataset = dataset_crud.get_dataset(db, dataset_uuid)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Create sample records
    print(f"Creating sample records for dataset {dataset_id}")
    
    # Create 10 sample records
    records = []
    for i in range(10):
        record = {
            "agreement_no": f"LOAN-{i+1:04d}",
            "principal_os_amt": 10000 + (i * 1000),
            "dpd_as_on_31st_jan_2025": i * 30,
            "classification": ["Standard", "Sub-standard", "Doubtful", "Loss", "W/off"][i % 5],
            "product_type": ["Consumer Durable", "Personal Loan", "Home Loan", "Auto Loan"][i % 4],
            "state": ["AP", "TN", "KA", "MH", "DL"][i % 5],
            "customer_name": f"Customer {i+1}",
            "additional_fields": json.dumps({
                "Loan No.": f"LOAN-{i+1:04d}",
                "DPD": i * 30,
                "Classification": ["Standard", "Sub-standard", "Doubtful", "Loss", "W/off"][i % 5],
                "Principal O/S": 10000 + (i * 1000),
                "Product Type": ["Consumer Durable", "Personal Loan", "Home Loan", "Auto Loan"][i % 4],
                "State": ["AP", "TN", "KA", "MH", "DL"][i % 5]
            })
        }
        records.append(record)
    
    # Create the records
    try:
        db_records = []
        for record in records:
            db_record = models.LoanRecord(**record, dataset_id=dataset_uuid)
            db_records.append(db_record)
        
        db.add_all(db_records)
        db.commit()
        
        # Update dataset record count
        dataset.total_records = len(db_records)
        db.commit()
        
        print(f"Created {len(db_records)} sample records")
        return dataset
    except Exception as e:
        db.rollback()
        print(f"Error creating sample records: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating sample records: {str(e)}")

@router.post("/{dataset_id}/reprocess", response_model=schemas.Dataset)
async def reprocess_dataset(
    dataset_id: str,
    request: Request = None,  # Make request optional
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_optional)
):
    """
    Reprocess a dataset to fix issues with records not being saved properly.
    This will attempt to read the original file and save the records again.
    """
    try:
        # Convert string to UUID
        print(f"\n==== REPROCESSING DATASET ====")
        print(f"Reprocessing dataset: {dataset_id}")
        try:
            dataset_uuid = UUID(dataset_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid dataset ID format")
        
        # Check if dataset exists
        dataset = dataset_crud.get_dataset(db, dataset_uuid)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        print(f"Found dataset: {dataset.name}, total_records: {dataset.total_records}")
        
        # Try to find the original file in the uploads directory
        import os
        from pathlib import Path
        
        # Define possible upload directories
        upload_dirs = [
            "./uploads",
            "../uploads",
            "./data",
            "../data",
            "/tmp/uploads",
        ]
        
        # Try to find the file in one of the upload directories
        file_path = None
        for upload_dir in upload_dirs:
            if os.path.exists(upload_dir):
                # Look for files with the same name as the dataset file_name
                if dataset.file_name:
                    potential_path = os.path.join(upload_dir, dataset.file_name)
                    if os.path.exists(potential_path):
                        file_path = potential_path
                        break
                        
                # If we didn't find an exact match, look for any Excel or CSV files
                for file in os.listdir(upload_dir):
                    if file.lower().endswith(('.xlsx', '.xls', '.csv')):
                        file_path = os.path.join(upload_dir, file)
                        break
                        
                if file_path:
                    break
        
        # If we found the file, read it
        records = []
        if file_path:
            print(f"Found original file: {file_path}")
            try:
                # Read the file based on its extension
                file_extension = Path(file_path).suffix.lower()
                
                if file_extension in ['.csv']:
                    # Try different encodings if utf-8 fails
                    try:
                        df = pd.read_csv(file_path, encoding='utf-8')
                    except UnicodeDecodeError:
                        try:
                            df = pd.read_csv(file_path, encoding='latin-1')
                        except:
                            df = pd.read_csv(file_path, encoding='cp1252')
                elif file_extension in ['.xls', '.xlsx']:
                    df = pd.read_excel(file_path)
                else:
                    raise ValueError(f"Unsupported file format: {file_extension}")
                    
                # Replace NaN/NA values with None for JSON serialization
                df = df.replace({pd.NA: None, pd.NaT: None, np.nan: None})
                
                # Convert to records
                records = df.to_dict('records')
                print(f"Successfully read {len(records)} records from file")
                
                # Print the first record for debugging
                if records and len(records) > 0:
                    print(f"First record sample: {list(records[0].keys())[:10]}")
                    print(f"Sample values: {list(records[0].items())[:5]}")
            except Exception as e:
                print(f"Error reading file: {e}")
                import traceback
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
        else:
            print("Original file not found, generating sample records")
            # Create sample records (matching the total_records in the dataset)
            num_records = dataset.total_records or 99  # Default to 99 if total_records is not set
            for i in range(num_records):
                # Use the exact field names from the Excel file as seen in the image
                record = {
                    # Generate sample data
                    "Loan No.": f"3019CD{i+1:06d}",
                    "DPD": i % 90,
                    "Classification": ["Standard", "Sub-standard", "W/off"][i % 3],
                    "Principal O/S": 10000 + (i * 100),
                    "Disbursement Date": f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                    "Sanction Date": f"2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                    "Date of NPA": f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}" if i % 3 == 1 else None,
                    "Date of Write-off": f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}" if i % 3 == 2 else None,
                    "Product Type": ["Consumer Durable", "Personal Loan", "Home Loan", "Auto Loan"][i % 4],
                    "Property Value": 15000 + (i * 150) if i % 2 == 0 else None,
                    "LTV": 65 + (i % 30) if i % 2 == 0 else None,
                    "State": ["AP", "TN", "KA", "MH", "DL", "UP", "MP"][i % 7],
                    "No. of EMI Paid": i % 24,
                    "Balance Tenor": 24 - (i % 24),
                    "Legal Status": ["None", "Notice Sent", "Arbitration", "Recovery"][i % 4],
                    "POST NPA COLLECTION": i * 50 if i % 3 == 1 else 0,
                    "6M Collection": i * 100 if i % 2 == 0 else 0,
                    "12M Collection": i * 200 if i % 2 == 0 else 0,
                }
                records.append(record)
        
        # Delete existing records
        print(f"Deleting existing records for dataset {dataset_id}")
        deleted_count = db.query(models.LoanRecord).filter(models.LoanRecord.dataset_id == dataset_uuid).delete()
        db.commit()
        print(f"Deleted {deleted_count} existing records")
        
        # Now process the records (either from file or generated)
        print(f"Processing {len(records)} records for dataset {dataset_id}")
        
        # Log the first record for debugging
        if records and len(records) > 0:
            print(f"First record sample: {list(records[0].keys())[:10]}")
            print(f"Sample values: {list(records[0].items())[:5]}")
        
        # Save the records
        print(f"Saving {len(records)} records to database")
        created_records = loan_record_crud.create_loan_records(db, records, dataset_uuid)
        
        # Update the dataset record count
        actual_record_count = len(created_records) if created_records else 0
        print(f"Actually created {actual_record_count} records")
        
        dataset.total_records = actual_record_count
        db.commit()
        print(f"Updated dataset.total_records to {dataset.total_records}")
        
        # Verify records were created
        verification_count = db.query(models.LoanRecord).filter(models.LoanRecord.dataset_id == dataset_uuid).count()
        print(f"Verification: {verification_count} records exist in database for this dataset")
        
        return dataset
    except Exception as e:
        db.rollback()
        print(f"Error reprocessing dataset: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error reprocessing dataset: {str(e)}")

@router.post("/{dataset_id}/update-collection-fields")
async def update_dataset_collection_fields(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update the collection fields (m3_collection, m6_collection, m12_collection, total_collection)
    for all loan records in a dataset.
    """
    try:
        # Convert string to UUID
        try:
            dataset_uuid = UUID(dataset_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid dataset ID format")
        
        # Check if dataset exists
        dataset = dataset_crud.get_dataset(db, dataset_uuid)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Check if user has access to this dataset
        if dataset.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
        
        # Update collection fields
        print(f"Updating collection fields for dataset: {dataset_id}")
        updated_count = update_collection_fields(db, dataset_uuid)
        
        # Update dataset status
        dataset.status = "collection_fields_updated"
        from datetime import datetime
        dataset.updated_at = datetime.utcnow()
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        return {"status": "success", "message": f"Updated collection fields for {updated_count} records", "dataset_id": dataset_id}
    except Exception as e:
        print(f"Error updating collection fields: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{dataset_id}", response_model=schemas.Dataset)
async def delete_dataset(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Delete a dataset and all associated loan records.
    This will permanently remove the dataset and all its data from the database.
    """
    # Check if dataset exists and belongs to the current user
    dataset = db.query(models.Dataset).filter(
        models.Dataset.id == dataset_id,
        models.Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found or you don't have permission to delete it")
    
    try:
        # Delete all loan records associated with this dataset
        # SQLAlchemy will handle this automatically due to the cascade delete relationship
        # But we can explicitly delete them for clarity
        db.query(models.LoanRecord).filter(models.LoanRecord.dataset_id == dataset_id).delete()
        
        # Delete the dataset
        db.delete(dataset)
        db.commit()
        
        return dataset
    except Exception as e:
        db.rollback()
        print(f"Error deleting dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting dataset: {str(e)}")

@router.post("/{dataset_id}/reprocess-csv", response_model=schemas.Dataset)
@router.get("/{dataset_id}/summary", response_model=schemas.SummaryData)
async def get_dataset_summary(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get summary data for a dataset (all records).
    """
    return await generate_dataset_summary(dataset_id, db, current_user, None)

@router.post("/{dataset_id}/summary", response_model=schemas.SummaryData)
async def get_filtered_dataset_summary(
    dataset_id: str,
    # mod hvb @ 26/10/2025 pointed to new version for bug fixes allow multiple filters over same field
    filter_criteria: Dict[str, Any] = Body(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get summary data for a dataset with optional filter criteria.
    """
    # mod hvb @ 26/10/2025 pointed to new version for bug fixes allow multiple filters over same field
    return await generate_dataset_summary(dataset_id, db, current_user, filter_criteria)

@router.post("/{dataset_id}/summary-v2")
async def get_filtered_dataset_summary(
    dataset_id: str,
    # mod hvb @ 26/10/2025 pointed to new version for bug fixes allow multiple filters over same field
    # filter_criteria: Dict[str, Any] = Body(None),
     filter_criteria: Optional[List[FilterCriteriaItem]] = Body(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get summary data for a dataset with optional filter criteria.
    """
    # mod hvb @ 26/10/2025 pointed to new version for bug fixes allow multiple filters over same field
    # return await generate_dataset_summary(dataset_id, db, current_user, filter_criteria)
    return  await generate_dataset_summary_v2(dataset_id, db, current_user, filter_criteria)


# hvb @ 26/10/2025
# Created v2 function for keeping original function intact
# with ref. of original generate_dataset_summary function
# reason for new function : old function allows only one filter per field.
# updated portion code is marked with ###NEW BUG FIX
async def generate_dataset_summary_v2(
        dataset_id: str,
        db: Session,
        current_user: models.User,
        ###NEW BUG FIX
        filter_criteria: Optional[List[FilterCriteriaItem]] = None,
        ###NEW BUG FIX
):
    try:
        print("\n\n====** STARTING DATASET SUMMARY GENERATION ====\n")
        # Convert string to UUID
        try:
            dataset_uuid = UUID(dataset_id)
            print(f"***********Dataset ID converted to UUID: {dataset_uuid}")
        except ValueError:
            print(f"Invalid UUID format: {dataset_id}")
            raise HTTPException(status_code=400, detail="Invalid dataset ID format")

        # Check if dataset exists
        dataset = dataset_crud.get_dataset(db, dataset_uuid)
        if not dataset:
            print(f"Dataset not found: {dataset_uuid}")
            raise HTTPException(status_code=404, detail="Dataset not found")
        else:
            print(f"Found dataset: {dataset.name}, records: {dataset.total_records}")

        # Get loan records for this dataset, applying filters if provided
        query = db.query(models.LoanRecord).filter(
            models.LoanRecord.dataset_id == dataset_uuid
        )

        ###NEW BUG FIX
        filtered_records_info = "all records"
        if filter_criteria:
            print(f"Applying filter criteria: {filter_criteria}")
            filtered_records_info = "filtered records"

            for criteria in filter_criteria:
                if not criteria.enabled:
                    continue

                field = criteria.field
                is_direct_field = True
                if not hasattr(models.LoanRecord, field):
                    print(f"Unknown field: {field}, maybe json field")
                    is_direct_field = False

                if is_direct_field:
                    column = getattr(models.LoanRecord, field)
                else:
                    column = models.LoanRecord.additional_fields[field].astext

                # Apply filter based on operator
                try:
                    if criteria.operator == '>=':
                        query = query.filter(column >= criteria.value)
                    elif criteria.operator == '<=':
                        query = query.filter(column <= criteria.value)
                    elif criteria.operator == '=':
                        query = query.filter(column == criteria.value)
                    elif criteria.operator == '>':
                        query = query.filter(column > criteria.value)
                    elif criteria.operator == '<':
                        query = query.filter(column < criteria.value)
                    elif criteria.operator == '!=':
                        query = query.filter(column != criteria.value)
                    elif criteria.operator == 'between' and criteria.min_value is not None and criteria.max_value is not None:
                        query = query.filter(column.between(criteria.min_value, criteria.max_value))

                    # added hvb @ 11/12/2025 for new operators added on front-end
                    # Null checks
                    elif criteria.operator == 'isNull':
                        query = query.filter(column.is_(None))

                    elif criteria.operator == 'isNotNull':
                        query = query.filter(column.is_not(None))

                    # String containment
                    elif criteria.operator == 'contains':
                        # Case-insensitive contains
                        query = query.filter(column.ilike(f"%{criteria.value}%"))

                    elif criteria.operator == 'startsWith':
                        query = query.filter(column.ilike(f"{criteria.value}%"))

                    elif criteria.operator == 'endsWith':
                        query = query.filter(column.ilike(f"%{criteria.value}"))

                    else:
                        # Unclear/unsupported operator: kept for reference
                        print(f"Unsupported operator or missing values for field {field}: {criteria.operator}")
                except Exception as e:
                    # Keep original error handling
                    print(f"Error applying filter {criteria.field} {criteria.operator} {criteria.value}: {e}")

                print(
                    f"Applied filter: {field} {criteria.operator} {criteria.value or (criteria.min_value, criteria.max_value)}")

        # Rather then computing one-by-one we sum up data.
        # Mod hvb @ 08/12/2025
        # loan_records = query.all()

        field1_col = getattr(models.LoanRecord, "m12_collection")
        field2_col = getattr(models.LoanRecord, "m6_collection")
        field3_col = getattr(models.LoanRecord, "principal_os_amt")
        field4_col = getattr(models.LoanRecord, "total_collection")


        summary_query = (
            query.with_entities(
                func.sum(field1_col).label("total_12m_col"),
                func.sum(field2_col).label("total_m6_col"),
                func.sum(field3_col).label("total_pos"),
                func.sum(field4_col).label("totalCollection"),
                func.count().label("total_acs")
            )
        )

        result = summary_query.first()
        summary_dict = result._asdict() if result else {}
        return summary_dict

        # loan_records = query.all()
        #
        # print(f"Found {len(loan_records)} {filtered_records_info} for dataset {dataset.name}")
        # ###NEW BUG FIX
        #
        # # Check if any loan records have collection values
        # if loan_records:
        #     collection_values_found = False
        #     for i, record in enumerate(loan_records[:5]):  # Check first 5 records
        #         m3 = getattr(record, 'm3_collection', None)
        #         m6 = getattr(record, 'm6_collection', None)
        #         m12 = getattr(record, 'm12_collection', None)
        #         total = getattr(record, 'total_collection', None)
        #         print(f"Record {i + 1} collection values: m3={m3}, m6={m6}, m12={m12}, total={total}")
        #         if any(val is not None and val != 0 for val in [m3, m6, m12, total]):
        #             collection_values_found = True
        #
        #     print(f"Collection values found in records: {collection_values_found}")
        #
        # # Even if there are no loan records, we'll still generate the summary with mock data
        # # This ensures the frontend always gets a response
        # if not loan_records:
        #     print(f"No loan records found for dataset {dataset_uuid}, using mock data")
        #     # We'll continue with empty loan_records, the summary functions will handle it
        #
        # # Use custom buckets if present
        # default_pos_buckets = [
        #     (0, 1000, "0 to 1000"),
        #     (1000, 10000, "1000 to 10000"),
        #     (10000, 25000, "10000 to 25000"),
        #     (25000, 50000, "25000 to 50000"),
        #     (50000, 75000, "50000 to 75000"),
        #     (75000, 200000, "75000 to 200000"),
        #     (200000, 500000, "200000 to 500000"),
        #     (500000, 1000000, "500000 to 1000000"),
        #     (1000000, 9999999999, "1000000 to +")
        # ]
        # pos_buckets = get_custom_buckets(dataset_id, default_pos_buckets, bucket_type="writeOffPool")
        # # Patch the writeoff summary function to accept custom buckets
        # writeoff_pool = generate_writeoff_pool_summary(loan_records, pos_buckets=pos_buckets)
        # print(f"Write-Off Pool summary generated with {len(writeoff_pool['rows'])} rows")
        # # DPD buckets
        # default_dpd_buckets = [
        #     {"name": "360 to 365", "lower": 360, "upper": 365, "year": "1 Year"},
        #     {"name": "365 to 450", "lower": 365, "upper": 450, "year": "1.5 Year"},
        #     {"name": "450 to 540", "lower": 450, "upper": 540, "year": "1.5 Year"},
        #     {"name": "540 to 630", "lower": 540, "upper": 630, "year": "1.5 Year"},
        #     {"name": "630 to 720", "lower": 630, "upper": 720, "year": "2 Year"},
        #     {"name": "720 to 900", "lower": 720, "upper": 900, "year": "2 Year"},
        #     {"name": "900 to 1080", "lower": 900, "upper": 1080, "year": "3 Year"},
        #     {"name": "1080 to 1440", "lower": 1080, "upper": 1440, "year": "4 Year"},
        #     {"name": "1440 to 1800", "lower": 1440, "upper": 1800, "year": "5 year"},
        #     {"name": "1800 to +", "lower": 1800, "upper": 9999999999, "year": "5+ Year"}
        # ]
        #
        # def get_custom_dpd_buckets(dataset_id, default_buckets):
        #     dataset_buckets = custom_buckets_store.get(str(dataset_id), {})
        #     buckets = dataset_buckets.get("dpdSummary")
        #     if buckets and isinstance(buckets, list) and len(buckets) > 0:
        #         # Each bucket should have lowerBound and upperBound
        #         return [
        #             {"name": f"{b['lowerBound']} to {b['upperBound'] if b['upperBound'] != 9999999999 else '+'}",
        #              "lower": b['lowerBound'], "upper": b['upperBound'], "year": ""}
        #             for b in buckets
        #         ]
        #     return default_buckets
        #
        # dpd_buckets = get_custom_dpd_buckets(dataset_id, default_dpd_buckets)
        # # Patch the dpd summary function to accept custom buckets
        # dpd_summary = generate_dpd_summary(loan_records, dpd_buckets=dpd_buckets)
        # result = {
        #     "writeOffPool": writeoff_pool,
        #     "dpdSummary": dpd_summary
        # }
        # print("Summary data generated successfully")
        # print("\n==== API RESPONSE FOR SUMMARY ENDPOINT ====")
        # import json as _json
        # print(_json.dumps(result, indent=2, default=str))
        # print("==== END API RESPONSE ====")
        #
        # # Ensure all columns are present in every row for both tables
        # for table_key in ['writeOffPool', 'dpdSummary']:
        #     if table_key in result and 'columns' in result[table_key] and 'rows' in result[table_key]:
        #         col_keys = [col['key'] for col in result[table_key]['columns']]
        #         for row in result[table_key]['rows']:
        #             for key in col_keys:
        #                 if key not in row:
        #                     # Use 0.0 for float columns, 0 for int, or empty string for others
        #                     if key in ['pos', 'percentOfPos', '3mCol', '6mCol', '12mCol', 'totalCollection',
        #                                'disbursementAmt', 'posSundown']:
        #                         row[key] = 0.0
        #                     elif key in ['noOfAccs', 'lowerBound', 'upperBound']:
        #                         row[key] = 0
        #                     else:
        #                         row[key] = ''
        # return result
    except Exception as e:
        print(f"Error generating summary: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


async def generate_dataset_summary(
    dataset_id: str,
    db: Session,
    current_user: models.User,
    filter_criteria: Dict[str, Any] = None
):
    try:
        print("\n\n====** STARTING DATASET SUMMARY GENERATION ====\n")
        # Convert string to UUID
        try:
            dataset_uuid = UUID(dataset_id)
            print(f"***********Dataset ID converted to UUID: {dataset_uuid}")
        except ValueError:
            print(f"Invalid UUID format: {dataset_id}")
            raise HTTPException(status_code=400, detail="Invalid dataset ID format")
        
        # Check if dataset exists
        dataset = dataset_crud.get_dataset(db, dataset_uuid)
        if not dataset:
            print(f"Dataset not found: {dataset_uuid}")
            raise HTTPException(status_code=404, detail="Dataset not found")
        else:
            print(f"Found dataset: {dataset.name}, records: {dataset.total_records}")
        
        # Get loan records for this dataset, applying filters if provided
        query = db.query(models.LoanRecord).filter(
            models.LoanRecord.dataset_id == dataset_uuid
        )
        
        # Apply filters if provided
        filtered_records_info = "all records"
        if filter_criteria:
            print(f"Applying filter criteria: {filter_criteria}")
            filtered_records_info = "filtered records"
            
            for field, criteria in filter_criteria.items():
                if isinstance(criteria, dict) and 'operator' in criteria and 'value' in criteria:
                    operator = criteria['operator']
                    value = criteria['value']
                    
                    # Map field names to actual database columns
                    field_mapping = {
                        'dpd': 'dpd_as_per_string',  # Use dpd_as_per_string for dpd filters
                        'collection_12m': 'collection_12m',
                        'principal_os_amt': 'principal_os_amt',
                        'state': 'state',
                        'product_type': 'product_type'
                    }
                    
                    db_field = field_mapping.get(field, field)
                    
                    if hasattr(models.LoanRecord, db_field):
                        column = getattr(models.LoanRecord, db_field)
                        
                        if operator == '>=':
                            query = query.filter(column >= value)
                        elif operator == '<=':
                            query = query.filter(column <= value)
                        elif operator == '=':
                            query = query.filter(column == value)
                        elif operator == '>':
                            query = query.filter(column > value)
                        elif operator == '<':
                            query = query.filter(column < value)
                        elif operator == '!=':
                            query = query.filter(column != value)
                        elif operator == 'between' and 'min_value' in criteria and 'max_value' in criteria:
                            query = query.filter(column.between(criteria['min_value'], criteria['max_value']))
                        
                        print(f"Applied filter: {db_field} {operator} {value}")
        
        loan_records = query.all()
        
        print(f"Found {len(loan_records)} {filtered_records_info} for dataset {dataset.name}")
        
        # Check if any loan records have collection values
        if loan_records:
            collection_values_found = False
            for i, record in enumerate(loan_records[:5]):  # Check first 5 records
                m3 = getattr(record, 'm3_collection', None)
                m6 = getattr(record, 'm6_collection', None)
                m12 = getattr(record, 'm12_collection', None)
                total = getattr(record, 'total_collection', None)
                print(f"Record {i+1} collection values: m3={m3}, m6={m6}, m12={m12}, total={total}")
                if any(val is not None and val != 0 for val in [m3, m6, m12, total]):
                    collection_values_found = True
            
            print(f"Collection values found in records: {collection_values_found}")
        
        # Even if there are no loan records, we'll still generate the summary with mock data
        # This ensures the frontend always gets a response
        if not loan_records:
            print(f"No loan records found for dataset {dataset_uuid}, using mock data")
            # We'll continue with empty loan_records, the summary functions will handle it
        
        # Use custom buckets if present
        default_pos_buckets = [
            (0, 1000, "0 to 1000"),
            (1000, 10000, "1000 to 10000"),
            (10000, 25000, "10000 to 25000"),
            (25000, 50000, "25000 to 50000"),
            (50000, 75000, "50000 to 75000"),
            (75000, 200000, "75000 to 200000"),
            (200000, 500000, "200000 to 500000"),
            (500000, 1000000, "500000 to 1000000"),
            (1000000, 9999999999, "1000000 to +")
        ]
        pos_buckets = get_custom_buckets(dataset_id, default_pos_buckets, bucket_type="writeOffPool")
        # Patch the writeoff summary function to accept custom buckets
        writeoff_pool = generate_writeoff_pool_summary(loan_records, pos_buckets=pos_buckets)
        print(f"Write-Off Pool summary generated with {len(writeoff_pool['rows'])} rows")
        # DPD buckets
        default_dpd_buckets = [
            # added hvb @ 09/11/2025 for bucket-ing dpd in less then a year.
            {"name": "0 to 360", "lower": 0, "upper": 360, "year": "1- Year"},

            {"name": "360 to 365", "lower": 360, "upper": 365, "year": "1 Year"},
            {"name": "365 to 450", "lower": 365, "upper": 450, "year": "1.5 Year"},
            {"name": "450 to 540", "lower": 450, "upper": 540, "year": "1.5 Year"},
            {"name": "540 to 630", "lower": 540, "upper": 630, "year": "1.5 Year"},
            {"name": "630 to 720", "lower": 630, "upper": 720, "year": "2 Year"},
            {"name": "720 to 900", "lower": 720, "upper": 900, "year": "2 Year"},
            {"name": "900 to 1080", "lower": 900, "upper": 1080, "year": "3 Year"},
            {"name": "1080 to 1440", "lower": 1080, "upper": 1440, "year": "4 Year"},
            {"name": "1440 to 1800", "lower": 1440, "upper": 1800, "year": "5 year"},
            {"name": "1800 to +", "lower": 1800, "upper": 9999999999, "year": "5+ Year"}
        ]
        def get_custom_dpd_buckets(dataset_id, default_buckets):
            dataset_buckets = custom_buckets_store.get(str(dataset_id), {})
            buckets = dataset_buckets.get("dpdSummary")
            if buckets and isinstance(buckets, list) and len(buckets) > 0:
                # Each bucket should have lowerBound and upperBound
                return [
                    {"name": f"{b['lowerBound']} to {b['upperBound'] if b['upperBound'] != 9999999999 else '+'}", "lower": b['lowerBound'], "upper": b['upperBound'], "year": ""}
                    for b in buckets
                ]
            return default_buckets
        dpd_buckets = get_custom_dpd_buckets(dataset_id, default_dpd_buckets)
        # Patch the dpd summary function to accept custom buckets
        dpd_summary = generate_dpd_summary(loan_records, dpd_buckets=dpd_buckets)
        result = {
            "writeOffPool": writeoff_pool,
            "dpdSummary": dpd_summary
        }
        print("Summary data generated successfully")
        print("\n==== API RESPONSE FOR SUMMARY ENDPOINT ====")
        import json as _json
        print(_json.dumps(result, indent=2, default=str))
        print("==== END API RESPONSE ====")
        
        # Ensure all columns are present in every row for both tables
        for table_key in ['writeOffPool', 'dpdSummary']:
            if table_key in result and 'columns' in result[table_key] and 'rows' in result[table_key]:
                col_keys = [col['key'] for col in result[table_key]['columns']]
                for row in result[table_key]['rows']:
                    for key in col_keys:
                        if key not in row:
                            # Use 0.0 for float columns, 0 for int, or empty string for others
                            if key in ['pos', 'percentOfPos', '3mCol', '6mCol', '12mCol', 'totalCollection', 'disbursementAmt', 'posSundown']:
                                row[key] = 0.0
                            elif key in ['noOfAccs', 'lowerBound', 'upperBound']:
                                row[key] = 0
                            else:
                                row[key] = ''
        return result
    except Exception as e:
        print(f"Error generating summary: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# This function has been moved to fixed_writeoff_summary.py
# The implementation is now in app/api/fixed_writeoff_summary.py

# Generate DPD Summary function is still here
    
    # Print the final result for debugging
    print("\n==== Final Write-Off Pool Summary Result ====\n")
    print(f"Number of rows: {len(result['rows'])}")
    print(f"Number of columns: {len(result['columns'])}")
    print(f"Column keys: {[col['key'] for col in result['columns']]}")
    
    return result


def generate_dpd_summary(loan_records, dpd_buckets=None):
    """
    Generate DPD Summary table from loan records.
    """
    print("\n==== STARTING DPD SUMMARY GENERATION ====\n")
    # Use custom buckets if provided
    if dpd_buckets is None:
        dpd_buckets = [
            # added hvb @ 09/11/2025 for bucket-ing dpd in less then a year.
            {"name": "0 to 360", "lower": 0, "upper": 360, "year": "1- Year"},
            
            {"name": "360 to 365", "lower": 360, "upper": 365, "year": "1 Year"},
            {"name": "365 to 450", "lower": 365, "upper": 450, "year": "1.5 Year"},
            {"name": "450 to 540", "lower": 450, "upper": 540, "year": "1.5 Year"},
            {"name": "540 to 630", "lower": 540, "upper": 630, "year": "1.5 Year"},
            {"name": "630 to 720", "lower": 630, "upper": 720, "year": "2 Year"},
            {"name": "720 to 900", "lower": 720, "upper": 900, "year": "2 Year"},
            {"name": "900 to 1080", "lower": 900, "upper": 1080, "year": "3 Year"},
            {"name": "1080 to 1440", "lower": 1080, "upper": 1440, "year": "4 Year"},
            {"name": "1440 to 1800", "lower": 1440, "upper": 1800, "year": "5 year"},
            {"name": "1800 to +", "lower": 1800, "upper": 9999999999, "year": "5+ Year"}
        ]
    print("Defined DPD buckets", dpd_buckets)
    
    # No fallback values - we'll only use real data
    
    # Initialize buckets with zero counts
    bucket_data = {}
    for bucket in dpd_buckets:
        bucket_data[bucket["name"]] = {
            "year": bucket["year"],
            "bucket": bucket["name"],
            "lowerBound": bucket["lower"],
            "upperBound": bucket["upper"] if bucket["upper"] != 9999999999 else None,
            "noOfAccs": 0,
            "pos": 0.0,
            "percentOfPos": 0.0,
            "disbursementAmt": 0.0,
            "3mCol": 0.0,
            "6mCol": 0.0,
            "12mCol": 0.0,
            "totalCollection": 0.0,
            "posSundown": 0.0
        }
    print("Initialized buckets with zero values")
    
    # Add a grand total bucket
    bucket_data["Grand Total"] = {
        "year": "Grand Total",
        "bucket": "Grand Total",
        "lowerBound": None,
        "upperBound": None,
        "noOfAccs": 0,
        "pos": 0.0,
        "percentOfPos": 0.0,
        "disbursementAmt": 0.0,
        "3mCol": 0.0,
        "6mCol": 0.0,
        "12mCol": 0.0,
        "totalCollection": 0.0,
        "posSundown": 0.0
    }
    print("Initialized Grand Total bucket")
    
    # Check if we have loan records to process
    if not loan_records or len(loan_records) == 0:
        print("No loan records found, returning empty buckets")
    else:
        print(f"Processing {len(loan_records)} loan records for DPD summary")
        
        # Debug: Print sample DPD values from the first few records
        print("\n==== Sample DPD Values ====\n")
        dpd_samples = []
        for i, record in enumerate(loan_records[:10]):
            dpd = record.dpd if record.dpd is not None else record.dpd_as_on_31st_jan_2025
            pos = float(record.pos_amount) if record.pos_amount is not None else 0.0
            dpd_samples.append((dpd, pos))
            print(f"Record {i+1}: DPD = {dpd}, POS = {pos}")
        print("\n==== End Sample DPD Values ====\n")
    
    # Process each loan record if we have real data
    if loan_records and len(loan_records) > 0:
        has_data = False
        dpd_distribution = {bucket["name"]: 0 for bucket in dpd_buckets}
        records_with_dpd = 0
        records_without_dpd = 0
        records_outside_buckets = 0
        
        for record in loan_records:
            # Try to get DPD value from different possible fields
            dpd_value = None
            if hasattr(record, 'dpd') and record.dpd is not None:
                dpd_value = float(record.dpd)
            elif hasattr(record, 'dpd_as_on_31st_jan_2025') and record.dpd_as_on_31st_jan_2025 is not None:
                dpd_value = float(record.dpd_as_on_31st_jan_2025)
            elif hasattr(record, 'dpd_days') and record.dpd_days is not None:
                dpd_value = float(record.dpd_days)
            
            if dpd_value is None:
                records_without_dpd += 1
                continue  # Skip records without DPD
            
            records_with_dpd += 1
            
            # Get financial values
            pos_amount = 0.0
            disbursement_amount = 0.0
            
            # Try to get POS amount from different possible fields
            # Added hvb @ 11/11/2025 to make it similar field read for both dpd and write off summaries
            if hasattr(record, 'principal_os_amt') and record.principal_os_amt is not None:
                try:
                    pos_amount = float(record.principal_os_amt)
                except (ValueError, TypeError):
                    #  print(f"Error converting principal_os_amt: {record.principal_os_amt}")
                    pos_amount = 0
            elif hasattr(record, 'pos_amount') and record.pos_amount is not None:
                try:
                    pos_amount = float(record.pos_amount)
                except (ValueError, TypeError):
                    pass
            
            # Try to get disbursement amount
            if hasattr(record, 'disbursement_amount') and record.disbursement_amount is not None:
                try:
                    disbursement_amount = float(record.disbursement_amount)
                except (ValueError, TypeError):
                    pass
            # Added hvb @ 05/11/2025 for column from db.
            elif hasattr(record, 'total_amt_disb') and record.total_amt_disb is not None:
                try:
                    disbursement_amount = float(record.total_amt_disb)
                except (ValueError, TypeError):
                    pass
            
            # Find the appropriate bucket for this record
            bucket_name = None
            for bucket in dpd_buckets:
                if bucket["lower"] <= dpd_value < bucket["upper"]:
                    bucket_name = bucket["name"]
                    dpd_distribution[bucket_name] += 1
                    break
            
            if bucket_name is None:
                records_outside_buckets += 1
                print(f"Record with DPD {dpd_value} doesn't fit in any bucket")
                continue  # Skip records that don't fit in any bucket
            
            has_data = True  # We found at least one valid record
            
            # Update bucket data
            bucket_data[bucket_name]["noOfAccs"] += 1
            bucket_data[bucket_name]["pos"] += pos_amount / 1000000  # Convert to millions
            bucket_data[bucket_name]["disbursementAmt"] += disbursement_amount / 1000000
            
            # Update collection data
            m3_col = 0.0
            m6_col = 0.0
            m12_col = 0.0
            total_col = 0.0
            
            # Try to get collection values safely
            if hasattr(record, 'm3_collection') and record.m3_collection is not None:
                try:
                    m3_col = float(record.m3_collection)
                except (ValueError, TypeError):
                    pass
                    
            if hasattr(record, 'm6_collection') and record.m6_collection is not None:
                try:
                    m6_col = float(record.m6_collection)
                except (ValueError, TypeError):
                    pass
                    
            if hasattr(record, 'm12_collection') and record.m12_collection is not None:
                try:
                    m12_col = float(record.m12_collection)
                except (ValueError, TypeError):
                    pass
                    
            if hasattr(record, 'total_collection') and record.total_collection is not None:
                try:
                    total_col = float(record.total_collection)
                except (ValueError, TypeError):
                    pass
            
            # Add collection values without dividing by 1,000,000 to show actual values
            bucket_data[bucket_name]["3mCol"] += m3_col
            bucket_data[bucket_name]["6mCol"] += m6_col
            bucket_data[bucket_name]["12mCol"] += m12_col
            bucket_data[bucket_name]["totalCollection"] += total_col
            
            # Update grand total
            bucket_data["Grand Total"]["noOfAccs"] += 1
            bucket_data["Grand Total"]["pos"] += pos_amount / 1000000  # Keep POS in millions
            bucket_data["Grand Total"]["disbursementAmt"] += disbursement_amount / 1000000  # Keep disbursement in millions
            bucket_data["Grand Total"]["3mCol"] += m3_col
            bucket_data["Grand Total"]["6mCol"] += m6_col
            bucket_data["Grand Total"]["12mCol"] += m12_col
            bucket_data["Grand Total"]["totalCollection"] += total_col
        
        # Print DPD distribution statistics
        print(f"\n==== DPD Distribution Statistics ====\n")
        print(f"Total records: {len(loan_records)}")
        print(f"Records with DPD: {records_with_dpd}")
        print(f"Records without DPD: {records_without_dpd}")
        print(f"Records outside bucket ranges: {records_outside_buckets}")
        print("\nDistribution across buckets:")
        for bucket_name, count in dpd_distribution.items():
            print(f"  {bucket_name}: {count} records")
        print("\n==== End DPD Distribution Statistics ====\n")
        
        # Log whether we found valid data
        if not has_data:
            print("No valid DPD records found in loan data, using empty values")
        else:
            print("Using real data for DPD summary")
            
            # Only estimate POS values if needed, but don't add any collection values
            total_accs = bucket_data["Grand Total"]["noOfAccs"]
            total_pos = bucket_data["Grand Total"]["pos"]
            
            # If we have accounts but no POS values, log this but don't estimate
            if total_accs > 0 and total_pos == 0:
                print("Found accounts but no POS values in the data. Using actual values (0) for POS.")
    
    # Calculate percentages and POS Sundown
    total_pos = bucket_data["Grand Total"]["pos"]
    if total_pos > 0:
        for bucket_name in bucket_data:
            bucket_data[bucket_name]["percentOfPos"] = (bucket_data[bucket_name]["pos"] / total_pos) * 100
            
            # Calculate POS Sundown (totalCollection / pos * 100)
            if bucket_data[bucket_name]["pos"] > 0:
                bucket_data[bucket_name]["posSundown"] = (bucket_data[bucket_name]["totalCollection"] / bucket_data[bucket_name]["pos"]) * 100
    
    print(f"DPD Summary calculations complete")
    print(f"Total POS: {bucket_data['Grand Total']['pos']}")
    print(f"Total Accounts: {bucket_data['Grand Total']['noOfAccs']}")
    print(f"Total Collection: {bucket_data['Grand Total']['totalCollection']}")
    
    # Ensure all float values are JSON serializable and properly formatted for frontend
    for bucket_name in bucket_data:
        for key, value in bucket_data[bucket_name].items():
            # Handle NaN or infinity values
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                bucket_data[bucket_name][key] = 0.0  # Replace non-JSON-serializable floats with 0.0
            # Remove string conversion for collection values; keep as float
            if key in ['3mCol', '6mCol', '12mCol', 'totalCollection']:
                bucket_data[bucket_name][key] = float(value)
            elif isinstance(value, float):
                # Round other float values to 2 decimal places
                bucket_data[bucket_name][key] = round(value, 2)
    
    # Prepare the summary table
    columns = [
        {"key": "bucket", "title": "Bucket"},
        {"key": "lowerBound", "title": "Lower Bound"},
        {"key": "upperBound", "title": "Upper Bound"},
        {"key": "noOfAccs", "title": "No of Accs"},
        {"key": "pos", "title": "POS"},
        {"key": "percentOfPos", "title": "% of POS"},
        {"key": "disbursementAmt", "title": "Disbursement Amt"},
        {"key": "3mCol", "title": "3M Col"},
        {"key": "6mCol", "title": "6M Col"},
        {"key": "12mCol", "title": "12M Col"},
        {"key": "totalCollection", "title": "Total Collection"},
        {"key": "posSundown", "title": "POS SUNDOWN"}
    ]
    
    # Convert bucket data to rows
    rows = []
    for bucket in dpd_buckets:
        rows.append(bucket_data[bucket["name"]])
    
    # Add grand total row at the end
    rows.append(bucket_data["Grand Total"])
    
    # Debug the final result
    print("\n==== Debug DPD Summary ====\n")
    for i, row in enumerate(rows):
        print(f"Row {i+1} - Bucket: {row['bucket']}")
        print(f"  Accounts: {row['noOfAccs']}")
        print(f"  POS: {row['pos']}")
        print(f"  3M Col: {row['3mCol']}")
        print(f"  Total Collection: {row['totalCollection']}")
        print("---")
    print("\n==== End Debug DPD Summary ====\n")
    
    return {
        "id": "dpdSummary",
        "title": "DPD Summary",
        "columns": columns,
        "rows": rows
    }


async def reprocess_csv_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """
    Reprocess a dataset using the CSV file we created in the uploads directory.
    This endpoint doesn't require authentication for testing purposes.
    """
    try:
        # Convert string to UUID
        print(f"\n==== REPROCESSING CSV DATASET ====\n")
        print(f"Reprocessing dataset: {dataset_id}")
        try:
            dataset_uuid = UUID(dataset_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid dataset ID format")
        
        # Check if dataset exists
        dataset = dataset_crud.get_dataset(db, dataset_uuid)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        print(f"Found dataset: {dataset.name}, total_records: {dataset.total_records}")
        
        # Use our hardcoded CSV file path
        file_path = "./uploads/loan_data.csv"
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"CSV file not found at {file_path}")
        
        # Read the CSV file
        records = []
        print(f"Reading CSV file: {file_path}")
        try:
            # Try different encodings if utf-8 fails
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, encoding='latin-1')
                except:
                    df = pd.read_csv(file_path, encoding='cp1252')
                    
            # Replace NaN/NA values with None for JSON serialization
            df = df.replace({pd.NA: None, pd.NaT: None, np.nan: None})
            
            # Convert to records
            records = df.to_dict('records')
            print(f"Successfully read {len(records)} records from file")
            
            # Print the first record for debugging
            if records and len(records) > 0:
                print(f"First record sample: {list(records[0].keys())[:10]}")
                print(f"Sample values: {list(records[0].items())[:5]}")
        except Exception as e:
            print(f"Error reading file: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
        
        # Delete existing records
        print(f"Deleting existing records for dataset {dataset_id}")
        deleted_count = db.query(models.LoanRecord).filter(models.LoanRecord.dataset_id == dataset_uuid).delete()
        db.commit()
        print(f"Deleted {deleted_count} existing records")
        
        # Now process the records
        print(f"Processing {len(records)} records for dataset {dataset_id}")
        
        # Save the records
        print(f"Saving {len(records)} records to database")
        created_records = loan_record_crud.create_loan_records(db, records, dataset_uuid)
        
        # Update the dataset with the new record count
        dataset.total_records = len(created_records) if created_records else 0
        dataset.processed = True
        db.commit()
        
        # Verify records were created
        verification_count = db.query(models.LoanRecord).filter(models.LoanRecord.dataset_id == dataset_uuid).count()
        print(f"Verification: {verification_count} records exist in database for this dataset")
        
        print(f"Successfully reprocessed dataset. Created {len(created_records) if created_records else 0} records.")
        return dataset
    except Exception as e:
        db.rollback()
        print(f"Error reprocessing dataset: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Added hvb @ 03/12/2025 for setting file-type of dataset.
@router.put("/{dataset_id}/file-type")
def update_file_type(
    dataset_id: str,
    payload: UpdateFileType,
    db: Session = Depends(get_db)
):
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    dataset.file_type = payload.file_type
    db.commit()
    db.refresh(dataset)

    return {"message": "File type updated", "file_type": dataset.file_type}

@router.get("/{dataset_id}/dataset-file-type")
def get_dataset_file_type(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return {"message": "File type found", "file_type": dataset.file_type}


@router.put("/{dataset_id}/summary/buckets")
async def update_summary_buckets(dataset_id: str, body: dict = Body(...)):
    """
    Update the bucket configuration for a dataset (in-memory only).
    """
    buckets = body.get("buckets")
    bucket_type = body.get("type")
    if not isinstance(buckets, list) or not bucket_type:
        raise HTTPException(status_code=422, detail="buckets must be a list and type must be provided")
    if dataset_id not in custom_buckets_store:
        custom_buckets_store[dataset_id] = {}
    custom_buckets_store[dataset_id][bucket_type] = buckets
    print(f"Custom buckets for dataset {dataset_id} type {bucket_type} updated: {buckets}")
    return {"status": "success", "buckets": buckets, "type": bucket_type}

def get_custom_buckets(dataset_id, default_buckets, bucket_type="writeOffPool"):
    dataset_buckets = custom_buckets_store.get(str(dataset_id), {})
    buckets = dataset_buckets.get(bucket_type)
    if buckets and isinstance(buckets, list) and len(buckets) > 0:
        # Each bucket should have lowerBound and upperBound
        return [(b['lowerBound'], b['upperBound'], f"{b['lowerBound']} to {b['upperBound'] if b['upperBound'] != 9999999999 else '+'}") for b in buckets]
    return default_buckets

def get_custom_dpd_buckets(dataset_id, default_buckets):
    dataset_buckets = custom_buckets_store.get(str(dataset_id), {})
    buckets = dataset_buckets.get("dpdSummary")
    if buckets and isinstance(buckets, list) and len(buckets) > 0:
        # Each bucket should have lowerBound and upperBound
        return [
            {"name": f"{b['lowerBound']} to {b['upperBound'] if b['upperBound'] != 9999999999 else '+'}", "lower": b['lowerBound'], "upper": b['upperBound'], "year": ""}
            for b in buckets
        ]
    return default_buckets

@router.get("/{dataset_id}/validations")
def get_validations(dataset_id: str, db: Session = Depends(get_db)):
    try:
        dataset_uuid = UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    # 1. DPD > 0
    dpd_gt_0 = db.query(models.LoanRecord).filter(
        models.LoanRecord.dataset_id == dataset_uuid,
        or_(
            models.LoanRecord.dpd_as_on_31st_jan_2025 <= 0,
            models.LoanRecord.dpd_as_on_31st_jan_2025 == None
        )
    ).count()

    # 2. POS > Disbursement
    pos_lt_disbursement = db.query(models.LoanRecord).filter(
        models.LoanRecord.dataset_id == dataset_uuid,
        #Added by jainil, merged hvb @ 15/12/2025
        # models.LoanRecord.principal_os_amt >= models.LoanRecord.disbursement_amount
        # <=
        models.LoanRecord.principal_os_amt <= models.LoanRecord.disbursement_amount
    ).count()

    # 3. POS < DIS
    pos_gt_dis = db.query(models.LoanRecord).filter(
        models.LoanRecord.dataset_id == dataset_uuid,
        #Added by jainil, merged hvb @ 15/12/2025
        # models.LoanRecord.principal_os_amt <= models.LoanRecord.disbursement_amount
        models.LoanRecord.principal_os_amt > models.LoanRecord.disbursement_amount
    ).count()

    # 4. Date format (flag records with invalid/missing dates)
    date_format = db.query(models.LoanRecord).filter(
        models.LoanRecord.dataset_id == dataset_uuid,
        or_(
        	#Added by jainil, merged hvb @ 15/12/2025
            # models.LoanRecord.first_disb_date == None,
            # models.LoanRecord.sanction_date == None
			models.LoanRecord.last_disb_date.is_(None),
            models.LoanRecord.sanction_date.is_(None),
            models.LoanRecord.date_of_npa.is_(None),
            models.LoanRecord.date_of_woff.is_(None),

            # import extract from sqlalchemy
            # Year < 2000 checks
            extract('year', models.LoanRecord.last_disb_date) < 2000,
            extract('year', models.LoanRecord.sanction_date) < 2000,
            extract('year', models.LoanRecord.date_of_npa) < 2000,
            extract('year', models.LoanRecord.date_of_woff) < 2000,
        )
    ).count()

    # 5. Duplicate Loan No.
    duplicate_loan_no = db.query(models.LoanRecord.agreement_no).filter(
        models.LoanRecord.dataset_id == dataset_uuid
    ).group_by(models.LoanRecord.agreement_no).having(func.count(models.LoanRecord.agreement_no) > 1).count()

    # 6. Blank required fields
    blank_required_fields = db.query(models.LoanRecord).filter(
        models.LoanRecord.dataset_id == dataset_uuid,
        or_(
            models.LoanRecord.agreement_no == None,
            models.LoanRecord.dpd_as_on_31st_jan_2025 == None,
            models.LoanRecord.principal_os_amt == None
        )
    ).count()

    # 7. Minimum POS Amount
    min_pos_amount = db.query(models.LoanRecord).filter(
        models.LoanRecord.dataset_id == dataset_uuid,
        models.LoanRecord.principal_os_amt < 1000
    ).count()

    # 8. TOS Calculation (example: TOS != POS + interest_overdue_amt)
    tos_calc = db.query(models.LoanRecord).filter(
        models.LoanRecord.dataset_id == dataset_uuid,
        models.LoanRecord.total_balance_amt != (models.LoanRecord.principal_os_amt + models.LoanRecord.interest_overdue_amt)
    ).count()

    # 9. Negative collections
    negative_collections = db.query(models.LoanRecord).filter(
        models.LoanRecord.dataset_id == dataset_uuid,
        or_(
            models.LoanRecord.total_collection < 0,
            models.LoanRecord.m3_collection < 0,
            models.LoanRecord.m6_collection < 0,
            models.LoanRecord.m12_collection < 0
        )
    ).count()

    # added by Jainil NPA date should be less than write-off date 

    # 10. NPA Date should be less than Write-off Date
    npa_date_le_woff_date = db.query(models.LoanRecord).filter(
    models.LoanRecord.dataset_id == dataset_uuid,
    or_(
        models.LoanRecord.date_of_npa.is_(None),
        models.LoanRecord.date_of_woff.is_(None),
        models.LoanRecord.date_of_npa >= models.LoanRecord.date_of_woff
    )
    ).count()

    # 11. calculate avg ticket size
    avg_ticket_data = db.query(
        func.coalesce(func.sum(models.LoanRecord.principal_os_amt), 0),
        func.count(models.LoanRecord.id)
    ).filter(
        models.LoanRecord.dataset_id == dataset_uuid,
        models.LoanRecord.principal_os_amt.isnot(None)
    ).one()

    total_pos, account_count = avg_ticket_data

    average_ticket_size = (
        float(total_pos) / account_count
        if account_count > 0 else 0
    ) 
    average_ticket_size = round(average_ticket_size, 2)

    # 12 POS rundown %
    pos_rundown_data = db.query(
        func.coalesce(func.sum(models.LoanRecord.disbursement_amount), 0),
        func.coalesce(func.sum(models.LoanRecord.principal_os_amt), 0)
    ).filter(
        models.LoanRecord.dataset_id == dataset_uuid,
        models.LoanRecord.disbursement_amount.isnot(None),
        models.LoanRecord.principal_os_amt.isnot(None)
    ).one()

    total_disbursement, total_pos = pos_rundown_data

    pos_rundown_pct = (
        (float(total_disbursement) - float(total_pos)) / float(total_disbursement)
        if total_disbursement > 0 else 0
    )   
    pos_rundown_pct = round(pos_rundown_pct * 100, 2)

    # 13 Invalid DPD for write-off accounts

    writeoff_dpd_invalid_count = db.query(models.LoanRecord).filter(
    models.LoanRecord.dataset_id == dataset_uuid,

    # Valid write-off definition
    models.LoanRecord.date_of_woff.isnot(None),
    models.LoanRecord.date_of_npa.isnot(None),
    models.LoanRecord.date_of_woff > models.LoanRecord.date_of_npa,

    # Invalid DPD condition
    or_(
        models.LoanRecord.dpd.is_(None),
        models.LoanRecord.dpd == 0
    )
    ).count()

    # 14 DPD Mismatch for Write-off Accounts
    writeoff_dpd_mismatch_count = db.query(models.LoanRecord).filter(
    models.LoanRecord.dataset_id == dataset_uuid,

    # Valid write-off definition
    models.LoanRecord.date_of_woff.isnot(None),
    models.LoanRecord.date_of_npa.isnot(None),
    models.LoanRecord.date_of_woff > models.LoanRecord.date_of_npa,

    # DPD mismatch condition
    or_(
        models.LoanRecord.dpd.is_(None),
        models.LoanRecord.dpd < 90
    )
    ).count()

    # 15 EMI paid vs COllection mismatch
    emi_paid_collection_mismatch_count = 0

    records = db.query(models.LoanRecord).filter(
    models.LoanRecord.dataset_id == dataset_uuid,
    models.LoanRecord.emi_amount.isnot(None),
    models.LoanRecord.emi_amount > 0,
    models.LoanRecord.emi_paid_months.isnot(None),
    models.LoanRecord.total_collection_since_inception.isnot(None)
    ).all()

    for r in records:
        expected_emi_paid = float(r.total_collection_since_inception) / float(r.emi_amount)

        if abs(expected_emi_paid - float(r.emi_paid_months)) > 1:
            emi_paid_collection_mismatch_count += 1

    # 15 tenor months mismatch
    tenor_mismatch_count = 0

    records = db.query(models.LoanRecord).filter(
        models.LoanRecord.dataset_id == dataset_uuid,
        models.LoanRecord.emi_paid_months.isnot(None),
        models.LoanRecord.balance_tenor_months.isnot(None),
        models.LoanRecord.current_tenor_months.isnot(None)
    ).all()

    for r in records:
        if abs(
            (r.emi_paid_months + r.balance_tenor_months)
            - r.current_tenor_months
        ) > 1:
            tenor_mismatch_count += 1

    # 16 Calculated EMI = Stored EMI -- emi calculator mismatch count
    emi_calculator_mismatch_count = 0

    rows = db.query(models.LoanRecord).filter(
    models.LoanRecord.dataset_id == dataset_uuid,
    models.LoanRecord.disbursement_amount.isnot(None),
    models.LoanRecord.emi_amount.isnot(None),
    models.LoanRecord.original_tenor_months.isnot(None),
    models.LoanRecord.original_tenor_months > 0,
    models.LoanRecord.roi_at_booking.isnot(None)
    ).all()

    for r in rows:
        try:
            P = float(r.disbursement_amount)
            emi_actual = float(r.emi_amount)
            n = int(r.original_tenor_months)
            annual_roi = float(r.roi_at_booking)

            if P <= 0 or emi_actual <= 0 or n <= 0 or annual_roi <= 0:
                continue

            r_monthly = annual_roi / 12 / 100

            emi_calculated = (
                P * r_monthly * (1 + r_monthly) ** n
            ) / ((1 + r_monthly) ** n - 1)

            deviation_pct = abs(emi_calculated - emi_actual) / emi_actual * 100

            if deviation_pct > 2:
                emi_calculator_mismatch_count += 1

        except Exception:
            continue

    # Helper Function to normalize the dates

    def normalize_date(val):
        # 1️⃣ Empty / missing
        if val is None:
            return None

        # 2️⃣ Already a date (but not datetime)
        if isinstance(val, date) and not isinstance(val, datetime):
            return val

        # 3️⃣ datetime → date
        if isinstance(val, datetime):
            return val.date()

        # 4️⃣ Pandas Timestamp → date
        if isinstance(val, pd.Timestamp):
            return val.date()

        # 5️⃣ Excel serial number → date
        if isinstance(val, (int, float)):
            try:
                return pd.to_datetime(
                    val,
                    unit="D",
                    origin="1899-12-30"
                ).date()
            except Exception:
                return None

        # 6️⃣ String → date
        if isinstance(val, str):
            try:
                # dayfirst=True handles Indian / Excel formats safely
                return pd.to_datetime(val, dayfirst=True).date()
            except Exception:
                return None

        # 7️⃣ Anything else → invalid
        return None


    # 17 DPD 36M vs NPA date mismatch count
    dpd36m_npa_mismatch_count = 0

    rows = db.query(models.LoanRecord).filter(
            models.LoanRecord.dataset_id == dataset_uuid,
            models.LoanRecord.date_of_npa.isnot(None),
            models.LoanRecord.additional_fields.isnot(None)
        ).all()

    for r in rows:
        try:
            # dpd_fields = r.additional_fields.get("dpd36m")
            inferred_npa = infer_npa_from_dpd36m(r.additional_fields)

            # inferred_npa = infer_npa_from_dpd36m(r.additional_fields)

            if not inferred_npa:
                continue

            # actual_npa = r.date_of_npa
            actual_npa = normalize_date(r.date_of_npa)

            if not actual_npa:
                continue

            delta_days = abs((actual_npa - inferred_npa).days)

            if delta_days > DPD36M_TOLERANCE_DAYS:
                dpd36m_npa_mismatch_count += 1

            # print("DPD36M keys:", r.additional_fields.keys())
            # print("Inferred NPA:", inferred_npa, "Actual:", r.date_of_npa)


        except Exception:
            continue




    return [
        {"id": "dpd_gt_0", "name": "DPD should be more than 0 days", "failed_count": dpd_gt_0},
        {"id": "pos_lt_disbursement", "name": "POS > DIS", "failed_count": pos_lt_disbursement},
        {"id": "pos_gt_dis", "name": "POS < DIS", "failed_count": pos_gt_dis},
        {"id": "date_format", "name": "Date format dd/mm/yyyy(checks if dates are null or <2000)", "failed_count": date_format},
        {"id": "duplicate_loan_no", "name": "No duplicate Loan No.", "failed_count": duplicate_loan_no},
        {"id": "blank_required_fields", "name": "No blank required fields", "failed_count": blank_required_fields},
        {"id": "min_pos_amount", "name": "Check minimum POS Amount (< Rs 1000)", "failed_count": min_pos_amount},
        {"id": "tos_calc", "name": "Check Total Outstanding (TOS) Calculation(POS + Int. overdue) ", "failed_count": tos_calc},
        {"id": "negative_collections", "name": "Collections of negative amounts", "failed_count": negative_collections},
        {"id": "npa_le_woff","name": "NPA Date less than Write-off Date","failed_count": npa_date_le_woff_date},
        {"id": "average_ticket_size","name": "Average Ticket Size","failed_count": average_ticket_size},
        {"id": "POS rundown %","name": "POS rundown %","failed_count": f"{pos_rundown_pct}%"},
        {"id": "writeoff_dpd_invalid_count","name": "Invalid DPD for write-off accounts","failed_count": writeoff_dpd_invalid_count},
        {"id": "writeoff_dpd_mismatch_count","name": "DPD Mismatch for Write-off Accounts","failed_count": writeoff_dpd_mismatch_count},
        {"id": "emi_paid_collection_mismatch_count","name": "EMI Paid mismatch with Total Collection","failed_count": emi_paid_collection_mismatch_count},
        {"id": "tenor_mismatch_count","name": "Tenor Months Mismatch Count (EMI paid + Tenor = Current)","failed_count": tenor_mismatch_count},
        {"id": "emi_calculator_mismatch_count","name": "EMI calulated vs EMI stored mismatch","failed_count": emi_calculator_mismatch_count},
        {"id": "dpd36m_npa_mismatch_count","name": "DPD 36M vs NPA date mismatch","failed_count": dpd36m_npa_mismatch_count}

       ]

@router.get("/{dataset_id}/validation-errors/{validation_id}")
def get_validation_errors(dataset_id: str, validation_id: str, db: Session = Depends(get_db)):
    try:
        dataset_uuid = UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")

    query = db.query(models.LoanRecord).filter(models.LoanRecord.dataset_id == dataset_uuid)

    if validation_id == "dpd_gt_0":
        query = query.filter(or_(
            models.LoanRecord.dpd_as_on_31st_jan_2025 <= 0,
            models.LoanRecord.dpd_as_on_31st_jan_2025 == None
        ))
    elif validation_id == "pos_lt_disbursement":
    	#Added by jainil, merged hvb @ 15/12/2025
        # query = query.filter(models.LoanRecord.principal_os_amt >= models.LoanRecord.disbursement_amount)
        # <=
        query = query.filter(models.LoanRecord.principal_os_amt <= models.LoanRecord.disbursement_amount)
    elif validation_id == "pos_gt_dis":
        #Added by jainil, merged hvb @ 15/12/2025
        #query = query.filter(models.LoanRecord.principal_os_amt <= models.LoanRecord.disbursement_amount)
        query = query.filter(models.LoanRecord.principal_os_amt > models.LoanRecord.disbursement_amount)
    elif validation_id == "date_format":
        query = query.filter(or_(
        	#Added by jainil, merged hvb @ 15/12/2025
            #models.LoanRecord.first_disb_date == None,
            #models.LoanRecord.sanction_date == None
            models.LoanRecord.last_disb_date.is_(None),
            models.LoanRecord.sanction_date.is_(None),
            models.LoanRecord.date_of_npa.is_(None),
            models.LoanRecord.date_of_woff.is_(None),

            # Year < 2000 checks
            extract('year', models.LoanRecord.last_disb_date) < 2000,
            extract('year', models.LoanRecord.sanction_date) < 2000,
            extract('year', models.LoanRecord.date_of_npa) < 2000,
            extract('year', models.LoanRecord.date_of_woff) < 2000,
        ))
    elif validation_id == "duplicate_loan_no":
        dupes = db.query(models.LoanRecord.agreement_no).filter(
            models.LoanRecord.dataset_id == dataset_uuid
        ).group_by(models.LoanRecord.agreement_no).having(func.count(models.LoanRecord.agreement_no) > 1).all()
        dupe_nos = [d[0] for d in dupes]
        query = query.filter(models.LoanRecord.agreement_no.in_(dupe_nos))
    elif validation_id == "blank_required_fields":
        query = query.filter(or_(
            models.LoanRecord.agreement_no == None,
            models.LoanRecord.dpd_as_on_31st_jan_2025 == None,
            models.LoanRecord.principal_os_amt == None
        ))
    elif validation_id == "min_pos_amount":
        query = query.filter(models.LoanRecord.principal_os_amt < 1000)
    elif validation_id == "tos_calc":
        query = query.filter(models.LoanRecord.total_balance_amt != (models.LoanRecord.principal_os_amt + models.LoanRecord.interest_overdue_amt))
    elif validation_id == "negative_collections":
        query = query.filter(or_(
            models.LoanRecord.total_collection < 0,
            models.LoanRecord.m3_collection < 0,
            models.LoanRecord.m6_collection < 0,
            models.LoanRecord.m12_collection < 0
        ))
    #added by jainil on 21-12-25
    elif validation_id == "npa_le_woff":
        query = query.filter(
            or_(
            models.LoanRecord.date_of_npa.is_(None),
            models.LoanRecord.date_of_woff.is_(None),
            models.LoanRecord.date_of_npa >= models.LoanRecord.date_of_woff
        )
        )
    
    elif validation_id in ("average_ticket_size", "pos_rundown_pct"):
        return []
    
    elif validation_id == "writeoff_dpd_invalid_count":
        from datetime import date

        CUTOFF_DATE = date(2025, 1, 31)
        records = []

        rows = db.query(models.LoanRecord).filter(
            models.LoanRecord.dataset_id == dataset_uuid,
            models.LoanRecord.date_of_woff.isnot(None),
            models.LoanRecord.date_of_npa.isnot(None),
            models.LoanRecord.date_of_woff > models.LoanRecord.date_of_npa,
            or_(
                models.LoanRecord.dpd.is_(None),
                models.LoanRecord.dpd == 0
            )
        ).all()

        for r in rows:
            derived_dpd = "NA"

            # Check if derived DPD can be calculated
            if (
                r.emi_amount is not None and r.emi_amount > 0
                and r.post_npa_collection is not None
                and r.date_of_npa is not None
                #and CUTOFF_DATE <= r.date_of_npa
            ):
                try:
                    G = (float(r.post_npa_collection) / float(r.emi_amount)) * 30
                    days_diff = (CUTOFF_DATE - r.date_of_npa).days
                    derived_dpd = round(days_diff + 90 - G, 2)
                except Exception:
                    derived_dpd = "NA"

            records.append({
                "Loan No.": r.agreement_no,
                "Reported DPD": r.dpd,
                "Derived DPD": derived_dpd,
                "Post NPA Collection": r.post_npa_collection,
                "EMI Amount": r.emi_amount,
                "NPA Date": r.date_of_npa,
                "Write-off Date": r.date_of_woff,
                "Cutoff Date": CUTOFF_DATE,
                "Classification": r.classification,
            })

        return records

    elif validation_id == "writeoff_dpd_mismatch_count":
        query = query.filter(
            models.LoanRecord.date_of_woff.isnot(None),
            models.LoanRecord.date_of_npa.isnot(None),
            models.LoanRecord.date_of_woff > models.LoanRecord.date_of_npa,
            or_(
                models.LoanRecord.dpd.is_(None),
                models.LoanRecord.dpd < 90
            )
        )

    elif validation_id == "emi_paid_collection_mismatch_count":
        records = []

        rows = db.query(models.LoanRecord).filter(
            models.LoanRecord.dataset_id == dataset_uuid,
            models.LoanRecord.emi_amount.isnot(None),
            models.LoanRecord.emi_amount > 0,
            models.LoanRecord.emi_paid_months.isnot(None),
            models.LoanRecord.total_collection_since_inception.isnot(None)
        ).all()

        for r in rows:
            expected_emi_paid = float(r.total_collection_since_inception) / float(r.emi_amount)

            if abs(expected_emi_paid - float(r.emi_paid_months)) > 1:
                records.append(r)

        return [
            {
                "Loan No.": r.agreement_no,
                "Classification": r.classification,
                "DPD": r.dpd_as_on_31st_jan_2025,

                # EMI math
                "EMI Amount": r.emi_amount,
                "EMI Paid (Stored)": r.emi_paid_months,
                "EMI Paid (Expected)": round(
                    float(r.total_collection_since_inception) / float(r.emi_amount), 2
                ),
                "EMI Delta (Months)": round(
                    (float(r.total_collection_since_inception) / float(r.emi_amount))
                    - float(r.emi_paid_months),
                    2
                ),

                # Money context
                "Total Collection (Since Inception)": r.total_collection_since_inception,
                "Principal O/S": r.principal_os_amt,
                "Disbursement Amount": getattr(r, "disbursement_amount", None),

                # Dates
                "NPA Date": fmt(r.date_of_npa),
                "Write-off Date": fmt(r.date_of_woff),
            }
            for r in records
        ]
    
    elif validation_id == "tenor_mismatch_count":
        records = []

        rows = db.query(models.LoanRecord).filter(
            models.LoanRecord.dataset_id == dataset_uuid,
            models.LoanRecord.emi_paid_months.isnot(None),
            models.LoanRecord.balance_tenor_months.isnot(None),
            models.LoanRecord.current_tenor_months.isnot(None)
        ).all()

        for r in rows:
            if abs(
                (r.emi_paid_months + r.balance_tenor_months)
                - r.current_tenor_months
            ) > 1:
                records.append(r)

        return [
            {
                "Loan No.": r.agreement_no,
                "Classification": r.classification,
                "DPD": r.dpd_as_on_31st_jan_2025,

                # Tenor logic
                "EMI Paid (Months)": r.emi_paid_months,
                "Balance Tenor (Months)": r.balance_tenor_months,
                "Current Tenor (Months)": r.current_tenor_months,
                "Calculated Tenor (Paid + Balance)": (
                    r.emi_paid_months + r.balance_tenor_months
                    if r.emi_paid_months is not None and r.balance_tenor_months is not None
                    else None
                ),
                "Tenor Delta (Months)": (
                    (r.emi_paid_months + r.balance_tenor_months) - r.current_tenor_months
                    if r.emi_paid_months is not None
                    and r.balance_tenor_months is not None
                    and r.current_tenor_months is not None
                    else None
                ),

                # EMI & money context
                "EMI Amount": r.emi_amount,
                "Total Collection": r.total_collection,
                "Principal O/S": r.principal_os_amt,
                "Disbursement Amount": getattr(r, "disbursement_amount", None),

                # Dates
                "NPA Date": fmt(r.date_of_npa),
                "Write-off Date": fmt(r.date_of_woff),
            }
            for r in records
        ]




    elif validation_id == "emi_calculator_mismatch_count":
        records = []

        rows = db.query(models.LoanRecord).filter(
            models.LoanRecord.dataset_id == dataset_uuid,
            models.LoanRecord.disbursement_amount.isnot(None),
            models.LoanRecord.emi_amount.isnot(None),
            models.LoanRecord.original_tenor_months.isnot(None),
            models.LoanRecord.original_tenor_months > 0,
            models.LoanRecord.roi_at_booking.isnot(None)
        ).all()

        for r in rows:
            try:
                P = float(r.disbursement_amount)
                emi_actual = float(r.emi_amount)
                n = int(r.original_tenor_months)
                annual_roi = float(r.roi_at_booking)

                if P <= 0 or emi_actual <= 0 or n <= 0 or annual_roi <= 0:
                    continue

                r_monthly = annual_roi / 12 / 100

                emi_calculated = (
                    P * r_monthly * (1 + r_monthly) ** n
                ) / ((1 + r_monthly) ** n - 1)

                deviation_pct = abs(emi_calculated - emi_actual) / emi_actual * 100

                if deviation_pct > 2:
                    records.append((r, emi_calculated, deviation_pct))


            except Exception:
                continue

        return [
            {
                "Loan No.": r.agreement_no,
                "DPD": r.dpd_as_on_31st_jan_2025,
                "Principal O/S": r.principal_os_amt,
                "Disbursement": r.disbursement_amount,
                "EMI Amount": r.emi_amount,
                "Calculated EMI": round(emi_calculated, 2),
                "Deviation (%)": round(deviation_pct, 2),
                "Total Collection": r.total_collection,
                "Tenor (Months)": r.original_tenor_months,
                "ROI": r.roi_at_booking,
                "Classification": r.classification,
            }
            for r, emi_calculated, deviation_pct in records
        ]
    
    elif validation_id == "dpd36m_npa_mismatch_count":
        records = []

        rows = db.query(models.LoanRecord).filter(
            models.LoanRecord.dataset_id == dataset_uuid,
            models.LoanRecord.date_of_npa.isnot(None),
            models.LoanRecord.additional_fields.isnot(None)
        ).all()

        for r in rows:
            try:
                inferred_npa = infer_npa_from_dpd36m(r.additional_fields)

                if not inferred_npa:
                    continue

                actual_npa = r.date_of_npa
                delta_days = abs((actual_npa - inferred_npa).days)

                if delta_days > DPD36M_TOLERANCE_DAYS:
                    records.append((r, inferred_npa, delta_days))

            except Exception:
                continue

        return [
            {
                "Loan No.": r.agreement_no,
                "DPD (Latest)": r.dpd,
                "Inferred NPA (from DPD36M)": fmt(inferred_npa),
                "Actual NPA Date": fmt(r.date_of_npa),
                "Delta (Days)": delta_days,
                "Classification": r.classification,
                "State": r.state
            }
            for r, inferred_npa, delta_days in records
        ]


       
    else:
        return []

    records = query.all()

    # added by jainil- NPA date and Writeoff date
    return [
        {
            "Loan No.": r.agreement_no,
            "DPD": r.dpd_as_on_31st_jan_2025,
            "Principal O/S": r.principal_os_amt,
            "Disbursement": getattr(r, 'disbursement_amount', None),
            "NPA Date": fmt(r.date_of_npa),
            "Write-off Date": fmt(r.date_of_woff),
            "Classification": r.classification,
        }
        for r in records
    ]