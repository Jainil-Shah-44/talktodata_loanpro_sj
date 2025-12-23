from typing import List

import sqlalchemy
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.schemas import ColumnInfo

PG_TYPE_MAP = {
    "string": "str",
    "number": "float",
    "boolean": "bool",
    "null": "None",
    "object": "dict",
    "array": "list"
}

table_columns_mem = {}
json_columns_mem = {}

def get_table_columns(db: Session, table_name: str, exclude: list[str], compulsoryCols: list[str]):
    #mod hvb @ 10/12/2025 for data_type of mapped dictionary with json
    # sql = """
    #     SELECT
    #         column_name,
    #         is_nullable,
    #         data_type
    #     FROM information_schema.columns
    #     WHERE table_name = :table_name
    #     AND column_name NOT IN :exclude
    #     ORDER BY ordinal_position;
    # """
    sql = """
            SELECT 
                column_name,
                is_nullable,
                CASE 
                    WHEN data_type IN ('character varying', 'varchar', 'text', 'char') THEN 'str'
                    WHEN data_type IN ('integer', 'bigint', 'smallint', 'numeric', 'real', 'double precision', 'decimal') THEN 'float'
                    WHEN data_type IN ('boolean') THEN 'bool'
                    WHEN data_type IN ('json', 'jsonb') THEN 'dict'
                    WHEN data_type IN ('ARRAY') THEN 'list'
                    
                    WHEN data_type = 'date' THEN 'date'
                    WHEN data_type IN ('timestamp', 'timestamp without time zone') THEN 'datetime'
                    WHEN data_type = 'timestamp with time zone' THEN 'datetime'
                    WHEN data_type = 'time' THEN 'time'
        
                    ELSE data_type
                END AS mapped_data_type
            FROM information_schema.columns
            WHERE table_name = :table_name
            AND column_name NOT IN :exclude
            ORDER BY ordinal_position;
        """

    #return in-mem columns info
    cached = table_columns_mem.get(table_name)
    if cached:
        return cached

    if not compulsoryCols:
        compulsoryCols = []

    # SQLAlchemy needs tuple for IN
    exclude_tuple = tuple(exclude) if exclude else tuple([""])

    rows = db.execute(
        sqlalchemy.text(sql),
        {"table_name": table_name, "exclude": exclude_tuple}
    ).fetchall()

    result = []
    for r in rows:
        result.append(
        # {
        #     "column_name": r.column_name,
        #     # "is_compulsory": (r.is_nullable == "NO"),
        #     "is_compulsory": (r.column_name in compulsoryCols),
        #     "data_type": r.data_type
        # }
        ColumnInfo(
            column_name=r.column_name,
            is_compulsory=(r.column_name in compulsoryCols),
            # mod hvb @ 10/12/2025 for data_type of mapped dictionary with json
            #data_type=r.data_type,
            data_type=r.mapped_data_type,
            is_json_col=False
        ))

    table_columns_mem[table_name] = result

    return result

def extract_jsonb_columns(
    db,
    table_name: str,
    key_value,
    id_col: str = "pk_id",
    json_col: str = "additional_fields"
) -> List[ColumnInfo]:
    """
    Reads the first row where json_col is not null and id_col = key_value,
    extracts keys + inferred datatypes, and returns a list[ColumnInfo].
    """

    #prepare in mem-key
    tbl_key = table_name + "-" + key_value + "-" + json_col

    # return in-mem columns info
    cached = json_columns_mem.get(tbl_key)
    if cached:
        return cached

    sql = f"""
    SELECT 
        key,
        jsonb_typeof(value) AS data_type
    FROM (
        SELECT 
            jsonb_object_keys({json_col}) AS key,
            {json_col} -> jsonb_object_keys({json_col}) AS value
        FROM (
            SELECT {json_col}
            FROM {table_name}
            WHERE {json_col} IS NOT NULL
              AND {id_col} = :key_value
            LIMIT 1
        ) t1
    ) t2;
    """

    rows = db.execute(
        text(sql),
        {"key_value": key_value}
    ).fetchall()

    result = []

    for r in rows:
        result.append(ColumnInfo(
            column_name=r.key,
            is_compulsory=False,
            data_type=PG_TYPE_MAP.get(r.data_type, "str"),
            is_json_col=True
        ))

    table_columns_mem[tbl_key] = result

    return  result

def is_json_col(key: str, table_name:str,json_src_col:str, column_name: str) -> bool:
    # prepare in mem-key
    tbl_key = table_name + "-" + key + "-" + json_src_col

    # return in-mem columns info
    cached = json_columns_mem.get(tbl_key)
    if cached:
        # lookup in cached for column_name
        for r in cached:
            if r.column_name == column_name:
                return True

    return False

def merge_columns(existing: list[ColumnInfo], dynamic: list[ColumnInfo]):
    existing_names = {c.column_name for c in existing}

    for d in dynamic:
        if d.column_name not in existing_names:
            existing.append(d)

    # added hvb @ 12/12/2025
    # ➜ Sort by column_name
    existing.sort(key=lambda x: x.column_name)

    return existing
