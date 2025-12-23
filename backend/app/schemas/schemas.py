from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class TokenData(BaseModel):
    user_id: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None

class DatasetCreate(DatasetBase):
    pass

class Dataset(DatasetBase):
    id: UUID
    user_id: UUID
    file_name: str
    file_size: Optional[int]
    file_type: Optional[str] = None # Added hvb @ 03/12/2025 for viewing file type
    total_records: Optional[int]
    upload_date: datetime
    status: str

    class Config:
        from_attributes = True

class LoanRecordBase(BaseModel):
    agreement_no: Optional[str] = None
    principal_os_amt: Optional[float] = None
    dpd_as_on_31st_jan_2025: Optional[int] = None
    classification: Optional[str] = None
    product_type: Optional[str] = None
    customer_name: Optional[str] = None
    state: Optional[str] = None
    bureau_score: Optional[int] = None
    total_collection: Optional[float] = None
    additional_fields: Optional[Dict[str, Any]] = None
    loan_id: Optional[str] = None
    disbursement_date: Optional[str] = None
    pos_amount: Optional[float] = None
    disbursement_amount: Optional[float] = None
    dpd: Optional[int] = None
    status: Optional[str] = None

    class Config:
        extra = "allow"

class LoanRecord(LoanRecordBase):
    id: UUID
    dataset_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
        extra = "allow"


class SummaryColumn(BaseModel):
    key: str
    title: str


class SummaryRow(BaseModel):
    bucket: str
    lowerBound: Optional[Union[int, float]] = None
    upperBound: Optional[Union[int, float]] = None
    noOfAccs: int
    pos: float
    percentOfPos: float
    # Write-Off Pool fields
    three_m_col: float = Field(0.0, alias="3mCol")
    six_m_col: float = Field(0.0, alias="6mCol")
    twelve_m_col: float = Field(0.0, alias="12mCol")
    total_collection: float = Field(0.0, alias="totalCollection")
    # DPD Summary fields
    disbursementAmt: float = 0.0
    posSundown: float = 0.0


class SummaryTable(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    columns: List[SummaryColumn]
    rows: List[SummaryRow]


class SummaryData(BaseModel):
    writeOffPool: SummaryTable
    dpdSummary: SummaryTable
    # Additional summary tables can be added here

#Added hvb @ 15/11/2025 for upload_profile
class ExtraColumnSchema(BaseModel):
    source_col: str
    target_name: str

class CleanupRuleSchema(BaseModel):
    col: int
    type: str  # 'dt', 'int', 'float', 'str', etc.

class SheetConfigSchema(BaseModel):
    sheet_index: int
    sheet_alias: Optional[str] = None
    header_row: int = -1
    skip_rows: int = 0
    cols_to_read: Optional[str] = None  # "0,2,6"
    key_columns: Optional[List[int]] = None
    extra: Optional[List[ExtraColumnSchema]] = None
    cleanup: Optional[List[CleanupRuleSchema]] = None

class ColumnMappingSchema(BaseModel):
    sheet_index: int
    source_col: str
    target_column: str

class RelationSchema(BaseModel):
    left_sheet: int
    right_sheet: int
    left_col: str
    right_col: str
    how: str = "left"

class MappingProfileCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    is_global: bool = True
    sheets: List[SheetConfigSchema]
    column_mappings: Optional[List[ColumnMappingSchema]] = []
    relations: Optional[List[RelationSchema]] = []

class MappingProfileUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_global: Optional[bool] = None
    file_type: Optional[str] = None #Added hvb @ 03/12/205
    sheets: Optional[List[SheetConfigSchema]] = None
    column_mappings: Optional[List[ColumnMappingSchema]] = None
    relations: Optional[List[RelationSchema]] = None

class MappingProfileOutSchema(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_global: bool
    is_active: bool
    file_type: Optional[str] = None  # Added hvb @ 03/12/205
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class ColumnInfo(BaseModel):
    column_name: str
    is_compulsory: bool
    data_type: str
    is_json_col: bool # added hvb @ 05/12/2025

class UpdateFileType(BaseModel):
    file_type: str