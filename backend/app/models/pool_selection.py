from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Date, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.core.database import Base

class PoolSelection(Base):
    __tablename__ = "pool_selections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    total_amount = Column(Numeric, nullable=False)
    account_count = Column(Integer, nullable=False)
    criteria = Column(JSONB)  # Store the filter criteria used
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    dataset = relationship("Dataset")
    records = relationship("PoolSelectionRecord", back_populates="pool_selection")


class PoolSelectionRecord(Base):
    __tablename__ = "pool_selection_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pool_selection_id = Column(Integer, ForeignKey("pool_selections.id", ondelete="CASCADE"), nullable=False)
    loan_record_id = Column(UUID(as_uuid=True), ForeignKey("loan_records.id", ondelete="CASCADE"), nullable=False)
    principal_os_amt = Column(Numeric, nullable=False)  # Store amount at time of selection
    
    # Relationships
    pool_selection = relationship("PoolSelection", back_populates="records")
    loan_record = relationship("LoanRecord", back_populates="pool_selection_records")
