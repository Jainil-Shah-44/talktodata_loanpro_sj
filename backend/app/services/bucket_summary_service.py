# app/services/bucket_summary_service.py
from typing import Dict, Any, List

from fastapi import HTTPException
from pandas.core.computation.expressions import where
from sqlalchemy import case, func, select, Float, and_, text, cast, Text
#from sqlalchemy.databases import postgresql
from sqlalchemy.orm import Session
from uuid import UUID

from app.curd.crud import dataset_crud
from app.models import models
from app.models.FilterCriteriaItem import FilterCriteriaItem
from app.models.bucket_config import BucketConfig
from app.models.models import LoanRecord, Dataset
from app.schemas.schemas import ColumnInfo

PG_TYPE_MAP = {
    "string": "str",
    "number": "float",
    "boolean": "bool",
    "null": "None",
    "object": "dict",
    "array": "list"
}

#async def apply_filters(query, filter_criteria: Dict[str, Any] = None):
async def apply_filters(query, filter_criteria: List[FilterCriteriaItem] = None):
    """Replace with your existing filtering logic."""
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

    return query


def build_bucket_case(col, rules):
    """Supports both numeric and string bucket configs."""

    # detect bucket type
    string_mode = "values" in rules[0]

    whens = []

    if string_mode:
        # ✅ NEW — dynamic grouping case
        if any(r.get("values") == ["ALL"] for r in rules):
            # return raw column so DB groups by all unique values
            return col

        # existing explicit string bucket logic
        whens = [
            (col.in_(r["values"]), r["label"])
            for r in rules if r["values"]
        ]

        else_label = next(
            (r["label"] for r in rules if not r["values"]),
            "Others"
        )

        return case(*whens, else_=else_label)

    else:
        # mod hvb as this fails 3 cases 1. BLANK (NULL) values bucket,
        # 2. NEGATIVE values bucket (max < 0), 3. Open-ended upper range (max is null)

        # numeric min/max boundaries
        # whens = [
        #     (and_(col >= r["min"], col < r["max"]), r["label"])
        #     for r in rules
        # ]
        #
        # return case(*whens, else_="Others")

        whens = []

        for r in rules:
            min_v = r.get("min")
            max_v = r.get("max")

            # 1) BLANK (NULL) values bucket
            if min_v is None and max_v is None:
                whens.append((col.is_(None), r["label"]))
                continue

            # 2) NEGATIVE values bucket (max < 0)
            if min_v is None and isinstance(max_v, (int, float)) and max_v < 0:
                whens.append((col < 0, r["label"]))
                continue

            # 3) Open-ended upper range (max is null)
            if max_v is None and isinstance(min_v, (int, float)):
                whens.append((col >= min_v, r["label"]))
                continue

            # 4) Normal range bucket
            if min_v is not None and max_v is not None:
                if min_v == max_v: # for case 0 to 0
                    whens.append((col == min_v, r["label"]))
                else:
                    #this logic doesn't work like b/w.
                    #However it was written w.r.to existing logic by Rajesh sir.
                    #But this is generating mismatch in bucket
                    #So modified hvb @ 28/11/2025
                    #whens.append((and_(col >= min_v, col < max_v), r["label"]))
                    whens.append((and_(col >= min_v, col <= max_v), r["label"]))
                continue

        return case(*whens, else_="Others")


# mod hvb @ 08/12/2025 for merging filter-criteria
# async def get_bucket_summary(db, config, filters: Dict[str, Any],dataset_uuid:UUID,create_empty_buckets: bool):
async def get_bucket_summary(db, config, filters: List[FilterCriteriaItem], dataset_uuid: UUID, create_empty_buckets: bool):
    """Generate bucket summary for one config."""

    print("\n\n====** STARTING CONFIG-ED SUMMARY GENERATION ====\n")

    # Check if dataset exists
    dataset = dataset_crud.get_dataset(db, dataset_uuid)
    if not dataset:
        print(f"Dataset not found: {dataset_uuid}")
        raise HTTPException(status_code=404, detail="Dataset not found")
    else:
        print(f"Found dataset: {dataset.name}, records: {dataset.total_records}")

    # Get loan records for this dataset, applying filters if provided
    base_q = db.query(models.LoanRecord).filter(
        models.LoanRecord.dataset_id == dataset_uuid
    )

    #base_q = db.query(Loan)

    base_q = await apply_filters(base_q, filters)
    filtered_cte = base_q.cte("filtered")

    # choose JSON or normal column
    if config.target_field_is_json:
        # col = func.cast(filtered_cte.c.additional_fields[config.target_field].astext, func.text)
        col_raw = filtered_cte.c.additional_fields[config.target_field].astext

        # detect bucket type
        string_mode = "values" in config.bucket_config[0]
        if not string_mode:
            col = cast(col_raw, Float)   # numeric grouping
        else:
            col = cast(col_raw, Text)  # string grouping
    else:
        # mod hvb @ 28/11/2025 as its not printing records with 0 rows
        col = getattr(filtered_cte.c, config.target_field)
        # error, not generating desire output.
        # col_raw = getattr(filtered_cte.c, config.target_field)
        #
        # col = case(
        #     (col_raw.is_(None), "0"),  # string 0
        #     else_=col_raw  # string column
        # ).cast(Float)

    case_expr = build_bucket_case(col, config.bucket_config).label("bucket")

    stmt = (
        select(
            case_expr,
            func.count().label("count"),
            #func.sum(filtered_cte.c.amount).label("sum_amount"),

            func.sum(filtered_cte.c.principal_os_amt).label("POS"),
            func.sum(filtered_cte.c.post_npa_collection).label("Post_NPA_Coll"),
            func.sum(filtered_cte.c.post_woff_collection).label("Post_W_Off_Coll"),

            func.sum(filtered_cte.c.m6_collection).label("M6_Collection"),
            func.sum(filtered_cte.c.m12_collection).label("M12_Collection"),
            func.sum(filtered_cte.c.total_collection).label("total_collection")
        )
        .select_from(filtered_cte)
        .group_by(case_expr)
        .order_by(case_expr)
    )

    #Uncomment to print statement
    # print(stmt.compile(
    #     dialect=postgresql.dialect(),
    #     compile_kwargs={"literal_binds": True}
    # ))

    rows = db.execute(stmt).fetchall()
    # Map SQL rows by label
    rows_by_label = {r.bucket: r for r in rows}
    #found_labels = set(rows_by_label.keys())

    # mod hvb for missing buckets with 0 rows
    # initialize totals
    totals = {
        "count": 0,
        "POS": 0,
        "Post_NPA_Coll": 0,
        "Post_W_Off_Coll": 0,
        "M6_Collection": 0,
        "M12_Collection": 0,
        "total_collection": 0,
    }

    # accumulate
    for r in rows:

        totals["count"] += r.count or 0
        totals["POS"] += r.POS or 0
        totals["Post_NPA_Coll"] += r.Post_NPA_Coll or 0
        totals["Post_W_Off_Coll"] += r.Post_W_Off_Coll or 0
        totals["M6_Collection"] += r.M6_Collection or 0
        totals["M12_Collection"] += r.M12_Collection or 0
        totals["total_collection"] += r.total_collection or 0

    summary_rows = []

    shall_create_empty_buckets = False
    if create_empty_buckets == True and (not (any(r.get("values") == ["ALL"] for r in config.bucket_config) )):
        shall_create_empty_buckets = True

    if shall_create_empty_buckets:
        # 🚀 Build rows in EXACT CONFIG ORDER (fixes sequencing)
        config_label_set = set()

        for rule in config.bucket_config:
            label = rule["label"]
            r = rows_by_label.get(label)

            config_label_set.add(label)  # <-- TRACK configured labels

            if r is None:
                # bucket missing → inject zero bucket
                summary_rows.append({
                    "label": label,
                    "count": 0,
                    "POS": 0,
                    "POS_Per": 0,
                    "Post_NPA_Coll": 0,
                    "Post_W_Off_Coll": 0,
                    "M6_Collection": 0,
                    "M12_Collection": 0,
                    "total_collection": 0,
                })
            else:
                pos_val = r.POS or 0
                pos_percent = (pos_val / totals["POS"] * 100) if totals["POS"] else 0

                summary_rows.append({
                    "label": label,
                    "count": r.count,
                    "POS": pos_val,
                    "POS_Per": round(pos_percent, 2),
                    "Post_NPA_Coll": r.Post_NPA_Coll,
                    "Post_W_Off_Coll": r.Post_W_Off_Coll,
                    "M6_Collection": r.M6_Collection,
                    "M12_Collection": r.M12_Collection,
                    "total_collection": r.total_collection,
                })
        # check missed bucket in rows
        # and add it
        for r in rows:
            if r.bucket not in config_label_set:
                pos_val = r.POS or 0
                pos_percent = (pos_val / totals["POS"] * 100) if totals["POS"] else 0

                summary_rows.append({
                    "label": r.bucket,
                    "count": r.count or 0,
                    "POS": pos_val,
                    "POS_Per": round(pos_percent, 2),
                    "Post_NPA_Coll": r.Post_NPA_Coll or 0,
                    "Post_W_Off_Coll": r.Post_W_Off_Coll or 0,
                    "M6_Collection": r.M6_Collection or 0,
                    "M12_Collection": r.M12_Collection or 0,
                    "total_collection": r.total_collection or 0,
                })
    else:
        for r in rows:
            pos_percent = (
                (r.POS / totals["POS"] * 100)
                if totals["POS"] else 0
            )

            summary_rows.append(
                {
                    "label": r.bucket,
                    "count": r.count,
                    "POS": r.POS,
                    "POS_Per": round(pos_percent, 2),
                    "Post_NPA_Coll": r.Post_NPA_Coll,
                    "Post_W_Off_Coll": r.Post_W_Off_Coll,
                    "M6_Collection": r.M6_Collection,
                    "M12_Collection": r.M12_Collection,
                    "total_collection": r.total_collection,
                }
            )

    # ✅ Append total row ONLY ONCE
    summary_rows.append(
        {
            "label": "Total",
            **totals,
            "POS_Per": 100.0,
        }
    )

    return {
        "id": config.id,
        "name": config.name,
        "summary_type": config.summary_type,
        "buckets": summary_rows  # already contains rows + Total
    }
    # # Build a mapping from label -> sql row
    # rows_by_label = {r.bucket: r for r in rows}
    #
    # # Initialize totals
    # totals = {
    #     "count": 0,
    #     "POS": 0,
    #     "Post_NPA_Coll": 0,
    #     "Post_W_Off_Coll": 0,
    #     "M6_Collection": 0,
    #     "M12_Collection": 0,
    #     "total_collection": 0,
    # }
    #
    # # Accumulate totals only from rows returned by SQL
    # for r in rows:
    #     totals["count"] += r.count or 0
    #     totals["POS"] += r.POS or 0
    #     totals["Post_NPA_Coll"] += r.Post_NPA_Coll or 0
    #     totals["Post_W_Off_Coll"] += r.Post_W_Off_Coll or 0
    #     totals["M6_Collection"] += r.M6_Collection or 0
    #     totals["M12_Collection"] += r.M12_Collection or 0
    #     totals["total_collection"] += r.total_collection or 0
    #
    # summary_rows = []
    #
    # # 🚀 NEW: loop through bucket_config rules, not SQL rows
    # for rule in config.bucket_config:
    #     label = rule.get("label")
    #     r = rows_by_label.get(label)
    #
    #     if r is None:
    #         # Inject zero bucket
    #         pos_val = 0
    #         post_npa = 0
    #         post_woff = 0
    #         m6 = 0
    #         m12 = 0
    #         total_coll = 0
    #         cnt = 0
    #     else:
    #         pos_val = r.POS or 0
    #         post_npa = r.Post_NPA_Coll or 0
    #         post_woff = r.Post_W_Off_Coll or 0
    #         m6 = r.M6_Collection or 0
    #         m12 = r.M12_Collection or 0
    #         total_coll = r.total_collection or 0
    #         cnt = r.count or 0
    #
    #     # Compute POS_Per
    #     pos_percent = (pos_val / totals["POS"] * 100) if totals["POS"] else 0
    #
    #     summary_rows.append({
    #         "label": label,
    #         "count": cnt,
    #         "POS": pos_val,
    #         "POS_Per": round(pos_percent, 2),
    #         "Post_NPA_Coll": post_npa,
    #         "Post_W_Off_Coll": post_woff,
    #         "M6_Collection": m6,
    #         "M12_Collection": m12,
    #         "total_collection": total_coll,
    #     })
    #
    # # Append Total row
    # summary_rows.append({
    #     "label": "Total",
    #     **totals,
    #     "POS_Per": 100.0 if totals["POS"] else 0.0,
    # })
    #
    # return {
    #     "id": config.id,
    #     "name": config.name,
    #     "summary_type": config.summary_type,
    #     "buckets": summary_rows
    # }

def get_configs(db,user_id,dataset_id:str) -> List[BucketConfig]:
    """
       Returns a list of *effective* bucket configs for the dataset,
       respecting override rules:
           dataset+user → dataset+default → global default
       """

    # Step 0 - check for dataset file-type and map that with summary-type
    file_type = db.query(Dataset).where(Dataset.id == dataset_id).first().file_type
    if not file_type:
        file_type = "--BLANK--"

    # Step 1 — get all configs for this dataset
    dataset_configs = (
        db.query(BucketConfig)
        .filter(BucketConfig.dataset_id == dataset_id)
        .order_by(BucketConfig.sort_order)  # ascending
        .all()
    )

    # Group by summary type
    grouped: Dict[str, List[BucketConfig]] = {}
    for cfg in dataset_configs:
        #group by target field
        #grouped.setdefault(cfg.summary_type, []).append(cfg)
        grouped.setdefault(cfg.target_field, []).append(cfg)

    # Step 2 — also load global defaults (dataset_id NULL)
    global_defaults = (
        db.query(BucketConfig)
        .filter(
            BucketConfig.dataset_id.is_(None),
            BucketConfig.is_default.is_(True),
            BucketConfig.summary_type == file_type # added hvb @ 03/12/2025
        )
        .order_by(BucketConfig.sort_order)  # ascending
        .all()
    )
    # group by target field
    #global_by_type = {cfg.summary_type: cfg for cfg in global_defaults}
    global_by_type = {cfg.target_field: cfg for cfg in global_defaults}

    effective_configs: List[BucketConfig] = []

    # Step 3 — resolve for each summary type
    #use target field
    #for summary_type, cfg_list in grouped.items():
    for target_field, cfg_list in grouped.items():

        # (A) dataset + user configs
        user_specific = [c for c in cfg_list if c.user_id == user_id]
        if user_specific:
            effective_configs.extend(user_specific)
            continue

        # (B) dataset defaults
        dataset_defaults = [c for c in cfg_list if c.is_default]
        if dataset_defaults:
            effective_configs.extend(dataset_defaults)
            continue

        # (C) global default fallback
        # target_type
        #if summary_type in global_by_type:
        if target_field in global_by_type:
            effective_configs.append(global_by_type[target_field])

    # Step 4 — also add global defaults for summary types NOT present in dataset configs
    #for summary_type, default_cfg in global_by_type.items():
    for target_field, default_cfg in global_by_type.items():
        if target_field not in grouped:
            effective_configs.append(default_cfg)
    
    effective_configs.sort(
    key=lambda c: (c.sort_order is None, c.sort_order)
    )


    return effective_configs



async def get_multiple_bucket_summaries(db, config_ids, config_types, filters, user_id,dataset_id:str,show_empty_buckets:bool):
    # priority: config_ids > config_types
    try:
        print("\n\n====** STARTING DATASET SUMMARY GENERATION ====\n")
        # Convert string to UUID
        try:
            dataset_uuid = UUID(dataset_id)
            print(f"***********Dataset ID converted to UUID: {dataset_uuid}")
        except ValueError:
            print(f"Invalid UUID format: {dataset_id}")
            raise HTTPException(status_code=400, detail="Invalid dataset ID format")

        if config_ids:
            configs = (
                db.query(BucketConfig)
                .filter(BucketConfig.id.in_(config_ids))
                .filter((BucketConfig.user_id == user_id) | (BucketConfig.is_default == True))
                .all()
            )
        # replaced with new logic hvb @ 27/11/2025, first lookup by dataset_id for specific config_types if not found,
        # use default one. if found use the dataset_id mapped summary_type
        # elif config_types:
        #     configs = (
        #         db.query(BucketConfig)
        #         .filter(BucketConfig.summary_type.in_(config_types))
        #         .filter((BucketConfig.user_id == user_id) | (BucketConfig.is_default == True))
        #         .all()
        #     )
        elif config_types:
            configs = []
            seen_ids = set()

            for st in config_types:
                # 1) try dataset + user specific configs for this summary_type
                dataset_configs = (
                    db.query(BucketConfig)
                    .filter(BucketConfig.summary_type == st)
                    .filter(BucketConfig.dataset_id == dataset_id)
                    .filter(BucketConfig.user_id == user_id)
                    .all()
                )

                if dataset_configs:
                    for c in dataset_configs:
                        if c.id not in seen_ids:
                            configs.append(c)
                            seen_ids.add(c.id)
                    continue  # do NOT fallback to default for this summary_type

                # 2) no dataset-specific -> fetch default configs for this summary_type
                default_configs = (
                    db.query(BucketConfig)
                    .filter(BucketConfig.summary_type == st)
                    .filter(BucketConfig.is_default == True)
                    .all()
                )

                for c in default_configs:
                    if c.id not in seen_ids:
                        configs.append(c)
                        seen_ids.add(c.id)
        else:
            raise HTTPException(status_code=400, detail="Provide config_ids or config_types")

        summaries = []
        for config in configs:
            summaries.append(await get_bucket_summary(db, config, filters,dataset_uuid,show_empty_buckets))

        return summaries
    except Exception as e:
        print(f"Error generating summary: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def get_dynamic_columns_for_id(db, id_value: int):
    sql = """
    SELECT 
        key,
        jsonb_typeof(value) AS data_type
    FROM (
        SELECT 
            jsonb_object_keys(additional_fields) AS key,
            additional_fields -> jsonb_object_keys(additional_fields) AS value
        FROM (
            SELECT additional_fields
            FROM your_table
            WHERE additional_fields IS NOT NULL
              AND pk_id = :id_variable
            LIMIT 1
        ) t1
    ) t2;
    """

    rows = db.execute(
        text(sql),
        {"id_variable": id_value}
    ).fetchall()

    dynamic_columns = [
        ColumnInfo(
            column_name=row.key,
            is_compulsory=False,
            data_type=PG_TYPE_MAP.get(row.data_type, "str")
        )
        for row in rows
    ]

    return dynamic_columns