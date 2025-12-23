from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String, Float
from app.core.database import get_db
from app.models import models
from app.schemas.fields_management import ColumnStatsRequest


router = APIRouter()

@router.post("/field-stats-loan")
# def get_column_stats(payload: ColumnStatsRequest, db: Session = Depends(get_db)):
#     table = models.LoanRecord
#
#     # Direct column vs JSON column
#     if payload.is_json_column:
#         column = table.additional_fields[payload.column_name].astext
#     else:
#         try:
#             column = getattr(table, payload.column_name)
#         except AttributeError:
#             raise HTTPException(400, f"Column {payload.column_name} not found")
#
#     # ---- CASE 1: STRING → DISTINCT VALUES ----
#     if payload.column_type == "str":
#         query = db.query(column.label("value")).distinct()
#         result = [row.value for row in query.all()]
#         return {"type": "distinct", "values": result}
#
#     # ---- CASE 2: NUMERIC → MIN & MAX ----
#     if payload.column_type in ["numeric", "float", "int"]:
#         numeric_col = cast(column, Float)
#         min_val = db.query(func.min(numeric_col)).scalar()
#         max_val = db.query(func.max(numeric_col)).scalar()
#         return {"type": "range", "min": min_val, "max": max_val}
#
#     # ---- CASE 3: DATE/DATETIME → MIN & MAX ----
#     if payload.column_type in ["datetime", "date","time"]:
#         min_val = db.query(func.min(column)).scalar()
#         max_val = db.query(func.max(column)).scalar()
#         return {"type": "range", "min": min_val, "max": max_val}
#
#     raise HTTPException(400, "Unsupported column_type")
def get_column_stats(payload: ColumnStatsRequest, db: Session = Depends(get_db)):

    # 1. Hard-coded table (as you originally wanted)
    table = models.LoanRecord

    # 2. Apply pk_id filter if provided
    query_base = db.query(table)
    if payload.pk_id:
        try:
            dataset_uuid = UUID(payload.pk_id)
            print(f"***********Dataset ID converted to UUID: {dataset_uuid}")
        except ValueError:
            raise HTTPException(400, "Unsupported pk_id type")

        query_base = query_base.filter(table.dataset_id == dataset_uuid)
    else:
        raise HTTPException(400, "Missing parameter : pk_id")

    # 3. Resolve the column
    if payload.is_json_column:
        column = table.additional_fields[payload.column_name].astext
    else:
        try:
            column = getattr(table, payload.column_name)
        except AttributeError:
            raise HTTPException(400, f"Column {payload.column_name} not found")

    # -----------------------------------------
    # CASE 1: STRING FIELD → DISTINCT VALUES
    # -----------------------------------------
    if payload.column_type == "str":
        rows = (
            query_base
            .with_entities(column.label("value"))
            .distinct()
            .all()
        )
        return {
            "type": "distinct",
            "values": [r.value for r in rows]
        }

    # -----------------------------------------
    # CASE 2: NUMERIC FIELD → MIN & MAX
    # -----------------------------------------
    if payload.column_type in ("numeric", "int", "float"):
        numeric_col = cast(column, Float)
        min_val = query_base.with_entities(func.min(numeric_col)).scalar()
        max_val = query_base.with_entities(func.max(numeric_col)).scalar()

        return {
            "type": "range",
            "min": min_val,
            "max": max_val
        }

    # -----------------------------------------
    # CASE 3: DATE/DATETIME FIELD → MIN & MAX
    # -----------------------------------------
    if payload.column_type in ("date", "datetime"):
        min_val = query_base.with_entities(func.min(column)).scalar()
        max_val = query_base.with_entities(func.max(column)).scalar()

        return {
            "type": "range",
            "min": min_val,
            "max": max_val
        }

    raise HTTPException(400, "Unsupported column_type")