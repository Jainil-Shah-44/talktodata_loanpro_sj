from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Date, JSON, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    datasets = relationship("Dataset", back_populates="user")

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    total_records = Column(Integer)
    upload_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_validated = Column(DateTime(timezone=True))
    status = Column(String(50), default="uploaded")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    #Added hvb @ 02/12/2025 for filetype of dataset
    file_type = Column(String(150), nullable=True)

    user = relationship("User", back_populates="datasets")
    loan_records = relationship("LoanRecord", back_populates="dataset")

class LoanRecord(Base):
    __tablename__ = "loan_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    
    # Core fields - always present
    agreement_no = Column(String(255), nullable=False)
    loan_id = Column(String(255))
    account_number = Column(String(255))
    
    # Common date fields
    first_disb_date = Column(Date)
    last_disb_date = Column(Date)
    sanction_date = Column(Date)
    date_of_npa = Column(Date)
    date_of_woff = Column(Date)
    
    # Validation fields
    npa_write_off = Column(String(50))
    date_woff_gt_npa_date = Column(Boolean)
    
    # DPD fields
    dpd_as_on_31st_jan_2025 = Column(Integer)
    dpd_as_per_string = Column(Integer)
    difference = Column(Integer)
    dpd_by_skc = Column(Integer)
    diff = Column(Integer)
    dpd = Column(Integer)
    
    # Amount fields
    principal_os_amt = Column(Numeric)
    interest_overdue_amt = Column(Numeric)
    penal_interest_overdue = Column(Numeric)
    chq_bounce_other_charges_amt = Column(Numeric)
    total_balance_amt = Column(Numeric)
    provision_done_till_date = Column(Numeric)
    carrying_value_as_on_date = Column(Numeric)
    sanction_amt = Column(Numeric)
    total_amt_disb = Column(Numeric)
    pos_amount = Column(Numeric)
    disbursement_amount = Column(Numeric)
    
    # Validation flags
    pos_gt_dis = Column(Boolean)
    
    # Classification and status fields
    classification = Column(String(100))
    june_24_pool = Column(String(100))
    product_type = Column(String(100))
    status = Column(String(100))
    
    # Customer information
    customer_name = Column(String(255))
    state = Column(String(100))
    bureau_score = Column(Integer)
    
    # Collection fields
    m1_collection = Column(Numeric)
    m2_collection = Column(Numeric)
    m3_collection = Column(Numeric)
    m4_collection = Column(Numeric)
    m5_collection = Column(Numeric)
    m6_collection = Column(Numeric)
    m7_collection = Column(Numeric)
    m8_collection = Column(Numeric)
    m9_collection = Column(Numeric)
    m10_collection = Column(Numeric)
    m11_collection = Column(Numeric)
    m12_collection = Column(Numeric)
    collection_12m = Column(Numeric)  # Added for convenience
    total_collection = Column(Numeric)
    post_npa_collection = Column(Numeric)
    post_woff_collection = Column(Numeric)
    
    # Auto-generated bucket fields
    auto_dpd_bucket = Column(String(100))
    auto_pos_bucket = Column(String(100))
    auto_model_year_skc_bucket = Column(String(100))
    auto_roi_at_booking_bucket = Column(String(100))
    auto_bureau_score_bucket = Column(String(100))
    auto_current_ltv_bucket = Column(String(100))
    
    # Legal fields
    sec_17_order_date_1 = Column(Integer)
    sec_9_order_date_1 = Column(Integer)
    arbitration_status = Column(String(255))
    action_taken_under_s138_ni_act = Column(String(255))
    
    # Validation status
    has_validation_errors = Column(Boolean, default=False)
    validation_error_types = Column(JSONB)

     #EMI amount calculation
    original_tenor_months = Column(Integer)
    current_tenor_months = Column(Integer)
    balance_tenor_months = Column(Integer)

    emi_amount = Column(Numeric)
    emi_paid_months = Column(Integer)

    total_collection_since_inception = Column(Numeric)
    roi_at_booking = Column(Numeric)
    
    # Store any additional fields not mapped to columns
    additional_fields = Column(JSONB)

    

    # Added hvb @ 27/11/2025 new fields added for summary
    city = Column(String(150))
    current_bureau_score = Column(Integer)
    claim_info = Column(String(150))
    category = Column(String(150))
    sarfesi_applicable = Column(String(50))
    legal_action1 = Column(String(150))
    legal_action2 = Column(String(150))
    asset_type_detail = Column(String(200))
    recovery_timeline_range_by_skc = Column(String(100))
    auctions_cnt = Column(Integer)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="loan_records")
    pool_selection_records = relationship("PoolSelectionRecord", back_populates="loan_record")
    
    # This method allows accessing any field from additional_fields as if it were a column
    def __getattr__(self, name):
        if 'additional_fields' in self.__dict__ and self.additional_fields and name in self.additional_fields:
            return self.additional_fields[name]
        raise AttributeError(f"'LoanRecord' object has no attribute '{name}'")

# Added hvb @ 26/10/2025 for saving filters
class Filter(Base):
    __tablename__ = "filters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    filter_name = Column(String(100), nullable=False)
    join_type = Column(String(3), default="AND")
    last_used = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by = Column(UUID)
    updated_by = Column(UUID)

    conditions = relationship("FilterCondition", back_populates="filter", cascade="all, delete")

class FilterCondition(Base):
    __tablename__ = "filter_conditions"

    id = Column(Integer, primary_key=True, index=True)
    filter_id = Column(Integer, ForeignKey("filters.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    operator = Column(String(20), nullable=False)
    value = Column(Text, nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    enabled = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    filter = relationship("Filter", back_populates="conditions")

# Note: PoolSelection and PoolSelectionRecord models are defined in app/models/pool_selection.py