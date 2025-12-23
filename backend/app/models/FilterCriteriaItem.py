# # New FilterCriteria type
# # Added hvb @ 26/10/2025 for resolving bug of applying multiple filters over same field
# from pydantic import BaseModel
# from typing import Optional,Union
#
# FilterValue = Union[str, float, int, None]
#
# class FilterCriteriaItem(BaseModel):
#     field: str
#     operator: str
#     value: Optional[Union[str, float, int]] = None
#     min_value: Optional[float] = None
#     max_value: Optional[float] = None
#     enabled: bool = True
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Union, List


class FilterCriteriaItem(BaseModel):
    field: str
    operator: str
    value: Optional[Union[str, float, int]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    enabled: bool = True

class FilterCreate(BaseModel):
    filter_name: str
    join_type: str  # "AND" or "OR"
    conditions: List[FilterCriteriaItem]

class FilterResponse(BaseModel):
    id: int
    filter_name: str
    join_type: str
    last_used: bool
    created_at: datetime
    updated_at: datetime