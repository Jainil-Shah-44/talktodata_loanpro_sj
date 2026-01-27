# app/schemas/bucket_summary.py
from datetime import datetime

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.models.FilterCriteriaItem import FilterCriteriaItem


class BucketRow(BaseModel):
    label: str

    count: int
    #sum_amount: Optional[float] = None
    principal_os_amt: float
    post_npa_collection: float
    post_woff_collection: float
    m6_collection: float
    m12_collection:float
    total_collection:float

class BucketConfigItem(BaseModel):
    id: UUID
    name: str
    summary_type: str
    bucket_config: Any
    is_default: bool
    target_field: Optional[str]
    target_field_is_json: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class BucketSummaryResponse(BaseModel):
    id: UUID
    name: str
    summary_type: str
    #buckets: List[BucketRow]
    buckets: List[Dict[str, Any]]

class BucketSummaryRequest(BaseModel):
    config_ids: Optional[List[UUID]] = None
    config_types: Optional[List[str]] = None
    # mod hvb @ 08/12/2025 merging filter-criteria
    # filters: Dict[str, Any] = {}
    filters: Optional[List[FilterCriteriaItem]] = None
    show_empty_buckets: bool = True

# added hvb @ 02-12-2025
class BucketConfigCreate(BaseModel):
    dataset_id: str
    name: str
    summary_type: str # we will save file_type in this field
    target_field: str
    bucket_config: List[Dict[str, Any]]
    is_default: bool = False
    target_field_is_json: bool = False # added hvb @ 05/12/2025

# added hvb @ 02-12-2025
class BucketConfigUpdate(BaseModel):
    name: Optional[str] = None
    target_field: Optional[str] = None
    summary_type: Optional[str] = None # we will save file_type in this field
    bucket_config: Optional[List[Dict[str, Any]]] = None
    is_default: Optional[bool] = None
    dataset_id: Optional[str] = None
    target_field_is_json: Optional[bool] = None
