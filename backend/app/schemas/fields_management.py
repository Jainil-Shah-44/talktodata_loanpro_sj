from pydantic import BaseModel

class ColumnStatsRequest(BaseModel):
    column_name: str
    column_type: str  # "str", "datetime", "numeric"
    is_json_column: bool = False
    pk_id: str = "pk_id"
