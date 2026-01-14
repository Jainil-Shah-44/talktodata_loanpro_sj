# services/mapping_config_builder.py

from sqlalchemy.orm import Session
from app.models.upload_profile import (
    MappingProfile, MappingSheet, SheetExtraColumn,
    SheetCleanup, SheetColumnMapping, SheetRelation
)

# NOTE:
# SheetExtraColumn.source_col MUST ALWAYS be raw Excel column index
# (not relative to cols_to_read)


# ==========================================================
#  METHOD 1: Build the EXACT mapping_config for Excel upload
# ==========================================================

def get_mapping_config(db: Session, profile_id: int,attach_col_config:bool):
    profile = db.query(MappingProfile).filter(
        MappingProfile.id == profile_id,
        MappingProfile.is_active == True
    ).first()

    if not profile:
        return None

    # ----------- Sheets -----------
    sheets = db.query(MappingSheet).filter(
        MappingSheet.profile_id == profile_id
    ).all()

    sheets_dict = {}

    for sh in sheets:
        sheet_entry = {
            "header_row": sh.header_row,
            "skip_rows": sh.skip_rows,
            "cols_to_read": sh.cols_to_read,
            "alias": sh.sheet_alias,
            "key_columns": sh.key_columns or []
        }

        # ---- extra ----
        extras = db.query(SheetExtraColumn).filter(
            SheetExtraColumn.sheet_id == sh.id
        ).all()

        if extras:
            #sheet_entry["extra"] = [{ex.source_col: ex.target_name} for ex in extras]
            #added by Jainil @ 13/1/26 --
            sheet_entry["timeseries"] = [
                    {
                        "source_col": ex.source_col,
                        "target_name": ex.target_name
                    }
                    for ex in extras
                ]
            
        # ---- cleanup ----
        cleanup_obj = db.query(SheetCleanup).filter(
            SheetCleanup.sheet_id == sh.id
        ).first()

        if cleanup_obj:
            # example -> [{7:"dt"},{8:"int"}]
            sheet_entry["clean_columns"] = [
                {rule["col"]: rule["type"]} for rule in cleanup_obj.rules
            ]

        sheets_dict[sh.sheet_index] = sheet_entry

    # ----------- Relations -----------
    relations_raw = db.query(SheetRelation).filter(
        SheetRelation.profile_id == profile_id
    ).all()

    relations_list = [
        {
            "left": r.left_sheet,
            "right": r.right_sheet,
            "left_col": r.left_col,
            "right_col": r.right_col,
            "how": r.how,
        }
        for r in relations_raw
    ]

    # ----------- Column Mappings (multi-target) -----------
    if attach_col_config:
        column_mappings_raw = db.query(SheetColumnMapping).filter(
            SheetColumnMapping.profile_id == profile_id
        ).all()

        # {"_Pool_col_13": ["dpd_as_per_string", "dpd"]}
        column_mapping = {}
        for m in column_mappings_raw:
            if m.source_col not in column_mapping:
                column_mapping[m.source_col] = []
            column_mapping[m.source_col].append(m.target_column)

        result = {
            "sheets": sheets_dict,
            "relations": relations_list,
            "column_mapping": column_mapping
        }
    else:
        result = {
            "sheets": sheets_dict,
            "relations": relations_list
        }

    return result


# ==========================================================
#  METHOD 2: Build database_config for inserting into postgres
# ==========================================================

def get_database_config(db: Session, profile_id: int):
    """
    Convert column mapping into database_config format:

    Example Output:
    {
        "_Pool_col_0": "agreement_no",
        "_Pool_col_7": "product_type_skc",
        "_Pool_col_9": "principal_os_amt",
        "_Pool_col_13": ["dpd_as_per_string", "dpd"]
    }
    """

    rows = db.query(SheetColumnMapping).filter(
        SheetColumnMapping.profile_id == profile_id
    ).all()

    db_config = {}

    for m in rows:
        src = m.source_col

        # single or multiple targets
        if src not in db_config:
            db_config[src] = m.target_column
        else:
            # already present -> convert to list (multi-target)
            if isinstance(db_config[src], str):
                db_config[src] = [db_config[src], m.target_column]
            else:
                db_config[src].append(m.target_column)

    # commented by Jainil @9-1-25
    # ✅ ALWAYS map extras into additional_fields

    # Added by Jainil @ 13/1/26
    #db_config["extra_data_json"] = "additional_fields"
    db_config["additional_fields"] = "additional_fields"
    db_config.update({
        "post_npa_collection": "post_npa_collection",
        "post_woff_collection": "post_woff_collection",
        "m6_collection": "m6_collection",
        "m12_collection": "m12_collection",
        "total_collection": "total_collection",
    })


    return db_config


#
def get_mapping_type(db: Session, profile_id: int):
    profile = db.query(MappingProfile).filter(
        MappingProfile.id == profile_id,
        MappingProfile.is_active == True
    ).first()
    if not profile:
        return None
    return  profile.file_type

# ==========================================================
#  METHOD 3: Combined Output (you requested)
# ==========================================================

def get_full_profile_config(db: Session, profile_id: int):
    mapping_config = get_mapping_config(db, profile_id,False)
    database_config = get_database_config(db, profile_id)

    if not mapping_config:
        return None

    underlying_file_type = get_mapping_type(db, profile_id)

    return {
        "mapping_config": mapping_config,
        "database_config": database_config,
        "underlying_file_type": underlying_file_type
    }

